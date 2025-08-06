-- Safe Dual Table Schema for AI Video Analysis System
-- Handles existing tables and policies gracefully

-- Original videos table - stores the uploaded videos
CREATE TABLE IF NOT EXISTS original_videos (
    id SERIAL PRIMARY KEY,
    video_hash VARCHAR(64) UNIQUE NOT NULL,  -- Unique identifier for the video content
    video_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,  -- Path in Supabase storage
    file_size BIGINT,  -- File size in bytes
    duration_seconds INTEGER,  -- Video duration if available
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Processed videos table - stores the processed videos with annotations
CREATE TABLE IF NOT EXISTS processed_videos (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    original_video_hash VARCHAR(64) NOT NULL,  -- References original_videos
    processed_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,  -- Path in Supabase storage
    file_size BIGINT,  -- File size in bytes
    processing_type VARCHAR(50) NOT NULL,  -- 'detection', 'identification', 'payment_detection'
    processing_status VARCHAR(20) DEFAULT 'processing',  -- 'processing', 'completed', 'failed'
    processing_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (original_video_hash) REFERENCES original_videos(video_hash) ON DELETE CASCADE
);

-- Processing sessions table - stores session metadata
CREATE TABLE IF NOT EXISTS processing_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    original_video_hash VARCHAR(64) NOT NULL,  -- References original_videos
    workflow_mode VARCHAR(50) NOT NULL,  -- 'detect_identify' or 'payment_only'
    status VARCHAR(20) DEFAULT 'processing',  -- 'processing', 'completed', 'failed'
    session_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (original_video_hash) REFERENCES original_videos(video_hash) ON DELETE CASCADE
);

-- Persons table - stores detected and identified persons
CREATE TABLE IF NOT EXISTS persons (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    person_id VARCHAR(50) NOT NULL,
    person_type VARCHAR(20) NOT NULL, -- 'detected' or 'identified'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES processing_sessions(session_id) ON DELETE CASCADE
);

-- Face images table - stores metadata for face images
CREATE TABLE IF NOT EXISTS face_images (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    person_id VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- 'first_detection', 'frame_*'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES processing_sessions(session_id) ON DELETE CASCADE
);

-- Payment results table - stores payment detection results
CREATE TABLE IF NOT EXISTS payment_results (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    total_payments INTEGER DEFAULT 0,
    cash_payments INTEGER DEFAULT 0,
    card_payments INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES processing_sessions(session_id) ON DELETE CASCADE
);

-- Create indexes for better performance (ignore if they exist)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_original_videos_hash') THEN
        CREATE INDEX idx_original_videos_hash ON original_videos(video_hash);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_processed_videos_session_id') THEN
        CREATE INDEX idx_processed_videos_session_id ON processed_videos(session_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_processed_videos_original_hash') THEN
        CREATE INDEX idx_processed_videos_original_hash ON processed_videos(original_video_hash);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_processing_sessions_session_id') THEN
        CREATE INDEX idx_processing_sessions_session_id ON processing_sessions(session_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_processing_sessions_video_hash') THEN
        CREATE INDEX idx_processing_sessions_video_hash ON processing_sessions(original_video_hash);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_persons_session_id') THEN
        CREATE INDEX idx_persons_session_id ON persons(session_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_face_images_session_person') THEN
        CREATE INDEX idx_face_images_session_person ON face_images(session_id, person_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_payment_results_session_id') THEN
        CREATE INDEX idx_payment_results_session_id ON payment_results(session_id);
    END IF;
END $$;

-- Enable Row Level Security (ignore if already enabled)
ALTER TABLE original_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE persons ENABLE ROW LEVEL SECURITY;
ALTER TABLE face_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_results ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (ignore if they exist)
DO $$ 
BEGIN
    -- Original videos policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'original_videos' AND policyname = 'Allow public access to original_videos') THEN
        CREATE POLICY "Allow public access to original_videos" ON original_videos FOR ALL USING (true);
    END IF;
    
    -- Processed videos policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'processed_videos' AND policyname = 'Allow public access to processed_videos') THEN
        CREATE POLICY "Allow public access to processed_videos" ON processed_videos FOR ALL USING (true);
    END IF;
    
    -- Processing sessions policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'processing_sessions' AND policyname = 'Allow public access to processing_sessions') THEN
        CREATE POLICY "Allow public access to processing_sessions" ON processing_sessions FOR ALL USING (true);
    END IF;
    
    -- Persons policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'persons' AND policyname = 'Allow public access to persons') THEN
        CREATE POLICY "Allow public access to persons" ON persons FOR ALL USING (true);
    END IF;
    
    -- Face images policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'face_images' AND policyname = 'Allow public access to face_images') THEN
        CREATE POLICY "Allow public access to face_images" ON face_images FOR ALL USING (true);
    END IF;
    
    -- Payment results policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'payment_results' AND policyname = 'Allow public access to payment_results') THEN
        CREATE POLICY "Allow public access to payment_results" ON payment_results FOR ALL USING (true);
    END IF;
END $$;

-- Create storage bucket for video analysis files
INSERT INTO storage.buckets (id, name, public) 
VALUES ('video-analysis', 'video-analysis', true)
ON CONFLICT (id) DO NOTHING;

-- Create storage policies (ignore if they exist)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND policyname = 'Allow public access to video-analysis bucket') THEN
        CREATE POLICY "Allow public access to video-analysis bucket" ON storage.objects
        FOR ALL USING (bucket_id = 'video-analysis');
    END IF;
END $$;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for processing_sessions table (ignore if exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_processing_sessions_updated_at') THEN
        CREATE TRIGGER update_processing_sessions_updated_at 
            BEFORE UPDATE ON processing_sessions 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Create or replace view for easy session data retrieval with both original and processed videos
CREATE OR REPLACE VIEW session_summary_complete AS
SELECT 
    ps.session_id,
    ps.workflow_mode,
    ps.status as session_status,
    ps.session_started_at,
    ps.session_completed_at,
    ov.video_filename as original_filename,
    ov.file_size as original_file_size,
    ov.duration_seconds,
    ov.uploaded_at,
    pv.processed_filename,
    pv.file_size as processed_file_size,
    pv.processing_type,
    pv.processing_status,
    pv.processing_started_at,
    pv.processing_completed_at,
    COUNT(DISTINCT p.person_id) as total_persons,
    COUNT(DISTINCT CASE WHEN p.person_type = 'detected' THEN p.person_id END) as detected_persons,
    COUNT(DISTINCT CASE WHEN p.person_type = 'identified' THEN p.person_id END) as identified_persons,
    pr.total_payments,
    pr.cash_payments,
    pr.card_payments
FROM processing_sessions ps
LEFT JOIN original_videos ov ON ps.original_video_hash = ov.video_hash
LEFT JOIN processed_videos pv ON ps.session_id = pv.session_id
LEFT JOIN persons p ON ps.session_id = p.session_id
LEFT JOIN payment_results pr ON ps.session_id = pr.session_id
GROUP BY ps.session_id, ps.workflow_mode, ps.status, ps.session_started_at, ps.session_completed_at,
         ov.video_filename, ov.file_size, ov.duration_seconds, ov.uploaded_at,
         pv.processed_filename, pv.file_size, pv.processing_type, pv.processing_status,
         pv.processing_started_at, pv.processing_completed_at,
         pr.total_payments, pr.cash_payments, pr.card_payments;

-- Create or replace view for original videos summary
CREATE OR REPLACE VIEW original_videos_summary AS
SELECT 
    ov.video_hash,
    ov.video_filename,
    ov.file_size,
    ov.duration_seconds,
    ov.uploaded_at,
    COUNT(DISTINCT ps.session_id) as total_processing_sessions,
    COUNT(DISTINCT pv.session_id) as total_processed_videos,
    MAX(ps.session_completed_at) as last_processed_at
FROM original_videos ov
LEFT JOIN processing_sessions ps ON ov.video_hash = ps.original_video_hash
LEFT JOIN processed_videos pv ON ov.video_hash = pv.original_video_hash
GROUP BY ov.video_hash, ov.video_filename, ov.file_size, ov.duration_seconds, ov.uploaded_at; 