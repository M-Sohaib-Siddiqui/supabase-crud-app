from typing import List, Dict, Any, Optional
from python_client.config import init_supabase

class DatabaseCRUD:
    """
    Handles CRUD operations for Supabase Postgres tables:
    1. database_items (Generic Table CRUD)
    2. files_metadata (File Metadata CRUD)
    3. audit_logs (System Audit Activity)
    """

    def __init__(self):
        self.supabase = init_supabase()

    # =========================================================
    # 1. DATABASE_ITEMS CRUD Operations
    # =========================================================
    def create_item(self, title: str, description: str = "", category: str = "General", status: str = "Active", tags: List[str] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new item in database_items table."""
        payload = {
            "title": title,
            "description": description,
            "category": category,
            "status": status,
            "tags": tags or [],
            "metadata": metadata or {}
        }
        res = self.supabase.table("database_items").insert(payload).execute()
        return res.data[0] if res.data else {}

    def get_items(self, category_filter: Optional[str] = None, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve items with optional filtering and search."""
        query = self.supabase.table("database_items").select("*").order("created_at", desc=True)
        if category_filter:
            query = query.eq("category", category_filter)
        if search_query:
            query = query.ilike("title", f"%{search_query}%")
        res = query.execute()
        return res.data or []

    def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single item by UUID."""
        res = self.supabase.table("database_items").select("*").eq("id", item_id).execute()
        return res.data[0] if res.data else None

    def update_item(self, item_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item by ID."""
        res = self.supabase.table("database_items").update(updates).eq("id", item_id).execute()
        return res.data[0] if res.data else {}

    def delete_item(self, item_id: str) -> bool:
        """Delete an item by ID."""
        res = self.supabase.table("database_items").delete().eq("id", item_id).execute()
        return len(res.data) > 0

    # =========================================================
    # 2. FILES_METADATA CRUD Operations
    # =========================================================
    def insert_file_metadata(self, filename: str, file_path: str, file_size: int, mime_type: str, file_hash: str = "", summary: str = "", status: str = "validated", tags: List[str] = None, metadata_json: Dict[str, Any] = None) -> Dict[str, Any]:
        """Insert metadata record for an uploaded storage file."""
        payload = {
            "filename": filename,
            "file_path": file_path,
            "file_size": file_size,
            "mime_type": mime_type,
            "file_hash": file_hash,
            "summary": summary,
            "status": status,
            "tags": tags or [],
            "metadata_json": metadata_json or {}
        }
        res = self.supabase.table("files_metadata").insert(payload).execute()
        return res.data[0] if res.data else {}

    def list_files_metadata(self) -> List[Dict[str, Any]]:
        """Retrieve all file metadata records."""
        res = self.supabase.table("files_metadata").select("*").order("created_at", desc=True).execute()
        return res.data or []

    def get_file_metadata_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Fetch metadata by storage file_path."""
        res = self.supabase.table("files_metadata").select("*").eq("file_path", file_path).execute()
        return res.data[0] if res.data else None

    def update_file_metadata(self, file_path: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update file metadata by storage file_path."""
        res = self.supabase.table("files_metadata").update(updates).eq("file_path", file_path).execute()
        return res.data[0] if res.data else {}

    def delete_file_metadata(self, file_path: str) -> bool:
        """Delete file metadata entry."""
        res = self.supabase.table("files_metadata").delete().eq("file_path", file_path).execute()
        return len(res.data) > 0

    # =========================================================
    # 3. AUDIT_LOGS Operations
    # =========================================================
    def create_audit_log(self, action: str, resource_type: str, resource_id: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Record an audit log entry."""
        payload = {
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {}
        }
        res = self.supabase.table("audit_logs").insert(payload).execute()
        return res.data[0] if res.data else {}

    def list_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent audit log records."""
        res = self.supabase.table("audit_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return res.data or []
