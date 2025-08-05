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

    def update_session_status(self, session_id, status):
        """Update session status"""
        if not self.is_connected():
            return False
        
        try:
            self.client.table('sessions').update({
                'status': status,
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
            # Convert image data to bytes if it's a PIL Image
            if hasattr(image_data, 'save'):
                img_byte_arr = io.BytesIO()
                image_data.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
            else:
                img_byte_arr = image_data
            
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
            video_data = {
                'session_id': session_id,
                'video_filename': video_filename,
                'file_path': file_path,
                'created_at': datetime.now().isoformat()
            }
            
            self.client.table('videos').insert(video_data).execute()
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
            
            self.client.table('payment_results').insert(data).execute()
            return True
        except Exception as e:
            st.error(f"Error saving payment results: {e}")
            return False

    def get_session_data(self, session_id):
        """Get session data from database"""
        if not self.is_connected():
            return None
        
        try:
            result = self.client.table('sessions').select('*').eq('session_id', session_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
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
        
        try:
            result = self.client.table('persons').select('*').eq('session_id', session_id).execute()
            return result.data
        except Exception as e:
            st.error(f"Error getting persons: {e}")
            return []

    def get_face_images_by_person(self, session_id, person_id):
        """Get all face images for a person"""
        if not self.is_connected():
            return []
        
        try:
            result = self.client.table('face_images').select('*').eq('session_id', session_id).eq('person_id', person_id).execute()
            return result.data
        except Exception as e:
            st.error(f"Error getting face images: {e}")
            return []

# Global Supabase manager instance
supabase_manager = SupabaseManager() 