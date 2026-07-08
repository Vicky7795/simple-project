-- Field rep / user
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'field_rep',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Healthcare Professional (HCP)
CREATE TABLE hcps (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    specialty VARCHAR(100),
    hospital_affiliation VARCHAR(150),
    email VARCHAR(150),
    phone VARCHAR(30),
    preferred_channel VARCHAR(30), -- call/visit/email
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Interaction log (core entity)
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    hcp_id INTEGER REFERENCES hcps(id),
    user_id INTEGER REFERENCES users(id),
    interaction_type VARCHAR(30),      -- visit/call/email/conference
    interaction_date TIMESTAMP,
    channel VARCHAR(30),
    topics_discussed TEXT[],           -- e.g. ['cardiology drug X', 'samples']
    products_discussed TEXT[],         -- e.g. ['CardioShield']
    sentiment VARCHAR(20),             -- positive/neutral/negative
    summary TEXT,                      -- LLM-generated or manual
    raw_input TEXT,                    -- original chat/free text (if conversational)
    source VARCHAR(20),                -- 'form' or 'chat'
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    samples_distributed JSONB,         -- {"product": "X", "qty": 10}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Edit/audit history (needed for the "Edit Interaction" tool)
CREATE TABLE interaction_edits (
    id SERIAL PRIMARY KEY,
    interaction_id INTEGER REFERENCES interactions(id),
    edited_field VARCHAR(60),
    old_value TEXT,
    new_value TEXT,
    edited_by INTEGER REFERENCES users(id),
    edited_at TIMESTAMP DEFAULT NOW()
);

-- Chat session state (for LangGraph conversational logging)
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    thread_id VARCHAR(80) UNIQUE,      -- LangGraph checkpointer thread id
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);
