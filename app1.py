import streamlit as st
import os
import shutil
import uuid
import hashlib
import json
from detection_logic import detect_persons
from identification_logic import identify_persons
from payment_detection_logic import detect_payments

# Helper: Calculate video file hash
def calculate_video_hash(video_file):
    hasher = hashlib.md5()
    video_file.seek(0)  # Ensure file pointer is at the start
    while chunk := video_file.read(8192):
        hasher.update(chunk)
    video_file.seek(0)  # Reset file pointer for further use
    return hasher.hexdigest()

# Setup folders and initialize session state globally
base_faces_dir = "known_faces"
temp_dir = "temp"
hash_file = "video_hashes.json"
os.makedirs(base_faces_dir, exist_ok=True)
os.makedirs(os.path.join(base_faces_dir, "Detected people"), exist_ok=True)
os.makedirs(os.path.join(base_faces_dir, "Identified people"), exist_ok=True)
os.makedirs(temp_dir, exist_ok=True)

# Load or initialize video_hashes from file
if 'video_hashes' not in st.session_state:
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            st.session_state.video_hashes = json.load(f)
    else:
        st.session_state.video_hashes = {}
if 'uploaded_videos' not in st.session_state:
    st.session_state.uploaded_videos = []
if 'person_count' not in st.session_state:
    st.session_state.person_count = {}
if 'workflow_mode' not in st.session_state:
    st.session_state.workflow_mode = None  # Options: 'detect_identify' or 'detect_identify_payment'

# Save video_hashes to file when updated
def save_video_hashes():
    with open(hash_file, 'w') as f:
        json.dump(st.session_state.video_hashes, f)

# Streamlit UI Setup
st.title("Enhanced Head Detection and Re-Identification System")
st.markdown("""
    A unified app for detecting and identifying persons in CCTV footage, with optional payment detection.
    Upload a video to process based on the selected mode.
    """)

# Sidebar with video upload and buttons
with st.sidebar:
    st.header("Video Upload")
    video_file = st.file_uploader("Upload CCTV Footage", type=["mp4", "avi", "mov"])
    
    if st.button("Clear All Data"):
        if os.path.exists(base_faces_dir):
            shutil.rmtree(base_faces_dir)
            os.makedirs(base_faces_dir, exist_ok=True)
            os.makedirs(os.path.join(base_faces_dir, "Detected people"), exist_ok=True)
            os.makedirs(os.path.join(base_faces_dir, "Identified people"), exist_ok=True)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)
        if os.path.exists(hash_file):
            os.remove(hash_file)
        st.session_state.clear()
        st.session_state.uploaded_videos = []
        st.session_state.video_hashes = {}
        st.session_state.person_count = {}
        st.session_state.workflow_mode = None
        st.success("All data and stored faces cleared!")

    if st.button("Detect & Identify"):
        st.session_state.workflow_mode = "detect_identify"
        st.success("Switched to Detect & Identify mode. Upload a video to proceed.")

    if st.button("Detect, Identify & Payment"):
        st.session_state.workflow_mode = "detect_identify_payment"
        st.success("Switched to Detect, Identify & Payment mode. Upload a video to proceed.")

# Automated workflow based on existing data
if video_file and 'current_video_session' not in st.session_state:
    video_session_id = str(uuid.uuid4())[:8]
    video_session_dir = os.path.join(temp_dir, video_session_id)
    os.makedirs(video_session_dir, exist_ok=True)
    temp_video_path = os.path.join(video_session_dir, video_file.name)
    with open(temp_video_path, "wb") as f:
        f.write(video_file.read())
    video_hash = calculate_video_hash(video_file)
    st.session_state.uploaded_videos.append({
        "video_path": temp_video_path,
        "session_id": video_session_id,
        "hash": video_hash
    })

    # Check existing data with stricter validation
    existing_detected_sessions = [d for d in os.listdir(os.path.join(base_faces_dir, "Detected people")) if os.path.isdir(os.path.join(base_faces_dir, "Detected people", d))]
    existing_identified_sessions = [d for d in os.listdir(os.path.join(base_faces_dir, "Identified people")) if os.path.isdir(os.path.join(base_faces_dir, "Identified people", d))]
    existing_sessions = set(existing_detected_sessions + existing_identified_sessions)
    existing_persons = set()
    for session_id in existing_sessions:
        detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
        identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
        if os.path.exists(detected_path):
            existing_persons.update([pid for pid in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, pid)) and os.path.exists(os.path.join(detected_path, pid, "first_detection.jpg"))])
        if os.path.exists(identified_path):
            existing_persons.update([pid for pid in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, pid)) and os.path.exists(os.path.join(identified_path, pid, "first_detection.jpg"))])
    st.write(f"Debug: Existing persons detected: {existing_persons}")  # Debug output

    # Decide workflow based on mode and video hash
    if st.session_state.workflow_mode == "detect_identify":
        if video_hash in st.session_state.video_hashes.values() and existing_persons:
            st.subheader(f"Identifying persons in Video Session {video_session_id}: {os.path.basename(temp_video_path)}")
            st.session_state.current_video_session = video_session_id
            identify_persons(st, base_faces_dir, temp_dir, video_session_dir, temp_video_path, video_session_id)
        else:
            st.subheader(f"Detecting persons in Video Session {video_session_id}: {os.path.basename(temp_video_path)}")
            st.session_state.current_video_session = video_session_id
            detect_persons(st, base_faces_dir, temp_dir, video_session_dir, temp_video_path, video_session_id)
            st.session_state.video_hashes[video_session_id] = video_hash
            save_video_hashes()
    elif st.session_state.workflow_mode == "detect_identify_payment":
        st.subheader(f"Processing Video Session {video_session_id}: {os.path.basename(temp_video_path)} (Detect, Identify & Payment)")
        st.session_state.current_video_session = video_session_id
        if video_hash in st.session_state.video_hashes.values() and existing_persons:
            identify_persons(st, base_faces_dir, temp_dir, video_session_dir, temp_video_path, video_session_id)
        else:
            detect_persons(st, base_faces_dir, temp_dir, video_session_dir, temp_video_path, video_session_id)
            st.session_state.video_hashes[video_session_id] = video_hash
            save_video_hashes()
        detect_payments(st, temp_video_path, video_session_id)

if 'current_video_session' in st.session_state:
    if st.button("Stop Current Video Processing", key=f"stop_button_{st.session_state.current_video_session}"):
        del st.session_state.current_video_session
        st.success("Video processing stopped. You can now upload a new video.")

if not st.session_state.uploaded_videos:
    if os.path.exists(base_faces_dir):
        detected_sessions = [d for d in os.listdir(os.path.join(base_faces_dir, "Detected people")) if os.path.isdir(os.path.join(base_faces_dir, "Detected people", d))]
        identified_sessions = [d for d in os.listdir(os.path.join(base_faces_dir, "Identified people")) if os.path.isdir(os.path.join(base_faces_dir, "Identified people", d))]
        if detected_sessions or identified_sessions:
            st.subheader("Previously Processed Video Sessions")
            for session_id in set(detected_sessions + identified_sessions):
                detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
                identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
                detected_count = len([d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]) if os.path.exists(detected_path) else 0
                identified_count = len([d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]) if os.path.exists(identified_path) else 0
                st.write(f"**Session {session_id}**: {detected_count} detected, {identified_count} identified")