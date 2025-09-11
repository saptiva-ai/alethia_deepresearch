-- Aletheia Database Initialization
-- This script sets up the basic database structure for Aletheia

-- Create database if not exists (handled by POSTGRES_DB env var)
-- CREATE DATABASE IF NOT EXISTS aletheia;

-- Create basic tables for research task tracking
CREATE TABLE IF NOT EXISTS research_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    scope VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    task_metadata JSONB,
    result_summary TEXT
);

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_research_tasks_status ON research_tasks(status);
CREATE INDEX IF NOT EXISTS idx_research_tasks_created_at ON research_tasks(created_at DESC);

-- Create table for research artifacts/evidence tracking
CREATE TABLE IF NOT EXISTS research_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES research_tasks(id) ON DELETE CASCADE,
    evidence_id VARCHAR(255) NOT NULL,
    source_url TEXT,
    source_title TEXT,
    excerpt TEXT,
    score FLOAT,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- Create indexes for evidence
CREATE INDEX IF NOT EXISTS idx_research_evidence_task_id ON research_evidence(task_id);
CREATE INDEX IF NOT EXISTS idx_research_evidence_score ON research_evidence(score DESC);

-- Create table for system metrics
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT NOT NULL,
    tags JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for metrics
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON system_metrics(metric_name, timestamp DESC);

-- Create a function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for research_tasks table
CREATE TRIGGER update_research_tasks_updated_at 
    BEFORE UPDATE ON research_tasks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for testing
INSERT INTO research_tasks (query, status, scope) VALUES 
    ('Sample research query', 'completed', 'test'),
    ('Another test query', 'pending', 'development')
ON CONFLICT DO NOTHING;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aletheia_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aletheia_user;