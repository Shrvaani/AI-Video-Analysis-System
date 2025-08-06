import os
import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import cv2
import numpy as np

class ImprovedSupabaseManager:
    def __init__(self):
        self.client: Client = None
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if self.supabase_url and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                # Test connection
                self.client.table('original_videos').select('id').limit(1).execute()
            except Exception as e:
                st.warning(f"⚠️ Supabase connection failed: {e}")
                self.client = None

    def is_connected(self):
        """Check if Supabase connection is available"""
        return self.client is not None

    def save_original_video(self, video_hash, video_filename, video_data):
        """Save original video to Supabase storage and database"""
        if not self.is_connected():
            return False
        
        try:
            # Check if video already exists
            existing = self.client.table('original_videos').select('video_hash').eq('video_hash', video_hash).execute()
            if existing.data:
                return True  # Video already exists, no need to save again
            
            file_path = f"original_videos/{video_hash}/{video_filename}"
            
            # Upload to Supabase storage
            self.client.storage.from_('video-analysis').upload(
                path=file_path,
                file=video_data,
                file_options={"content-type": "video/mp4"}
            )
            
            # Get file size
            file_size = len(video_data)
            
            # Try to get video duration
            duration_seconds = None
            try:
                # Create temporary file to get duration
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                    temp_file.write(video_data)
                    temp_file.flush()
                    cap = cv2.VideoCapture(temp_file.name)
                    if cap.isOpened():
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                        if fps > 0 and frame_count > 0:
                            duration_seconds = int(frame_count / fps)
                    cap.release()
                os.unlink(temp_file.name)
            except:
                pass  # Duration extraction is optional
            
            # Save video metadata to database
            video_data = {
                'video_hash': video_hash,
                'video_filename': video_filename,
                'file_path': file_path,
                'file_size': file_size,
                'duration_seconds': duration_seconds,
                'created_at': datetime.now().isoformat()
            }
            
            self.client.table('original_videos').insert(video_data).execute()
            return True
        except Exception as e:
            st.error(f"Error saving original video: {e}")
            return False

    def create_processing_session(self, session_id, video_hash, workflow_mode):
        """Create a new processing session"""
        if not self.is_connected():
            return False
        
        try:
            session_data = {
                'session_id': session_id,
                'video_hash': video_hash,
                'workflow_mode': workflow_mode,
                'status': 'processing',
                'processing_started_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            self.client.table('processing_sessions').insert(session_data).execute()
            return True
        except Exception as e:
            st.error(f"Error creating processing session: {e}")
            return False

    def update_session_status(self, session_id, status):
        """Update processing session status"""
        if not self.is_connected():
            return False
        
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if status == 'completed':
                update_data['processing_completed_at'] = datetime.now().isoformat()
            
            self.client.table('processing_sessions').update(update_data).eq('session_id', session_id).execute()
            return True
        except Exception as e:
            st.error(f"Error updating session status: {e}")
            return False

    def save_person_data(self, session_id, person_id, person_type="detected"):
        """Save person data to database"""
        if not self.is_connected():
            return False
        
        try:
            person_data = {
                'session_id': session_id,
                'person_id': person_id,
                'person_type': person_type,
                'created_at': datetime.now().isoformat()
            }
            
            self.client.table('persons').insert(person_data).execute()
            return True
        except Exception as e:
            st.error(f"Error saving person data: {e}")
            return False

    def save_face_image(self, session_id, person_id, image_data, image_type="first_detection"):
        """Save face image to Supabase storage and database"""
        if not self.is_connected():
            return False
        
        try:
            # Convert numpy array to bytes if needed
            if isinstance(image_data, np.ndarray):
                success, buffer = cv2.imencode('.jpg', image_data)
                if not success:
                    return False
                image_bytes = buffer.tobytes()
            else:
                image_bytes = image_data
            
            file_path = f"face_images/{session_id}/{person_id}/{image_type}.jpg"
            
            # Upload to Supabase storage
            self.client.storage.from_('video-analysis').upload(
                path=file_path,
                file=image_bytes,
                file_options={"content-type": "image/jpeg"}
            )
            
            # Save metadata to database
            image_metadata = {
                'session_id': session_id,
                'person_id': person_id,
                'file_path': file_path,
                'file_type': image_type,
                'created_at': datetime.now().isoformat()
            }
            
            self.client.table('face_images').insert(image_metadata).execute()
            return True
        except Exception as e:
            st.error(f"Error saving face image: {e}")
            return False

    def save_payment_results(self, session_id, payment_data):
        """Save payment detection results"""
        if not self.is_connected():
            return False
        
        try:
            data = {
                'session_id': session_id,
                'total_payments': payment_data.get('total_payments', 0),
                'cash_payments': payment_data.get('cash_payments', 0),
                'card_payments': payment_data.get('card_payments', 0),
                'created_at': datetime.now().isoformat()
            }
            
            self.client.table('payment_results').insert(data).execute()
            return True
        except Exception as e:
            st.error(f"Error saving payment results: {e}")
            return False

    def get_session_summary(self, session_id):
        """Get complete session summary using the view"""
        if not self.is_connected():
            return None
        
        try:
            result = self.client.table('session_summary').select('*').eq('session_id', session_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"Error getting session summary: {e}")
            return None

    def get_all_sessions(self):
        """Get all processing sessions with video information"""
        if not self.is_connected():
            return []
        
        try:
            result = self.client.table('session_summary').select('*').order('processing_started_at', desc=True).execute()
            return result.data
        except Exception as e:
            st.error(f"Error getting sessions: {e}")
            return []

    def get_original_video_by_hash(self, video_hash):
        """Get original video information by hash"""
        if not self.is_connected():
            return None
        
        try:
            result = self.client.table('original_videos').select('*').eq('video_hash', video_hash).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"Error getting original video: {e}")
            return None

    def get_persons_by_session(self, session_id):
        """Get all persons for a session"""
        if not self.is_connected():
            return []
        
        # Add retry logic for temporary resource unavailability
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                result = self.client.table('persons').select('*').eq('session_id', session_id).execute()
                return result.data
            except Exception as e:
                if "Resource temporarily unavailable" in str(e) and attempt < max_retries - 1:
                    # Wait before retrying
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    st.error(f"Error getting persons: {e}")
                    return []
        return []

    def clear_all_data(self):
        """Clear all data from Supabase database and storage"""
        if not self.is_connected():
            return False
        
        try:
            # Clear all tables
            self.client.table('payment_results').delete().neq('id', 0).execute()
            self.client.table('face_images').delete().neq('id', 0).execute()
            self.client.table('persons').delete().neq('id', 0).execute()
            self.client.table('processing_sessions').delete().neq('id', 0).execute()
            self.client.table('original_videos').delete().neq('id', 0).execute()
            
            # Clear storage bucket
            try:
                self.client.storage.from_('video-analysis').remove([])
            except:
                pass  # Ignore storage errors
            
            return True
        except Exception as e:
            st.error(f"Error clearing Supabase data: {e}")
            return False

# Global improved Supabase manager instance
improved_supabase_manager = ImprovedSupabaseManager() 