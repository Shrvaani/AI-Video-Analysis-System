-- Minimal Dual Table Schema - Only adds new tables
-- This works with existing database structure

-- Original videos table - stores the uploaded videos
CREATE TABLE IF NOT EXISTS original_videos (
    id SERIAL PRIMARY KEY,
    video_hash VARCHAR(64) UNIQUE NOT NULL,
    video_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    duration_seconds INTEGER,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Processed videos table - stores the processed videos with annotations
CREATE TABLE IF NOT EXISTS processed_videos (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    original_video_hash VARCHAR(64) NOT NULL,
    processed_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    processing_type VARCHAR(50) NOT NULL,
    processing_status VARCHAR(20) DEFAULT 'processing',
    processing_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for new tables
CREATE INDEX IF NOT EXISTS idx_original_videos_hash ON original_videos(video_hash);
CREATE INDEX IF NOT EXISTS idx_processed_videos_session_id ON processed_videos(session_id);
CREATE INDEX IF NOT EXISTS idx_processed_videos_original_hash ON processed_videos(original_video_hash);

-- Enable RLS on new tables
ALTER TABLE original_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_videos ENABLE ROW LEVEL SECURITY;

-- Create policies for new tables
CREATE POLICY "Allow public access to original_videos" ON original_videos FOR ALL USING (true);
CREATE POLICY "Allow public access to processed_videos" ON processed_videos FOR ALL USING (true);

-- Create storage bucket if it doesn't exist
INSERT INTO storage.buckets (id, name, public) 
VALUES ('video-analysis', 'video-analysis', true)
ON CONFLICT (id) DO NOTHING;

-- Create simple view for original videos
CREATE OR REPLACE VIEW original_videos_summary AS
SELECT 
    ov.video_hash,
    ov.video_filename,
    ov.file_size,
    ov.duration_seconds,
    ov.uploaded_at,
    COUNT(DISTINCT pv.session_id) as total_processed_videos
FROM original_videos ov
LEFT JOIN processed_videos pv ON ov.video_hash = pv.original_video_hash
GROUP BY ov.video_hash, ov.video_filename, ov.file_size, ov.duration_seconds, ov.uploaded_at; 