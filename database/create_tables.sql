-- Database schema for FastenersAI Bot
-- Based on the comprehensive specification

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Items table - main catalog
CREATE TABLE IF NOT EXISTS items (
  id BIGSERIAL PRIMARY KEY,
  ku TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  specs_json JSONB DEFAULT '{}'::jsonb,
  pack_qty NUMERIC,
  price NUMERIC,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- SKU aliases table for fuzzy matching
CREATE TABLE IF NOT EXISTS sku_aliases (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT,
  alias TEXT NOT NULL,
  ku TEXT NOT NULL REFERENCES items(ku) ON DELETE CASCADE,
  weight NUMERIC DEFAULT 1.0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Requests table - main request tracking
CREATE TABLE IF NOT EXISTS requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT,
  chat_id TEXT,
  user_id TEXT,
  status TEXT DEFAULT 'pending',
  source TEXT,               -- text/excel/image/voice
  storage_uri TEXT,          -- исходник в Supabase Storage
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Request lines table - individual line items
CREATE TABLE IF NOT EXISTS request_lines (
  id BIGSERIAL PRIMARY KEY,
  request_id UUID REFERENCES requests(id) ON DELETE CASCADE,
  line_no INT,
  raw_text TEXT,
  normalized_text TEXT,
  chosen_ku TEXT,            -- финальный выбор, может быть NULL
  qty_packs NUMERIC,         -- если удалось извлечь
  qty_units NUMERIC,         -- qty_packs * pack_qty если pack_qty задан
  price NUMERIC,
  total NUMERIC,
  status TEXT DEFAULT 'pending', -- ok / needs_review / not_found / error
  chosen_method TEXT,        -- rules/vector/gpt/manual
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Candidates table - search results for each line
CREATE TABLE IF NOT EXISTS candidates (
  id BIGSERIAL PRIMARY KEY,
  request_line_id BIGINT REFERENCES request_lines(id) ON DELETE CASCADE,
  ku TEXT REFERENCES items(ku),
  name TEXT,
  score NUMERIC,             -- 0..1
  pack_qty NUMERIC,
  price NUMERIC,
  explanation TEXT,          -- если GPT участвовал
  source TEXT,               -- rules/vector/gpt
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_items_ku ON items(ku);
CREATE INDEX IF NOT EXISTS idx_items_active ON items(is_active);
CREATE INDEX IF NOT EXISTS idx_sku_aliases_alias ON sku_aliases(alias);
CREATE INDEX IF NOT EXISTS idx_sku_aliases_ku ON sku_aliases(ku);
CREATE INDEX IF NOT EXISTS idx_requests_chat_id ON requests(chat_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_request_lines_request_id ON request_lines(request_id);
CREATE INDEX IF NOT EXISTS idx_request_lines_status ON request_lines(status);
CREATE INDEX IF NOT EXISTS idx_candidates_request_line_id ON candidates(request_line_id);
CREATE INDEX IF NOT EXISTS idx_candidates_ku ON candidates(ku);

-- RLS (Row Level Security) policies
-- Enable RLS on all tables
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
ALTER TABLE sku_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE request_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (can be customized per tenant)
-- For now, allow all operations for authenticated users
CREATE POLICY "Allow all for authenticated users" ON items FOR ALL USING (true);
CREATE POLICY "Allow all for authenticated users" ON sku_aliases FOR ALL USING (true);
CREATE POLICY "Allow all for authenticated users" ON requests FOR ALL USING (true);
CREATE POLICY "Allow all for authenticated users" ON request_lines FOR ALL USING (true);
CREATE POLICY "Allow all for authenticated users" ON candidates FOR ALL USING (true);

-- Functions for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_items_updated_at BEFORE UPDATE ON items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_requests_updated_at BEFORE UPDATE ON requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_request_lines_updated_at BEFORE UPDATE ON request_lines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample data insertion (for testing)
INSERT INTO items (ku, name, specs_json, pack_qty, price) VALUES
('BOLT-M10x30-8.8', 'Болт DIN 933 кл.пр.8.8 М10х30, цинк', '{"diameter": "M10", "length": "30", "strength_class": "8.8", "coating": "цинк"}', 100, 2.50),
('BOLT-M12x40-8.8', 'Болт DIN 933 кл.пр.8.8 М12х40, цинк', '{"diameter": "M12", "length": "40", "strength_class": "8.8", "coating": "цинк"}', 50, 3.20),
('ANCHOR-M10x100', 'Анкер клиновой оцинк. М10х100', '{"diameter": "M10", "length": "100", "type": "клиновой", "coating": "оцинк"}', 25, 15.80),
('ANCHOR-M12x120', 'Анкер клиновой оцинк. М12х120', '{"diameter": "M12", "length": "120", "type": "клиновой", "coating": "оцинк"}', 20, 18.50)
ON CONFLICT (ku) DO NOTHING;

-- Sample aliases
INSERT INTO sku_aliases (alias, ku, weight) VALUES
('болт м10х30', 'BOLT-M10x30-8.8', 1.0),
('болт din 933 м10х30', 'BOLT-M10x30-8.8', 1.0),
('анкер м10х100', 'ANCHOR-M10x100', 1.0),
('анкер клиновой м10х100', 'ANCHOR-M10x100', 1.0)
ON CONFLICT DO NOTHING;