import os
import sys
import json
import pandas as pd
from PIL import Image
import io
import streamlit as st

# Ensure project root is in sys.path for local and Streamlit Cloud execution
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from python_client.db_crud import DatabaseCRUD
from python_client.storage_crud import StorageCRUD
from python_client.edge_invoker import EdgeInvoker

# Page Configuration
st.set_page_config(
    page_title="Supabase CRUD & Storage Manager",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Modern Custom CSS Styling
st.markdown("""
<style>
    /* Global Styles */
    .main {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    h1, h2, h3 {
        color: #10b981 !important;
        font-weight: 700;
    }
    /* Stat Cards */
    .stat-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .stat-val {
        font-size: 26px;
        font-weight: bold;
        color: #10b981;
    }
    .stat-lbl {
        font-size: 13px;
        color: #8b949e;
        margin-top: 4px;
    }
    /* Custom Badges */
    .badge-success {
        background-color: #064e3b;
        color: #34d399;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-warning {
        background-color: #78350f;
        color: #fbbf24;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_clients():
    db = DatabaseCRUD()
    storage = StorageCRUD()
    edge = EdgeInvoker()
    return db, storage, edge

try:
    db, storage, edge = get_clients()
except Exception as e:
    st.error(f"⚡ **Supabase Connection Error**: {e}")
    st.info("💡 Please set your `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env` (for local dev) or Streamlit Secrets (for Streamlit Cloud deployment).")
    st.stop()

# =========================================================
# SIDEBAR NAVIGATION & LOGO
# =========================================================
logo_path = os.path.join(os.path.dirname(__file__), "logo.jpg")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)
else:
    st.sidebar.markdown("## ⚡ **SUPABASE CRUD**")

st.sidebar.markdown("### **CRUD Application Dashboard**")
st.sidebar.markdown("---")

view_option = st.sidebar.radio(
    "Navigation Menu",
    ["📁 Storage Manager", "📊 Database Tables", "⚡ Edge Functions", "📜 Audit Logs"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.caption("🚀 Built with Python, Supabase, Deno & Streamlit")

# =========================================================
# VIEW 1: STORAGE MANAGER (Files & Metadata CRUD)
# =========================================================
if view_option == "📁 Storage Manager":
    st.title("📁 Supabase Storage & File Metadata Manager")
    st.write("Upload, download, manage, and process files with server-side Deno Edge Function validation.")

    # Key Metrics Header
    files_list = storage.list_files()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stat-card"><div class="stat-val">{len(files_list)}</div><div class="stat-lbl">Total Files Stored</div></div>', unsafe_allow_html=True)
    with col2:
        total_size_mb = sum([f.get("file_size", 0) for f in files_list]) / (1024 * 1024)
        st.markdown(f'<div class="stat-card"><div class="stat-val">{total_size_mb:.2f} MB</div><div class="stat-lbl">Total Storage Used</div></div>', unsafe_allow_html=True)
    with col3:
        validated_cnt = len([f for f in files_list if f.get("status") == "validated"])
        st.markdown(f'<div class="stat-card"><div class="stat-val">{validated_cnt}</div><div class="stat-lbl">Validated Files</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="stat-card"><div class="stat-val">3</div><div class="stat-lbl">Active Edge Functions</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 1. CREATE FILE (Upload Section)
    st.subheader("📤 Upload New File")
    uploaded_file = st.file_uploader(
        "Drag and drop or browse file to upload (Allowed: PNG, JPG, PDF, TXT, CSV, JSON | Max 10MB)",
        type=["png", "jpg", "jpeg", "gif", "pdf", "txt", "csv", "json", "md"]
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        dest_filename = st.text_input("Destination Filename in Storage", value=uploaded_file.name)
        mime_type = uploaded_file.type or "application/octet-stream"

        if st.button("🚀 Upload & Process File", type="primary"):
            with st.spinner("Invoking 'file-validator-processor' Edge Function & uploading to bucket..."):
                try:
                    res = storage.upload_file(
                        file_path_or_bytes=file_bytes,
                        filename=dest_filename,
                        content_type=mime_type,
                        validate_edge_fn=True
                    )
                    st.success(f"✅ File '{dest_filename}' uploaded successfully!")
                    st.json(res)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Upload Failed: {e}")

    st.markdown("---")

    # 2. READ & EXPLORE FILES
    st.subheader("📋 Uploaded Storage Files")
    if not files_list:
        st.info("No files stored yet. Use the uploader above to add your first file.")
    else:
        df = pd.DataFrame(files_list)
        # Reorder and select key display columns
        display_cols = ["filename", "file_path", "file_size", "mime_type", "status", "created_at"]
        available_cols = [c for c in display_cols if c in df.columns]
        
        st.dataframe(df[available_cols], use_container_width=True)

        st.subheader("🔍 File Actions & Previews")
        selected_file_path = st.selectbox(
            "Select a file to inspect, download, update, or delete:",
            options=[f["file_path"] for f in files_list]
        )

        if selected_file_path:
            file_record = next((f for f in files_list if f["file_path"] == selected_file_path), None)
            if file_record:
                pcol1, pcol2 = st.columns([1, 1])

                with pcol1:
                    st.markdown("##### ⚙️ Operations")
                    
                    # Action A: Secure Download via Signed URL
                    if st.button("🔑 Generate Signed Download Link (1 Hr Expiry)"):
                        signed_url = storage.create_signed_url(selected_file_path, expires_in_seconds=3600)
                        st.success("Signed URL Generated! (Recorded in Audit Logs)")
                        st.code(signed_url, language="text")
                        st.markdown(f"[📥 Download Direct Link]({signed_url})")

                    # Action B: Direct Binary Download
                    try:
                        file_data = storage.download_file_bytes(selected_file_path)
                        st.download_button(
                            label="⬇️ Download Raw File",
                            data=file_data,
                            file_name=file_record.get("filename", "downloaded_file"),
                            mime=file_record.get("mime_type", "application/octet-stream")
                        )
                    except Exception as e:
                        st.warning(f"Raw download note: {e}")

                    # Action C: Update Metadata
                    st.markdown("##### ✏️ Update Metadata")
                    with st.form(key=f"update_form_{selected_file_path}"):
                        new_summary = st.text_area("Summary", value=file_record.get("summary") or "")
                        tags_str = st.text_input("Tags (comma separated)", value=", ".join(file_record.get("tags") or []))
                        submit_update = st.form_submit_button("Update File Metadata")

                        if submit_update:
                            tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]
                            storage.update_file(selected_file_path, metadata_updates={"summary": new_summary, "tags": tags_list})
                            st.success("Metadata updated successfully!")
                            st.rerun()

                    # Action D: Delete File
                    st.markdown("##### 🗑️ Delete File")
                    if st.button(f"DELETE '{selected_file_path}'", type="primary"):
                        if storage.delete_file(selected_file_path):
                            st.success(f"File '{selected_file_path}' deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete file.")

                with pcol2:
                    st.markdown("##### 🖼️ File Content Preview & Details")
                    st.json(file_record)

                    # Preview Images
                    mime = file_record.get("mime_type", "")
                    if "image" in mime:
                        try:
                            raw_img = storage.download_file_bytes(selected_file_path)
                            image = Image.open(io.BytesIO(raw_img))
                            st.image(image, caption=file_record.get("filename"), use_container_width=True)
                        except Exception:
                            st.info("Image preview unavailable.")

# =========================================================
# VIEW 2: DATABASE TABLES (Pure Table CRUD)
# =========================================================
elif view_option == "📊 Database Tables":
    st.title("📊 Supabase Postgres Database CRUD")
    st.write("Perform complete Create, Read, Update, and Delete operations on Supabase database tables.")

    tab1, tab2 = st.tabs(["📋 Table Items ('database_items')", "➕ Create New Item"])

    with tab1:
        search_q = st.text_input("🔍 Search items by title...", value="")
        items = db.get_items(search_query=search_q if search_q else None)

        if not items:
            st.info("No records found in 'database_items' table.")
        else:
            items_df = pd.DataFrame(items)
            st.dataframe(items_df, use_container_width=True)

            st.markdown("### ✏️ Edit or Delete Record")
            item_ids = [item["id"] for item in items]
            selected_item_id = st.selectbox("Select Record ID to Modify:", options=item_ids)

            if selected_item_id:
                sel_item = next((i for i in items if i["id"] == selected_item_id), None)
                if sel_item:
                    with st.form("edit_item_form"):
                        e_title = st.text_input("Title", value=sel_item.get("title", ""))
                        e_desc = st.text_area("Description", value=sel_item.get("description", ""))
                        e_cat = st.selectbox("Category", ["General", "Reports", "UserData", "Settings"], index=0)
                        e_status = st.selectbox("Status", ["Active", "Pending", "Archived"], index=0)
                        
                        col_u1, col_u2 = st.columns(2)
                        with col_u1:
                            btn_save = st.form_submit_button("Save Changes", type="primary")
                        with col_u2:
                            btn_del = st.form_submit_button("Delete Record")

                        if btn_save:
                            db.update_item(selected_item_id, {"title": e_title, "description": e_desc, "category": e_cat, "status": e_status})
                            st.success("Item updated!")
                            st.rerun()

                        if btn_del:
                            db.delete_item(selected_item_id)
                            st.success("Item deleted!")
                            st.rerun()

    with tab2:
        st.markdown("### Add New Item to Postgres Table")
        with st.form("create_item_form"):
            c_title = st.text_input("Title *")
            c_desc = st.text_area("Description")
            c_cat = st.selectbox("Category", ["General", "Reports", "UserData", "Settings"])
            c_status = st.selectbox("Status", ["Active", "Pending", "Archived"])
            btn_create = st.form_submit_button("Create Item", type="primary")

            if btn_create:
                if not c_title:
                    st.error("Title is required.")
                else:
                    newItem = db.create_item(title=c_title, description=c_desc, category=c_cat, status=c_status)
                    st.success("Record created successfully!")
                    st.json(newItem)

# =========================================================
# VIEW 3: EDGE FUNCTIONS CONSOLE
# =========================================================
elif view_option == "⚡ Edge Functions":
    st.title("⚡ Supabase Deno Edge Functions Console")
    st.write("Interact directly with serverless Deno functions deployed on Supabase.")

    selected_fn = st.selectbox(
        "Select Edge Function to Trigger:",
        ["file-validator-processor", "doc-summarizer", "audit-logger"]
    )

    st.markdown(f"### Payload Editor for `{selected_fn}`")

    default_payloads = {
        "file-validator-processor": {
            "filename": "annual_report_2026.pdf",
            "file_size": 2048576,
            "mime_type": "application/pdf"
        },
        "doc-summarizer": {
            "filename": "notes.md",
            "text_content": "Supabase is an open-source Firebase alternative providing Postgres, Auth, Storage, and Edge Functions on Deno."
        },
        "audit-logger": {
            "action": "MANUAL_UI_TRIGGER",
            "resource_type": "streamlit_ui",
            "resource_id": "dashboard_user",
            "details": {"test_mode": True}
        }
    }

    payload_str = st.text_area(
        "Input JSON Payload:",
        value=json.dumps(default_payloads.get(selected_fn, {}), indent=2),
        height=180
    )

    if st.button("🚀 Invoke Edge Function", type="primary"):
        try:
            payload_json = json.loads(payload_str)
            with st.spinner(f"Invoking {selected_fn}..."):
                res = edge.invoke_function(selected_fn, payload_json)
                st.subheader("Server Response")
                st.json(res)
        except Exception as e:
            st.error(f"Error invoking function: {e}")

# =========================================================
# VIEW 4: AUDIT LOGS TRACKER
# =========================================================
elif view_option == "📜 Audit Logs":
    st.title("📜 System Audit & Access Logs")
    st.write("Real-time stream of all storage downloads, file uploads, updates, and Edge Function triggers.")

    logs = db.list_audit_logs(limit=100)
    if not logs:
        st.info("No audit logs recorded yet.")
    else:
        logs_df = pd.DataFrame(logs)
        st.dataframe(logs_df, use_container_width=True)
