-- ============================================================================
-- AIChatLegal - Supabase PostgreSQL Production Schema
-- Target Project: tbibrvctsbslgdniqugw
-- ============================================================================

-- 1. Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Custom Enums
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('sales_rep', 'sales_head', 'legal_counsel', 'compliance_officer', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE policy_status AS ENUM ('draft', 'pending_legal_review', 'flagged_high_risk', 'approved_with_riders', 'fully_approved', 'rejected');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 3. Table: policies (Sales Submissions & Bank Deal Proposals)
CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_code VARCHAR(64) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    deal_value_usd NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    product_category VARCHAR(100) NOT NULL,
    sales_rep_name VARCHAR(255) NOT NULL,
    sales_head_approval BOOLEAN DEFAULT FALSE,
    raw_content TEXT NOT NULL,
    summary TEXT,
    status policy_status DEFAULT 'pending_legal_review',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Table: policy_embeddings
CREATE TABLE IF NOT EXISTS policy_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Table: risk_scores
CREATE TABLE IF NOT EXISTS risk_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    overall_risk_score INT CHECK (overall_risk_score BETWEEN 0 AND 100),
    risk_level risk_level DEFAULT 'medium',
    regulatory_compliance_score INT CHECK (regulatory_compliance_score BETWEEN 0 AND 100),
    financial_exposure_score INT CHECK (financial_exposure_score BETWEEN 0 AND 100),
    jurisdictional_risk_score INT CHECK (jurisdictional_risk_score BETWEEN 0 AND 100),
    flagged_clauses JSONB DEFAULT '[]'::jsonb,
    ai_recommendation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Table: legal_advice
CREATE TABLE IF NOT EXISTS legal_advice (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    lawyer_name VARCHAR(255) NOT NULL,
    advice_summary TEXT NOT NULL,
    required_riders TEXT[],
    compliance_directives TEXT[],
    decision policy_status NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Table: audit_logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES policies(id) ON DELETE SET NULL,
    actor_name VARCHAR(255) NOT NULL,
    actor_role user_role NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    action_details JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45) DEFAULT '127.0.0.1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Indexes for Scalability
CREATE INDEX IF NOT EXISTS idx_policies_status ON policies(status);
CREATE INDEX IF NOT EXISTS idx_policies_client ON policies(client_name);
CREATE INDEX IF NOT EXISTS idx_policies_created ON policies(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_risk_policy_id ON risk_scores(policy_id);
CREATE INDEX IF NOT EXISTS idx_advice_policy_id ON legal_advice(policy_id);
CREATE INDEX IF NOT EXISTS idx_audit_policy ON audit_logs(policy_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(created_at DESC);

-- HNSW Index for Vector Search
CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw 
ON policy_embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
