from typing import Dict, Any, Optional
from python_client.config import init_supabase

class EdgeInvoker:
    """
    Client helper to invoke Supabase Edge Functions:
    1. file-validator-processor: Validates file payload (size, extension, mime)
    2. doc-summarizer: Auto-summarizes text/doc files
    3. audit-logger: Logs access & audit events
    """

    def __init__(self):
        self.supabase = init_supabase()

    def invoke_function(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic invocation of a deployed Supabase Edge Function.
        """
        try:
            res = self.supabase.functions.invoke(
                function_name,
                invoke_options={"body": payload}
            )
            # Handle Response object or dict
            if hasattr(res, "json"):
                return res.json()
            elif isinstance(res, dict):
                return res
            elif hasattr(res, "data"):
                return res.data
            return {"raw_response": str(res)}
        except Exception as e:
            print(f"Edge Function '{function_name}' invocation note/error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "function_name": function_name,
                "note": "Edge function may not be deployed locally/cloud yet. CLI instructions in README."
            }

    def validate_file(self, filename: str, file_size: int, mime_type: str = "", file_base64: str = "") -> Dict[str, Any]:
        """Invoke file-validator-processor function."""
        payload = {
            "filename": filename,
            "file_size": file_size,
            "mime_type": mime_type,
            "file_base64": file_base64
        }
        return self.invoke_function("file-validator-processor", payload)

    def summarize_document(self, filename: str, text_content: str = "", file_base64: str = "") -> Dict[str, Any]:
        """Invoke doc-summarizer function."""
        payload = {
            "filename": filename,
            "text_content": text_content,
            "file_base64": file_base64
        }
        return self.invoke_function("doc-summarizer", payload)

    def log_audit(self, action: str, resource_type: str, resource_id: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Invoke audit-logger function."""
        payload = {
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {}
        }
        return self.invoke_function("audit-logger", payload)
