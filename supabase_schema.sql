-- Supabase Database Schema for AI Video Analysis System

-- Enable Row Level Security (RLS)
ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret';

-- Sessions table - stores video processing sessions
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    video_hash VARCHAR(64) NOT NULL,
    workflow_mode VARCHAR(50) NOT NULL,
    video_filename VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'processing',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Persons table - stores detected and identified persons
CREATE TABLE IF NOT EXISTS persons (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    person_id VARCHAR(50) NOT NULL,
    person_type VARCHAR(20) NOT NULL, -- 'detected' or 'identified'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Face images table - stores metadata for face images
CREATE TABLE IF NOT EXISTS face_images (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    person_id VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- 'first_detection', 'frame_*'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Videos table - stores video file metadata with processing information
CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    video_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    video_hash VARCHAR(64) NOT NULL,  -- For duplicate detection
    workflow_mode VARCHAR(50) NOT NULL,  -- What was processed: 'detect_identify', 'payment_only'
    processing_status VARCHAR(20) DEFAULT 'uploaded',  -- uploaded, processing, completed, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Payment results table - stores payment detection results
CREATE TABLE IF NOT EXISTS payment_results (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    total_payments INTEGER DEFAULT 0,
    cash_payments INTEGER DEFAULT 0,
    card_payments INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_video_hash ON sessions(video_hash);
CREATE INDEX IF NOT EXISTS idx_persons_session_id ON persons(session_id);
CREATE INDEX IF NOT EXISTS idx_face_images_session_person ON face_images(session_id, person_id);
CREATE INDEX IF NOT EXISTS idx_videos_session_id ON videos(session_id);
CREATE INDEX IF NOT EXISTS idx_payment_results_session_id ON payment_results(session_id);

-- Enable Row Level Security
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE persons ENABLE ROW LEVEL SECURITY;
ALTER TABLE face_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_results ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (you can modify these for authentication later)
CREATE POLICY "Allow public access to sessions" ON sessions FOR ALL USING (true);
CREATE POLICY "Allow public access to persons" ON persons FOR ALL USING (true);
CREATE POLICY "Allow public access to face_images" ON face_images FOR ALL USING (true);
CREATE POLICY "Allow public access to videos" ON videos FOR ALL USING (true);
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

-- Create trigger for sessions table
CREATE TRIGGER update_sessions_updated_at 
    BEFORE UPDATE ON sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for videos table
CREATE TRIGGER update_videos_updated_at 
    BEFORE UPDATE ON videos 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column(); 