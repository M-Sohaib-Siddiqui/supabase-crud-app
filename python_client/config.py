import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load local .env file if available
load_dotenv()

def get_config_val(key: str, default: str = "") -> str:
    """
    Retrieve configuration value from Streamlit Secrets or Environment/.env file.
    """
    # 1. Try Streamlit Secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass

    # 2. Try OS Environment variables / .env file
    return os.getenv(key, default)

SUPABASE_URL = get_config_val("SUPABASE_URL")
SUPABASE_ANON_KEY = get_config_val("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = get_config_val("SUPABASE_SERVICE_ROLE_KEY")
STORAGE_BUCKET = get_config_val("SUPABASE_STORAGE_BUCKET", "documents")

def init_supabase() -> Client:
    """
    Initialize and return the Supabase client.
    """
    url = get_config_val("SUPABASE_URL")
    key = get_config_val("SUPABASE_ANON_KEY")

    if not url or url == "https://your-project-id.supabase.co":
        raise ValueError(
            "SUPABASE_URL is missing or set to placeholder. Please set your credentials in .env or Streamlit Secrets."
        )
    if not key or key == "your-supabase-anon-key":
        raise ValueError(
            "SUPABASE_ANON_KEY is missing or set to placeholder. Please set your credentials in .env or Streamlit Secrets."
        )

    return create_client(url, key)
