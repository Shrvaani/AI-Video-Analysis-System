import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import json
import uuid
from datetime import datetime
import base64
from PIL import Image
import io

# Load environment variables
load_dotenv()

class SupabaseManager:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            st.error("""
            **Supabase configuration missing!**
            
            Please set the following environment variables:
            - SUPABASE_URL: Your Supabase project URL
            - SUPABASE_ANON_KEY: Your Supabase anonymous key
            
            You can get these from your Supabase project dashboard.
            """)
            self.client = None
        else:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                st.success("✅ Connected to Supabase successfully!")
            except Exception as e:
                st.error(f"❌ Failed to connect to Supabase: {e}")
                self.client = None

    def is_connected(self):
        return self.client is not None

    def save_session_data(self, session_id, video_hash, workflow_mode, video_filename):
        """Save session metadata to database"""
        if not self.is_connected():
            return False
        
        try:
            data = {
                'session_id': session_id,
                'video_hash': video_hash,
                'workflow_mode': workflow_mode,
                'video_filename': video_filename,
                'created_at': datetime.now().isoformat(),
                'status': 'processing'
            }
            
            result = self.client.table('sessions').insert(data).execute()
            return True
        except Exception as e:
            st.error(f"Error saving session data: {e}")
            return False

    def update_session_status(self, session_id, workflow_mode):
        """Update session workflow mode"""
        if not self.is_connected():
            return False
        
        try:
            self.client.table('sessions').update({
                'workflow_mode': workflow_mode,
                'status': 'processing',
                'updated_at': datetime.now().isoformat()
            }).eq('session_id', session_id).execute()
            return True
        except Exception as e:
            st.error(f"Error updating session status: {e}")
            return False

    def save_person_data(self, session_id, person_id, person_type="detected"):
        """Save person detection/identification data"""
        if not self.is_connected():
            return False
        
        try:
            data = {
                'session_id': session_id,
                'person_id': person_id,
                'person_type': person_type,  # 'detected' or 'identified'
                'created_at': datetime.now().isoformat()
            }
            
            self.client.table('persons').insert(data).execute()
            return True
        except Exception as e:
            st.error(f"Error saving person data: {e}")
            return False

    def save_face_image(self, session_id, person_id, image_data, image_type="first_detection"):
        """Save face image to Supabase storage"""
        if not self.is_connected():
            return False
        
        try:
            # Convert image data to bytes
            img_byte_arr = None
            
            # Handle different image data types
            if hasattr(image_data, 'save'):  # PIL Image
                img_byte_arr = io.BytesIO()
                image_data.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
            elif hasattr(image_data, 'tobytes'):  # NumPy array
                # Convert BGR to RGB and encode as JPEG
                import cv2
                success, encoded_image = cv2.imencode('.jpg', image_data)
                if success:
                    img_byte_arr = encoded_image.tobytes()
                else:
                    st.error("Failed to encode NumPy array as JPEG")
                    return False
            elif isinstance(image_data, (str, bytes)):  # File path or bytes
                img_byte_arr = image_data
            else:
                st.error(f"Unsupported image data type: {type(image_data)}")
                return False
            
            # Create file path
            file_path = f"faces/{session_id}/{person_id}/{image_type}.jpg"
            
            # Upload to Supabase storage
            self.client.storage.from_('video-analysis').upload(
                path=file_path,
                file=img_byte_arr,
                file_options={"content-type": "image/jpeg"}
            )
            
            # Save file metadata to database
            file_data = {
                'session_id': session_id,
                'person_id': person_id,
                'file_path': file_path,
                'file_type': image_type,
                'created_at': datetime.now().isoformat()
            }
            
            self.client.table('face_images').insert(file_data).execute()
            return True
        except Exception as e:
            st.error(f"Error saving face image: {e}")
            return False

    def save_video_file(self, session_id, video_filename, video_data):
        """Save video file to Supabase storage"""
        if not self.is_connected():
            return False
        
        try:
            file_path = f"videos/{session_id}/{video_filename}"
            
            # Upload to Supabase storage
            self.client.storage.from_('video-analysis').upload(
                path=file_path,
                file=video_data,
                file_options={"content-type": "video/mp4"}
            )
            
            # Save video metadata to database
            video_metadata = {
                'session_id': session_id,
                'video_filename': video_filename,
                'file_path': file_path,
                'created_at': datetime.now().isoformat()
            }
            
            self.client.table('videos').insert(video_metadata).execute()
            return True
        except Exception as e:
            st.error(f"Error saving video file: {e}")
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
            
            # Remove any fields that don't exist in the database schema
            # The payment_results table only has: session_id, total_payments, cash_payments, card_payments, created_at
            
            result = self.client.table('payment_results').insert(data).execute()
            return True
        except Exception as e:
            st.error(f"Error saving payment results: {e}")
            return False

    def get_session_data(self, session_id):
        """Get session data from database"""
        if not self.is_connected():
            return None
        
        # Add retry logic for temporary resource unavailability
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                result = self.client.table('sessions').select('*').eq('session_id', session_id).execute()
                return result.data[0] if result.data else None
            except Exception as e:
                if "Resource temporarily unavailable" in str(e) and attempt < max_retries - 1:
                    # Wait before retrying
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    st.error(f"Error getting session data: {e}")
                    return None

    def get_all_sessions(self):
        """Get all sessions from database"""
        if not self.is_connected():
            return []
        
        try:
            result = self.client.table('sessions').select('*').order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            st.error(f"Error getting sessions: {e}")
            return []

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

    def get_face_images_by_person(self, session_id, person_id):
        """Get all face images for a person"""
        if not self.is_connected():
            return []
        
        # Add retry logic for temporary resource unavailability
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                result = self.client.table('face_images').select('*').eq('session_id', session_id).eq('person_id', person_id).execute()
                return result.data
            except Exception as e:
                if "Resource temporarily unavailable" in str(e) and attempt < max_retries - 1:
                    # Wait before retrying
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    st.error(f"Error getting face images: {e}")
                    return []

    def get_payment_results(self, session_id):
        """Get payment results for a session"""
        if not self.is_connected():
            return None
        
        try:
            result = self.client.table('payment_results').select('*').eq('session_id', session_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"Error getting payment results: {e}")
            return None

    def get_all_payment_results(self):
        """Get all payment results"""
        if not self.is_connected():
            return []
        
        try:
            result = self.client.table('payment_results').select('*').order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            st.error(f"Error getting payment results: {e}")
            return []

    def clear_all_data(self):
        """Clear all data from Supabase database and storage"""
        if not self.is_connected():
            return False
        
        try:
            # Clear all tables
            self.client.table('sessions').delete().neq('id', 0).execute()
            self.client.table('persons').delete().neq('id', 0).execute()
            self.client.table('face_images').delete().neq('id', 0).execute()
            self.client.table('videos').delete().neq('id', 0).execute()
            self.client.table('payment_results').delete().neq('id', 0).execute()
            
            # Clear storage bucket
            try:
                self.client.storage.from_('video-analysis').remove([])
            except:
                pass  # Ignore storage errors
            
            return True
        except Exception as e:
            st.error(f"Error clearing Supabase data: {e}")
            return False

# Global Supabase manager instance
supabase_manager = SupabaseManager() 