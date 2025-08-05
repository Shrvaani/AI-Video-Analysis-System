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

    def get_person_session_count(self, person_id):
        """Get the number of unique video sessions where a person appears"""
        if not self.is_connected():
            return 0
        
        try:
            # Get all sessions where this person appears
            result = self.client.table('persons').select('session_id').eq('person_id', person_id).execute()
            
            # Get unique video hashes for these sessions
            unique_video_hashes = set()
            for person_data in result.data:
                session_id = person_data['session_id']
                # Get video hash for this session
                session_result = self.client.table('sessions').select('video_hash').eq('session_id', session_id).execute()
                if session_result.data:
                    unique_video_hashes.add(session_result.data[0]['video_hash'])
            
            return len(unique_video_hashes)
        except Exception as e:
            st.error(f"Error getting person session count: {e}")
            return 0

    def clear_all_data(self):
        """Clear all data from Supabase database and storage"""
        if not self.is_connected():
            return False
        
        try:
            # First, let's check what data exists
            sessions_result = self.client.table('sessions').select('*').execute()
            st.info(f"🗑️ Current sessions in DB: {len(sessions_result.data)}")
            
            persons_result = self.client.table('persons').select('*').execute()
            st.info(f"🗑️ Current persons in DB: {len(persons_result.data)}")
            
            # Get all session IDs first
            session_ids = [session['session_id'] for session in sessions_result.data]
            
            st.info(f"🗑️ Found {len(session_ids)} sessions to clear: {session_ids}")
            
            if not session_ids:
                st.info("🗑️ No sessions to clear")
                return True
            
            # Delete data for each session (this avoids foreign key constraint issues)
            for session_id in session_ids:
                st.info(f"🗑️ Clearing session: {session_id}")
                
                # Delete face images
                face_result = self.client.table('face_images').delete().eq('session_id', session_id).execute()
                st.info(f"🗑️ Deleted {len(face_result.data) if face_result.data else 0} face images")
                
                # Delete persons
                person_result = self.client.table('persons').delete().eq('session_id', session_id).execute()
                st.info(f"🗑️ Deleted {len(person_result.data) if person_result.data else 0} persons")
                
                # Delete videos
                video_result = self.client.table('videos').delete().eq('session_id', session_id).execute()
                st.info(f"🗑️ Deleted {len(video_result.data) if video_result.data else 0} videos")
                
                # Delete payment results
                payment_result = self.client.table('payment_results').delete().eq('session_id', session_id).execute()
                st.info(f"🗑️ Deleted {len(payment_result.data) if payment_result.data else 0} payment results")
            
            # Finally delete all sessions
            session_delete_result = self.client.table('sessions').delete().execute()
            st.info(f"🗑️ Deleted {len(session_delete_result.data) if session_delete_result.data else 0} sessions")
            
            # Verify deletion
            verify_sessions = self.client.table('sessions').select('*').execute()
            st.info(f"🗑️ Sessions after deletion: {len(verify_sessions.data)}")
            
            # Clear storage bucket
            try:
                self.client.storage.from_('video-analysis').remove([])
                st.info("🗑️ Cleared storage bucket")
            except Exception as storage_error:
                st.warning(f"⚠️ Storage clearing failed: {storage_error}")
            
            return True
        except Exception as e:
            st.error(f"Error clearing Supabase data: {e}")
            return False

# Global Supabase manager instance
supabase_manager = SupabaseManager() 