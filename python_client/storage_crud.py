import os
import base64
from typing import Dict, Any, List, Optional
from python_client.config import init_supabase, STORAGE_BUCKET
from python_client.db_crud import DatabaseCRUD

class StorageCRUD:
    """
    Handles complete Supabase Storage CRUD operations:
    Create  -> Validate via Edge Function + Upload to Bucket + Insert DB Metadata
    Read    -> List Files + Download Bytes / Signed URLs + Audit Log
    Update  -> Replace File Content or Update Metadata
    Delete  -> Remove from Bucket + Purge DB Metadata
    """

    def __init__(self, bucket_name: str = STORAGE_BUCKET):
        self.supabase = init_supabase()
        self.db = DatabaseCRUD()
        self.bucket = bucket_name
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Helper to ensure storage bucket is initialized."""
        try:
            buckets = self.supabase.storage.list_buckets()
            existing = [b.name for b in buckets] if buckets else []
            if self.bucket not in existing:
                self.supabase.storage.create_bucket(self.bucket, options={"public": True})
        except Exception as e:
            # Bucket might already exist or public creation handled via RLS
            pass

    # =========================================================
    # CREATE FILE (Upload + Validate + Store Metadata)
    # =========================================================
    def upload_file(
        self,
        file_path_or_bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        destination_path: Optional[str] = None,
        validate_edge_fn: bool = True
    ) -> Dict[str, Any]:
        """
        Upload file to Supabase Storage bucket and create metadata entry.
        """
        # Read file bytes & prepare base64 string
        if isinstance(file_path_or_bytes, str):
            with open(file_path_or_bytes, "rb") as f:
                file_bytes = f.read()
            if not filename:
                filename = os.path.basename(file_path_or_bytes)
        else:
            file_bytes = file_path_or_bytes

        storage_key = destination_path or filename
        file_size = len(file_bytes)
        base64_content = base64.b64encode(file_bytes).decode("utf-8")

        validation_result = {}
        file_hash = ""
        status = "validated"

        # 1. Call Edge Function: file-validator-processor
        if validate_edge_fn:
            try:
                from python_client.edge_invoker import EdgeInvoker
                invoker = EdgeInvoker()
                val_res = invoker.validate_file(
                    filename=filename,
                    file_size=file_size,
                    mime_type=content_type,
                    file_base64=base64_content
                )
                validation_result = val_res
                file_hash = val_res.get("file_hash", "")
                if not val_res.get("valid", True):
                    raise ValueError(f"File Validation Failed: {', '.join(val_res.get('errors', []))}")
            except Exception as e:
                if "File Validation Failed" in str(e):
                    raise e
                status = "unverified"

        # 2. Upload Object to Supabase Storage Bucket
        upload_res = self.supabase.storage.from_(self.bucket).upload(
            path=storage_key,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )

        # 3. Process Text Summary if Document File (Edge Function 2)
        summary = ""
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext in ["txt", "md", "csv", "json"]:
            try:
                from python_client.edge_invoker import EdgeInvoker
                invoker = EdgeInvoker()
                sum_res = invoker.summarize_document(filename=filename, file_base64=base64_content)
                summary = sum_res.get("summary", "")
            except Exception:
                pass

        # 4. Insert Record into Postgres files_metadata table
        meta_record = self.db.insert_file_metadata(
            filename=filename,
            file_path=storage_key,
            file_size=file_size,
            mime_type=content_type,
            file_hash=file_hash,
            summary=summary,
            status=status,
            tags=[ext] if ext else [],
            metadata_json=validation_result
        )

        # 5. Record Audit Log
        self.db.create_audit_log(
            action="UPLOAD",
            resource_type="storage",
            resource_id=storage_key,
            details={"file_size": file_size, "mime_type": content_type}
        )

        return {
            "status": "success",
            "storage_key": storage_key,
            "metadata": meta_record,
            "validation": validation_result
        }

    # =========================================================
    # READ FILE (List, Download Bytes, Signed URL)
    # =========================================================
    def list_files(self) -> List[Dict[str, Any]]:
        """List files from metadata table enriched with public URLs."""
        records = self.db.list_files_metadata()
        for rec in records:
            path = rec["file_path"]
            rec["public_url"] = self.get_public_url(path)
        return records

    def download_file_bytes(self, storage_key: str) -> bytes:
        """Download raw binary content of a file from storage."""
        data = self.supabase.storage.from_(self.bucket).download(storage_key)
        
        # Log download audit event
        self.db.create_audit_log(
            action="DOWNLOAD",
            resource_type="storage",
            resource_id=storage_key,
            details={"download_type": "binary"}
        )
        return data

    def get_public_url(self, storage_key: str) -> str:
        """Get public URL for a file in storage."""
        return self.supabase.storage.from_(self.bucket).get_public_url(storage_key)

    def create_signed_url(self, storage_key: str, expires_in_seconds: int = 3600) -> str:
        """
        Generate a secure time-limited Signed URL and trigger Edge Function audit log.
        """
        res = self.supabase.storage.from_(self.bucket).create_signed_url(storage_key, expires_in_seconds)
        signed_url = res.get("signedUrl", "") if isinstance(res, dict) else str(res)

        # Trigger Audit Logger Edge Function (Edge Function 3)
        try:
            from python_client.edge_invoker import EdgeInvoker
            invoker = EdgeInvoker()
            invoker.log_audit(
                action="DOWNLOAD_SIGNED_URL",
                resource_type="storage",
                resource_id=storage_key,
                details={"expires_in": expires_in_seconds, "url_generated": True}
            )
        except Exception:
            pass

        return signed_url

    # =========================================================
    # UPDATE FILE (Replace Content / Metadata)
    # =========================================================
    def update_file(
        self,
        storage_key: str,
        new_file_bytes: Optional[bytes] = None,
        new_content_type: Optional[str] = None,
        metadata_updates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Replace file content in Storage bucket and/or update Postgres metadata.
        """
        if new_file_bytes:
            content_type = new_content_type or "application/octet-stream"
            # Update storage object (upsert)
            self.supabase.storage.from_(self.bucket).upload(
                path=storage_key,
                file=new_file_bytes,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            
            db_updates = metadata_updates or {}
            db_updates["file_size"] = len(new_file_bytes)
            db_updates["mime_type"] = content_type
            updated_meta = self.db.update_file_metadata(storage_key, db_updates)
        elif metadata_updates:
            updated_meta = self.db.update_file_metadata(storage_key, metadata_updates)
        else:
            updated_meta = self.db.get_file_metadata_by_path(storage_key) or {}

        # Record Audit Log
        self.db.create_audit_log(
            action="UPDATE",
            resource_type="storage",
            resource_id=storage_key,
            details={"updated_fields": list((metadata_updates or {}).keys())}
        )

        return updated_meta

    # =========================================================
    # DELETE FILE (Remove from Bucket + Database)
    # =========================================================
    def delete_file(self, storage_key: str) -> bool:
        """
        Delete file object from Storage bucket and remove metadata from Postgres.
        """
        try:
            self.supabase.storage.from_(self.bucket).remove([storage_key])
        except Exception as e:
            print(f"Warning: Storage bucket delete error: {e}")

        # Delete Database metadata entry
        deleted_db = self.db.delete_file_metadata(storage_key)

        # Record Audit Log
        self.db.create_audit_log(
            action="DELETE",
            resource_type="storage",
            resource_id=storage_key,
            details={"success": deleted_db}
        )

        return deleted_db
