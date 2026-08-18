import os
import sys
import json
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from python_client.db_crud import DatabaseCRUD
from python_client.storage_crud import StorageCRUD
from python_client.edge_invoker import EdgeInvoker

console = Console()

class SupabaseTerminalApp:
    """
    Interactive Terminal CLI CRUD Application for Supabase
    Handles Database Tables, Storage Files, and Edge Function Triggers.
    """

    def __init__(self):
        try:
            self.db = DatabaseCRUD()
            self.storage = StorageCRUD()
            self.edge = EdgeInvoker()
        except Exception as e:
            console.print(Panel(f"[bold red]Initialization Error:[/bold red] {e}\n\n[yellow]Please ensure your .env file contains valid SUPABASE_URL and SUPABASE_ANON_KEY credentials.[/yellow]", title="Supabase Client Error"))
            sys.exit(1)

    def display_banner(self):
        console.print(
            Panel(
                "[bold green]Supabase Full-Stack CRUD Application (CLI)[/bold green]\n"
                "[cyan]Database Postgres + Supabase Storage + 3 Deno Edge Functions[/cyan]",
                border_style="green"
            )
        )

    def main_menu(self):
        while True:
            console.print("\n[bold yellow]=== MAIN MENU ===[/bold yellow]")
            console.print("1. 📁 Storage CRUD (Upload, List, Download, Update, Delete Files)")
            console.print("2. 📊 Database Table CRUD (Create, Read, Update, Delete Records)")
            console.print("3. ⚡ Invoke Edge Functions Directly")
            console.print("4. 📜 View System Audit Logs")
            console.print("5. 🚪 Exit")

            choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5"], default="1")

            if choice == "1":
                self.storage_menu()
            elif choice == "2":
                self.db_menu()
            elif choice == "3":
                self.edge_menu()
            elif choice == "4":
                self.view_audit_logs()
            elif choice == "5":
                console.print("[green]Goodbye![/green]")
                break

    # =========================================================
    # 1. STORAGE FILE CRUD MENU
    # =========================================================
    def storage_menu(self):
        while True:
            console.print("\n[bold cyan]--- STORAGE FILES CRUD ---[/bold cyan]")
            console.print("1. 📤 Upload File (Create)")
            console.print("2. 📋 List Uploaded Files (Read)")
            console.print("3. 📥 Generate Signed Download Link (Read)")
            console.print("4. ✏️ Update File Metadata (Update)")
            console.print("5. 🗑️ Delete File (Delete)")
            console.print("6. ⬅️ Back to Main Menu")

            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6"], default="1")

            if choice == "1":
                self.storage_upload()
            elif choice == "2":
                self.storage_list()
            elif choice == "3":
                self.storage_download_link()
            elif choice == "4":
                self.storage_update()
            elif choice == "5":
                self.storage_delete()
            elif choice == "6":
                break

    def storage_upload(self):
        file_path = Prompt.ask("\nEnter local file path to upload")
        if not os.path.exists(file_path):
            console.print(f"[red]File not found at path: {file_path}[/red]")
            return

        filename = os.path.basename(file_path)
        dest_name = Prompt.ask("Enter destination filename in storage", default=filename)
        mime_type = Prompt.ask("Enter MIME type", default="application/octet-stream")

        console.print("[yellow]Validating file via 'file-validator-processor' Edge Function & uploading...[/yellow]")
        try:
            res = self.storage.upload_file(
                file_path_or_bytes=file_path,
                filename=dest_name,
                content_type=mime_type,
                validate_edge_fn=True
            )
            console.print(Panel(f"[bold green]File Uploaded Successfully![/bold green]\n\nStorage Key: {res.get('storage_key')}\nDatabase ID: {res.get('metadata', {}).get('id')}", title="Upload Status"))
        except Exception as e:
            console.print(f"[bold red]Upload Failed:[/bold red] {e}")

    def storage_list(self):
        console.print("\n[yellow]Fetching files from Supabase Storage & Metadata DB...[/yellow]")
        files = self.storage.list_files()
        if not files:
            console.print("[yellow]No files found in storage metadata table.[/yellow]")
            return

        table = Table(title="Supabase Storage Files")
        table.add_column("Filename", style="cyan")
        table.add_column("Storage Key", style="magenta")
        table.add_column("Size (KB)", style="green")
        table.add_column("MIME Type", style="blue")
        table.add_column("Status", style="yellow")
        table.add_column("Uploaded At", style="white")

        for f in files:
            size_kb = f.get("file_size", 0) / 1024
            table.add_row(
                f.get("filename", ""),
                f.get("file_path", ""),
                f"{size_kb:.2f} KB",
                f.get("mime_type", ""),
                f.get("status", "validated"),
                str(f.get("created_at", ""))[:19]
            )
        console.print(table)

    def storage_download_link(self):
        files = self.storage.list_files()
        if not files:
            console.print("[yellow]No files available to download.[/yellow]")
            return
        
        storage_key = Prompt.ask("Enter Storage Key to generate download link")
        expires = int(Prompt.ask("Enter URL expiration time in seconds", default="3600"))

        try:
            signed_url = self.storage.create_signed_url(storage_key, expires)
            console.print(Panel(f"[bold green]Signed Download URL Generated:[/bold green]\n{signed_url}", title="Secure Signed URL"))
        except Exception as e:
            console.print(f"[red]Error generating signed URL:[/red] {e}")

    def storage_update(self):
        storage_key = Prompt.ask("Enter Storage Key of file to update metadata")
        new_summary = Prompt.ask("Enter new document summary (leave blank to skip)", default="")
        new_tags = Prompt.ask("Enter comma-separated tags (leave blank to skip)", default="")

        updates = {}
        if new_summary:
            updates["summary"] = new_summary
        if new_tags:
            updates["tags"] = [t.strip() for t in new_tags.split(",")]

        if not updates:
            console.print("[yellow]No updates specified.[/yellow]")
            return

        res = self.storage.update_file(storage_key, metadata_updates=updates)
        console.print(f"[green]Metadata updated for '{storage_key}'![/green]")

    def storage_delete(self):
        storage_key = Prompt.ask("Enter Storage Key of file to delete")
        if Confirm.ask(f"Are you sure you want to PERMANENTLY delete '{storage_key}'?"):
            success = self.storage.delete_file(storage_key)
            if success:
                console.print(f"[bold green]File '{storage_key}' successfully deleted from Storage & Postgres![/bold green]")
            else:
                console.print(f"[red]Failed to delete '{storage_key}' from database metadata.[/red]")

    # =========================================================
    # 2. DATABASE TABLE CRUD MENU
    # =========================================================
    def db_menu(self):
        while True:
            console.print("\n[bold cyan]--- DATABASE TABLE CRUD ('database_items') ---[/bold cyan]")
            console.print("1. ➕ Create Record")
            console.print("2. 🔍 Read / List Records")
            console.print("3. ✏️ Update Record")
            console.print("4. 🗑️ Delete Record")
            console.print("5. ⬅️ Back to Main Menu")

            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"], default="1")

            if choice == "1":
                self.db_create()
            elif choice == "2":
                self.db_read()
            elif choice == "3":
                self.db_update()
            elif choice == "4":
                self.db_delete()
            elif choice == "5":
                break

    def db_create(self):
        title = Prompt.ask("\nEnter item title")
        description = Prompt.ask("Enter description", default="")
        category = Prompt.ask("Enter category", default="General")
        status = Prompt.ask("Enter status", default="Active")

        item = self.db.create_item(title=title, description=description, category=category, status=status)
        console.print(Panel(f"[bold green]Record Created![/bold green]\n\nID: {item.get('id')}\nTitle: {item.get('title')}", title="Database Insert"))

    def db_read(self):
        items = self.db.get_items()
        if not items:
            console.print("[yellow]No records found in 'database_items' table.[/yellow]")
            return

        table = Table(title="Database Items")
        table.add_column("ID", style="magenta")
        table.add_column("Title", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Created At", style="white")

        for item in items:
            table.add_row(
                item.get("id", "")[:8] + "...",
                item.get("title", ""),
                item.get("category", ""),
                item.get("status", ""),
                str(item.get("created_at", ""))[:19]
            )
        console.print(table)

    def db_update(self):
        item_id = Prompt.ask("Enter full Item UUID to update")
        new_title = Prompt.ask("Enter new title (leave blank to skip)", default="")
        new_status = Prompt.ask("Enter new status (Active/Pending/Archived)", default="")

        updates = {}
        if new_title:
            updates["title"] = new_title
        if new_status:
            updates["status"] = new_status

        if not updates:
            console.print("[yellow]No updates provided.[/yellow]")
            return

        res = self.db.update_item(item_id, updates)
        console.print(f"[green]Record '{item_id}' updated successfully![/green]")

    def db_delete(self):
        item_id = Prompt.ask("Enter Item UUID to delete")
        if Confirm.ask(f"Delete record '{item_id}'?"):
            ok = self.db.delete_item(item_id)
            if ok:
                console.print(f"[green]Record '{item_id}' deleted![/green]")
            else:
                console.print(f"[red]Failed to delete record '{item_id}'.[/red]")

    # =========================================================
    # 3. EDGE FUNCTIONS DIRECT TRIGGER MENU
    # =========================================================
    def edge_menu(self):
        console.print("\n[bold magenta]--- EDGE FUNCTIONS CONSOLE ---[/bold magenta]")
        console.print("1. file-validator-processor (Validate File Payload)")
        console.print("2. doc-summarizer (Extract & Summarize Text)")
        console.print("3. audit-logger (Log Audit Event)")

        choice = Prompt.ask("Select Edge Function to trigger", choices=["1", "2", "3"], default="1")

        if choice == "1":
            fname = Prompt.ask("Enter sample filename", default="test_document.pdf")
            fsize = int(Prompt.ask("Enter file size in bytes", default="1048576"))
            res = self.edge.validate_file(filename=fname, file_size=fsize, mime_type="application/pdf")
        elif choice == "2":
            fname = Prompt.ask("Enter sample filename", default="notes.txt")
            text = Prompt.ask("Enter text content to summarize", default="Supabase provides Postgres database, authentication, storage, and serverless Edge Functions running on Deno.")
            res = self.edge.summarize_document(filename=fname, text_content=text)
        elif choice == "3":
            res = self.edge.log_audit(action="MANUAL_TEST", resource_type="cli", resource_id="terminal_session")

        console.print(Panel(json.dumps(res, indent=2), title="Edge Function Response"))

    def view_audit_logs(self):
        logs = self.db.list_audit_logs(limit=20)
        if not logs:
            console.print("[yellow]No audit logs recorded yet.[/yellow]")
            return

        table = Table(title="System Audit Logs")
        table.add_column("Action", style="green")
        table.add_column("Resource Type", style="cyan")
        table.add_column("Resource ID", style="magenta")
        table.add_column("Timestamp", style="white")

        for log in logs:
            table.add_row(
                log.get("action", ""),
                log.get("resource_type", ""),
                log.get("resource_id", ""),
                str(log.get("created_at", ""))[:19]
            )
        console.print(table)

def main():
    app = SupabaseTerminalApp()
    app.display_banner()
    app.main_menu()

if __name__ == "__main__":
    main()
