-- =========================================================
-- Supabase Schema for CRUD App (Database + Storage + Audit Logs)
-- Run this SQL script in the Supabase Dashboard SQL Editor
-- =========================================================

-- Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------
-- 1. Table: files_metadata
-- Stores metadata for uploaded files in Supabase Storage
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.files_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_size BIGINT NOT NULL,
    mime_type TEXT NOT NULL,
    file_hash TEXT,
    summary TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'validated', 'processed', 'error'
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    metadata_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------
-- 2. Table: database_items
-- Standard table for Database CRUD operations demo
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.database_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'General',
    status TEXT DEFAULT 'Active', -- 'Active', 'Pending', 'Archived'
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------
-- 3. Table: audit_logs
-- Immutable log of file & system access events
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action TEXT NOT NULL, -- 'UPLOAD', 'DOWNLOAD', 'UPDATE', 'DELETE', 'EDGE_FUNCTION'
    resource_type TEXT NOT NULL, -- 'storage', 'database', 'edge_function'
    resource_id TEXT,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------
-- Automatic updated_at Trigger Function
-- ---------------------------------------------------------
CREATE OR REPLACE FUNCTION update_timestamp_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_files_metadata_timestamp
    BEFORE UPDATE ON public.files_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp_column();

CREATE TRIGGER update_database_items_timestamp
    BEFORE UPDATE ON public.database_items
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp_column();

-- ---------------------------------------------------------
-- Storage Bucket Setup (Bucket Name: documents)
-- ---------------------------------------------------------
INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', true)
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------
-- Row Level Security (RLS) Policies
-- Allow public select/insert/update/delete for demo purposes
-- ---------------------------------------------------------
ALTER TABLE public.files_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.database_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read on files_metadata" ON public.files_metadata FOR SELECT USING (true);
CREATE POLICY "Allow public write on files_metadata" ON public.files_metadata FOR ALL USING (true);

CREATE POLICY "Allow public read on database_items" ON public.database_items FOR SELECT USING (true);
CREATE POLICY "Allow public write on database_items" ON public.database_items FOR ALL USING (true);

CREATE POLICY "Allow public read on audit_logs" ON public.audit_logs FOR SELECT USING (true);
CREATE POLICY "Allow public write on audit_logs" ON public.audit_logs FOR ALL USING (true);

-- Storage bucket RLS Policies
CREATE POLICY "Public Access Bucket Policy" ON storage.objects FOR SELECT USING (bucket_id = 'documents');
CREATE POLICY "Public Upload Bucket Policy" ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'documents');
CREATE POLICY "Public Update Bucket Policy" ON storage.objects FOR UPDATE USING (bucket_id = 'documents');
CREATE POLICY "Public Delete Bucket Policy" ON storage.objects FOR DELETE USING (bucket_id = 'documents');
