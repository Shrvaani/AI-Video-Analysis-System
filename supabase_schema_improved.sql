-- Improved Supabase Database Schema for AI Video Analysis System
-- Focus: Store only original videos, separate metadata from processing results

-- Enable Row Level Security (RLS)
ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret';

-- Original videos table - stores only the original uploaded videos
CREATE TABLE IF NOT EXISTS original_videos (
    id SERIAL PRIMARY KEY,
    video_hash VARCHAR(64) UNIQUE NOT NULL,  -- Unique identifier for the video content
    video_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,  -- Path in Supabase storage
    file_size BIGINT,  -- File size in bytes
    duration_seconds INTEGER,  -- Video duration if available
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Processing sessions table - stores processing metadata (no video duplication)
CREATE TABLE IF NOT EXISTS processing_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    video_hash VARCHAR(64) NOT NULL,  -- References original_videos
    workflow_mode VARCHAR(50) NOT NULL,  -- 'detect_identify' or 'payment_only'
    status VARCHAR(20) DEFAULT 'processing',  -- 'processing', 'completed', 'failed'
    processing_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (video_hash) REFERENCES original_videos(video_hash) ON DELETE CASCADE
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_original_videos_hash ON original_videos(video_hash);
CREATE INDEX IF NOT EXISTS idx_processing_sessions_session_id ON processing_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_processing_sessions_video_hash ON processing_sessions(video_hash);
CREATE INDEX IF NOT EXISTS idx_persons_session_id ON persons(session_id);
CREATE INDEX IF NOT EXISTS idx_face_images_session_person ON face_images(session_id, person_id);
CREATE INDEX IF NOT EXISTS idx_payment_results_session_id ON payment_results(session_id);

-- Enable Row Level Security
ALTER TABLE original_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE persons ENABLE ROW LEVEL SECURITY;
ALTER TABLE face_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_results ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (you can modify these for authentication later)
CREATE POLICY "Allow public access to original_videos" ON original_videos FOR ALL USING (true);
CREATE POLICY "Allow public access to processing_sessions" ON processing_sessions FOR ALL USING (true);
CREATE POLICY "Allow public access to persons" ON persons FOR ALL USING (true);
CREATE POLICY "Allow public access to face_images" ON face_images FOR ALL USING (true);
CREATE POLICY "Allow public access to payment_results" ON payment_results FOR ALL USING (true);

-- Create storage bucket for video analysis files
INSERT INTO storage.buckets (id, name, public) 
VALUES ('video-analysis', 'video-analysis', true)
ON CONFLICT (id) DO NOTHING;

-- Create storage policies
CREATE POLICY "Allow public access to video-analysis bucket" ON storage.objects
FOR ALL USING (bucket_id = 'video-analysis');

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for processing_sessions table
CREATE TRIGGER update_processing_sessions_updated_at 
    BEFORE UPDATE ON processing_sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create view for easy session data retrieval
CREATE OR REPLACE VIEW session_summary AS
SELECT 
    ps.session_id,
    ps.workflow_mode,
    ps.status,
    ps.processing_started_at,
    ps.processing_completed_at,
    ov.video_filename,
    ov.file_size,
    ov.duration_seconds,
    COUNT(DISTINCT p.person_id) as total_persons,
    COUNT(DISTINCT CASE WHEN p.person_type = 'detected' THEN p.person_id END) as detected_persons,
    COUNT(DISTINCT CASE WHEN p.person_type = 'identified' THEN p.person_id END) as identified_persons,
    pr.total_payments,
    pr.cash_payments,
    pr.card_payments
FROM processing_sessions ps
LEFT JOIN original_videos ov ON ps.video_hash = ov.video_hash
LEFT JOIN persons p ON ps.session_id = p.session_id
LEFT JOIN payment_results pr ON ps.session_id = pr.session_id
GROUP BY ps.session_id, ps.workflow_mode, ps.status, ps.processing_started_at, ps.processing_completed_at,
         ov.video_filename, ov.file_size, ov.duration_seconds, pr.total_payments, pr.cash_payments, pr.card_payments; 