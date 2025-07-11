-- Supabase Database Schema for Metra Platform
-- Run this in your Supabase SQL editor to create the necessary tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    subscription_tier TEXT DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    project_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    task_type TEXT NOT NULL, -- 'text-generation', 'classification', 'qa', etc.
    language TEXT DEFAULT 'english',
    domain TEXT DEFAULT 'general',
    status TEXT DEFAULT 'active', -- 'active', 'paused', 'archived'
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data Collection Jobs table
CREATE TABLE IF NOT EXISTS data_collection_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending', -- 'pending', 'collecting', 'processing_dfe', 'completed', 'failed'
    progress INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    collected_count INTEGER DEFAULT 0,
    sources_progress JSONB DEFAULT '{}',
    errors TEXT[],
    message TEXT,
    config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Training Jobs table
CREATE TABLE IF NOT EXISTS training_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    task_name TEXT NOT NULL,
    task_description TEXT,
    base_model TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'preparing', 'training', 'completed', 'failed'
    progress INTEGER DEFAULT 0,
    data_count INTEGER DEFAULT 0,
    training_config JSONB DEFAULT '{}',
    logs JSONB DEFAULT '[]',
    metrics JSONB DEFAULT '{}',
    model_url TEXT,
    replicate_training_id TEXT,
    openai_job_id TEXT,
    exports JSONB DEFAULT '{}',
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Collected Data table
CREATE TABLE IF NOT EXISTS collected_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id TEXT NOT NULL,
    text TEXT NOT NULL,
    title TEXT,
    url TEXT,
    source TEXT,
    label TEXT DEFAULT 'unknown',
    confidence FLOAT DEFAULT 0.0,
    task_type TEXT,
    processed_at TIMESTAMP WITH TIME ZONE,
    processed_by TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model Exports table
CREATE TABLE IF NOT EXISTS model_exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    export_id TEXT UNIQUE NOT NULL,
    training_job_id UUID REFERENCES training_jobs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    format TEXT NOT NULL, -- 'pytorch', 'gguf', 'openai'
    status TEXT DEFAULT 'preparing', -- 'preparing', 'exporting', 'completed', 'failed'
    progress INTEGER DEFAULT 0,
    file_path TEXT,
    download_url TEXT,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Invitations table (for invitation-only system)
CREATE TABLE IF NOT EXISTS invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    invitation_code TEXT UNIQUE NOT NULL,
    invited_by UUID REFERENCES users(id),
    used_at TIMESTAMP WITH TIME ZONE,
    used_by UUID REFERENCES users(id),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '7 days'),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_auth_user_id ON users(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_data_collection_jobs_user_id ON data_collection_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_data_collection_jobs_job_id ON data_collection_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_training_jobs_user_id ON training_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_training_jobs_job_id ON training_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_collected_data_job_id ON collected_data(job_id);
CREATE INDEX IF NOT EXISTS idx_model_exports_training_job_id ON model_exports(training_job_id);
CREATE INDEX IF NOT EXISTS idx_invitations_email ON invitations(email);
CREATE INDEX IF NOT EXISTS idx_invitations_code ON invitations(invitation_code);

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_collection_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE collected_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_exports ENABLE ROW LEVEL SECURITY;
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = auth_user_id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = auth_user_id);

-- Projects policies
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT USING (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

CREATE POLICY "Users can create own projects" ON projects
    FOR INSERT WITH CHECK (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE USING (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE USING (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

-- Data collection jobs policies
CREATE POLICY "Users can view own data collection jobs" ON data_collection_jobs
    FOR SELECT USING (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

CREATE POLICY "Users can create own data collection jobs" ON data_collection_jobs
    FOR INSERT WITH CHECK (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

CREATE POLICY "Users can update own data collection jobs" ON data_collection_jobs
    FOR UPDATE USING (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

-- Training jobs policies
CREATE POLICY "Users can view own training jobs" ON training_jobs
    FOR SELECT USING (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

CREATE POLICY "Users can create own training jobs" ON training_jobs
    FOR INSERT WITH CHECK (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

CREATE POLICY "Users can update own training jobs" ON training_jobs
    FOR UPDATE USING (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

-- Collected data policies
CREATE POLICY "Users can view own collected data" ON collected_data
    FOR SELECT USING (job_id IN (
        SELECT job_id FROM data_collection_jobs 
        WHERE user_id IN (
            SELECT id FROM users WHERE auth_user_id = auth.uid()
        )
    ));

CREATE POLICY "System can insert collected data" ON collected_data
    FOR INSERT WITH CHECK (true); -- Allow system to insert during collection

-- Model exports policies
CREATE POLICY "Users can view own model exports" ON model_exports
    FOR SELECT USING (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

CREATE POLICY "Users can create own model exports" ON model_exports
    FOR INSERT WITH CHECK (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

CREATE POLICY "Users can update own model exports" ON model_exports
    FOR UPDATE USING (user_id IN (
        SELECT id FROM users WHERE auth_user_id = auth.uid()
    ));

-- Invitations policies (admin only for now)
CREATE POLICY "Service role can manage invitations" ON invitations
    FOR ALL USING (true);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_collection_jobs_updated_at BEFORE UPDATE ON data_collection_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_training_jobs_updated_at BEFORE UPDATE ON training_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_model_exports_updated_at BEFORE UPDATE ON model_exports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert a test user for development
INSERT INTO users (auth_user_id, email, full_name) VALUES 
(uuid_generate_v4(), 'test@metra.ai', 'Test User')
ON CONFLICT (email) DO NOTHING;

-- Create a sample project for testing
INSERT INTO projects (user_id, name, description, task_type, language, domain) 
SELECT u.id, '中医AI诊断系统', '基于中医理论的AI诊断治疗系统', 'text-generation', 'chinese', 'health'
FROM users u WHERE u.email = 'test@metra.ai'
ON CONFLICT DO NOTHING;