-- Create context_cache table for Phase 3 state persistence
CREATE TABLE IF NOT EXISTS context_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(255) NOT NULL UNIQUE,
    conversation_id VARCHAR(255) NOT NULL,
    sinistro_id VARCHAR(255),
    context_data JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    ttl_hours INT DEFAULT 24,
    expires_at TIMESTAMP GENERATED ALWAYS AS (created_at + INTERVAL '1 hour' * ttl_hours) STORED
);

CREATE INDEX idx_conversation_id ON context_cache(conversation_id);
CREATE INDEX idx_sinistro_id ON context_cache(sinistro_id);
CREATE INDEX idx_cache_key ON context_cache(cache_key);
CREATE INDEX idx_expires_at ON context_cache(expires_at);

-- Add row-level security
ALTER TABLE context_cache ENABLE ROW LEVEL SECURITY;

-- Create policy for authenticated users
CREATE POLICY "Enable read access for all authenticated users" ON context_cache
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert access for all authenticated users" ON context_cache
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update access for all authenticated users" ON context_cache
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Add cleanup function for expired records
CREATE OR REPLACE FUNCTION cleanup_expired_context_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM context_cache WHERE expires_at < now();
END;
$$ LANGUAGE plpgsql;
