import streamlit as st
import os
import shutil
import uuid
import hashlib
import json

# Import Supabase manager
try:
    from supabase_config import supabase_manager
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    supabase_manager = None

# Check for required dependencies
missing_deps = []

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    missing_deps.append("opencv-python-headless")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    missing_deps.append("ultralytics")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    missing_deps.append("numpy")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    missing_deps.append("pandas")

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    missing_deps.append("plotly")

# Display missing dependencies warning
if missing_deps:
    st.warning(f"""
    **⚠️ Missing Dependencies Detected**
    
    The following packages are not available: {', '.join(missing_deps)}
    
    This may be due to installation issues on Streamlit Cloud. The app will run in limited mode.
    
    **To fix this:**
    1. Check that your requirements.txt includes: {', '.join(missing_deps)}
    2. Ensure packages.txt has the necessary system dependencies
    3. Try redeploying the application
    
    **Current Status:**
    - OpenCV: {'✅ Available' if CV2_AVAILABLE else '❌ Missing'}
    - YOLO: {'✅ Available' if YOLO_AVAILABLE else '❌ Missing'}
    - NumPy: {'✅ Available' if NUMPY_AVAILABLE else '❌ Missing'}
    - Pandas: {'✅ Available' if PANDAS_AVAILABLE else '❌ Missing'}
    - Plotly: {'✅ Available' if PLOTLY_AVAILABLE else '❌ Missing'}
    """)

# Only import the logic modules if all dependencies are available
if CV2_AVAILABLE and YOLO_AVAILABLE and NUMPY_AVAILABLE and PANDAS_AVAILABLE and PLOTLY_AVAILABLE:
    try:
        from detection_logic import detect_persons
        from identification_logic import identify_persons
        from payment_detection_logic import detect_payments
        ALL_MODULES_AVAILABLE = True
    except ImportError as e:
        ALL_MODULES_AVAILABLE = False
        st.error(f"""
        **Module import error: {str(e)}**
        
        Please check that all required files are present:
        - detection_logic.py
        - identification_logic.py
        - payment_detection_logic.py
        """)
else:
    ALL_MODULES_AVAILABLE = False
    # Create dummy functions for limited mode
    def detect_persons(*args, **kwargs):
        st.error("Video processing is not available due to missing dependencies.")
        st.info("Please check the dependency status above and redeploy the application.")
    
    def identify_persons(*args, **kwargs):
        st.error("Person identification is not available due to missing dependencies.")
        st.info("Please check the dependency status above and redeploy the application.")
    
    def detect_payments(*args, **kwargs):
        st.error("Payment detection is not available due to missing dependencies.")
        st.info("Please check the dependency status above and redeploy the application.")

# Custom CSS for modern styling
st.set_page_config(
    page_title="AI Video Analysis System",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    /* CSS Variables for theme support */
    :root {
        --background-color: #ffffff;
        --text-color: #262730;
        --card-background: #f8f9fa;
        --border-color: #e9ecef;
        --info-box-bg: #e3f2fd;
        --info-box-border: #2196f3;
    }
    
    /* Streamlit light mode (default) */
    .stApp {
        --background-color: #ffffff;
        --text-color: #262730;
        --card-background: #f8f9fa;
        --border-color: #e9ecef;
        --info-box-bg: #e3f2fd;
        --info-box-border: #2196f3;
    }
    
    /* Streamlit dark mode detection */
    .stApp[data-theme="dark"] {
        --background-color: #0e1117;
        --text-color: #fafafa;
        --card-background: #262730;
        --border-color: #464646;
        --info-box-bg: #1e3a5f;
        --info-box-border: #4fc3f7;
    }
    
    /* App container background - only for dark mode */
    .stApp[data-theme="dark"] [data-testid="stAppViewContainer"] {
        background-color: var(--background-color) !important;
    }
    
    /* Main content area - only for dark mode */
    .stApp[data-theme="dark"] .main .block-container {
        background-color: var(--background-color) !important;
    }
    
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        padding: 1.5rem 2rem !important;
        border-radius: 10px !important;
        margin-bottom: 1.5rem !important;
        color: white !important;
        text-align: center !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        max-height: 120px !important;
        overflow: hidden !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
    }
    
    .main-header h1 {
        margin: 0 !important;
        font-size: 2rem !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
        text-align: center !important;
        width: 100% !important;
    }
    
    .main-header p {
        margin: 0.3rem 0 0 0 !important;
        font-size: 1rem !important;
        opacity: 0.9 !important;
        line-height: 1.3 !important;
        text-align: center !important;
        width: 100% !important;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .session-card {
        background: var(--card-background);
        padding: 1.2rem !important;
        border-radius: 8px !important;
        border-left: 4px solid #667eea;
        margin: 0.6rem 0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: var(--text-color);
        max-width: 600px !important;
        font-size: 0.9rem !important;
        line-height: 1.4 !important;
    }
    
    .session-card h5 {
        margin: 0 0 0.6rem 0 !important;
        font-size: 0.95rem !important;
    }
    
    .session-card p {
        margin: 0.3rem 0 !important;
        font-size: 0.8rem !important;
        line-height: 1.3 !important;
    }
    
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: var(--card-background);
        margin: 1rem 0;
        color: var(--text-color);
    }
    
    .control-section {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid var(--border-color);
        color: var(--text-color);
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .danger-button {
        background: linear-gradient(90deg, #ff6b6b 0%, #ee5a24 100%) !important;
    }
    
    .success-button {
        background: linear-gradient(90deg, #00b894 0%, #00a085 100%) !important;
    }
    
    .info-box {
        background: var(--info-box-bg);
        border-left: 4px solid var(--info-box-border);
        padding: 0.75rem 1rem !important;
        border-radius: 5px;
        margin: 1rem 0 !important;
        color: var(--text-color);
        max-width: none !important;
        width: 100% !important;
        text-align: center !important;
        font-size: 0.9rem !important;
    }
    
    .info-box h4 {
        margin: 0 0 0.3rem 0 !important;
        font-size: 1rem !important;
    }
    
    .info-box p {
        margin: 0 !important;
        font-size: 0.85rem !important;
        line-height: 1.3 !important;
    }
    
    .progress-container {
        background: var(--card-background);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: var(--text-color);
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-active {
        background: #00b894;
        animation: pulse 2s infinite;
    }
    
    .status-inactive {
        background: #ddd;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* Dark mode specific overrides for Streamlit elements */
    .stApp[data-theme="dark"] .stAlert {
        background-color: var(--card-background) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--border-color) !important;
    }
    
    .stApp[data-theme="dark"] .stMarkdown {
        color: var(--text-color) !important;
    }
    
    .stApp[data-theme="dark"] .stText {
        color: var(--text-color) !important;
    }
    
    /* Ensure warning messages are visible in dark mode */
    .stApp[data-theme="dark"] .element-container .stAlert {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
        border: 1px solid #4a5568 !important;
    }
    
    .stApp[data-theme="dark"] .stAlert[data-baseweb="notification"] {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
    }
    
    /* Success and error message styling for dark mode */
    .stApp[data-theme="dark"] .stAlert[data-baseweb="notification"][data-severity="success"] {
        background-color: #22543d !important;
        color: #9ae6b4 !important;
        border: 1px solid #38a169 !important;
    }
    
    .stApp[data-theme="dark"] .stAlert[data-baseweb="notification"][data-severity="error"] {
        background-color: #742a2a !important;
        color: #feb2b2 !important;
        border: 1px solid #e53e3e !important;
    }
    
    .stApp[data-theme="dark"] .stAlert[data-baseweb="notification"][data-severity="warning"] {
        background-color: #744210 !important;
        color: #faf089 !important;
        border: 1px solid #d69e2e !important;
    }
    
    .stApp[data-theme="dark"] .stAlert[data-baseweb="notification"][data-severity="info"] {
        background-color: #2a4365 !important;
        color: #90cdf4 !important;
        border: 1px solid #3182ce !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper: Calculate video file hash
def calculate_video_hash(video_file):
    hasher = hashlib.md5()
    video_file.seek(0)  # Ensure file pointer is at the start
    while chunk := video_file.read(8192):
        hasher.update(chunk)
    video_file.seek(0)  # Reset file pointer for further use
    return hasher.hexdigest()

# Helper: Calculate video hash from file path
def calculate_video_hash_from_file(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
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

# Main Header
st.markdown("""
<div class="main-header">
    <h1>🎥 AI Video Analysis System</h1>
    <p>Advanced Person Detection, Re-Identification & Payment Analysis</p>
</div>
""", unsafe_allow_html=True)

# Supabase Status Indicator
if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
    st.success("☁️ **Cloud Storage**: Connected to Supabase - Data will be saved to cloud")
else:
    st.warning("💾 **Local Storage**: Using local file system - Data will be lost on app restart")

# Main content area with right sidebar
col1, spacer, col2 = st.columns([1, 0.1, 1])

with col2:
    # Main content area
    # Upload Section
    st.markdown("### Video Upload")
    video_file = st.file_uploader("Choose a video file", type=["mp4", "avi", "mov"], help="Upload CCTV footage for analysis")

    # Workflow status and current mode - displayed as a bar below upload section, only after video upload
    if video_file:
        if st.session_state.workflow_mode:
            st.markdown(f"""
            <div class="info-box">
                <h4>🎯 Current Workflow Mode</h4>
                <p><strong>{st.session_state.workflow_mode.replace('_', ' ').title() if st.session_state.workflow_mode else "Not Set"}</strong></p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="info-box">
                <h4>ℹ️ Select a Workflow Mode</h4>
                <p>Choose a workflow mode from the controls below to begin processing videos.</p>
            </div>
            """, unsafe_allow_html=True)

    # Store video file info for processing in the video interface section
    if video_file:
        # Check if this is a new video (different from the last uploaded video)
        current_video_hash = calculate_video_hash(video_file)
        last_video_hash = st.session_state.get('last_uploaded_video_hash')
        
        # If this is a new video, reset the workflow mode and clear processing state
        if last_video_hash != current_video_hash:
            st.session_state.workflow_mode = None
            if 'pending_processing' in st.session_state:
                del st.session_state.pending_processing
            if 'current_video_session' in st.session_state:
                del st.session_state.current_video_session
        
        # Store the current video hash for future comparison
        st.session_state.last_uploaded_video_hash = current_video_hash
        
        # Generate session ID and prepare video processing
        video_session_id = str(uuid.uuid4())[:8]
        video_session_dir = os.path.join(temp_dir, video_session_id)
        temp_video_path = os.path.join(video_session_dir, video_file.name)
        
        # Create directory and save video file
        try:
            # Ensure temp directory exists
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)
                st.info(f"📁 Created temp directory: {temp_dir}")
            
            # Create session directory
            os.makedirs(video_session_dir, exist_ok=True)
            st.info(f"📁 Created session directory: {video_session_dir}")
            
            # Check write permissions
            test_file = os.path.join(video_session_dir, "test.txt")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                st.error(f"❌ No write permission in directory {video_session_dir}: {e}")
                st.stop()
                
        except Exception as e:
            st.error(f"❌ Failed to create directory {video_session_dir}: {e}")
            st.stop()
        
        # Save video file locally
        try:
            video_content = video_file.read()
            with open(temp_video_path, "wb") as f:
                f.write(video_content)
            st.info(f"💾 Video content read: {len(video_content)} bytes")
        except Exception as e:
            st.error(f"❌ Failed to read or save video file: {e}")
            st.stop()
        
        # Verify the file was saved correctly
        if not os.path.exists(temp_video_path):
            st.error(f"❌ Failed to save video file to {temp_video_path}")
            st.stop()
        
        # Check file size
        file_size = os.path.getsize(temp_video_path)
        if file_size == 0:
            st.error(f"❌ Video file is empty: {temp_video_path}")
            st.stop()
        
        st.success(f"✅ Video saved successfully: {temp_video_path} ({file_size} bytes)")
        
        # Test if video can be opened
        import cv2
        test_cap = cv2.VideoCapture(temp_video_path)
        if not test_cap.isOpened():
            st.error(f"❌ Cannot open video file: {temp_video_path}")
            st.error("This might be due to unsupported video format or corrupted file.")
            st.stop()
        test_cap.release()
        
        # Save to Supabase if available (will be done after session is created)
        video_content_for_supabase = None
        if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
            try:
                # Reset file pointer to beginning and read content for later use
                video_file.seek(0)
                video_content_for_supabase = video_file.read()
            except Exception as e:
                st.warning(f"⚠️ Failed to prepare video for cloud storage: {e}")
            
        # Use the already calculated hash
        video_hash = current_video_hash
        st.session_state.uploaded_videos.append({
            "video_path": temp_video_path,
            "session_id": video_session_id,
            "hash": video_hash
        })
        
        # Save session data to Supabase if available (will be updated when workflow mode is selected)
        if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
            try:
                # Save with temporary workflow mode, will be updated later
                supabase_manager.save_session_data(
                    video_session_id, 
                    video_hash, 
                    'uploaded',  # Temporary status
                    video_file.name
                )
                
                # Now save video file after session is created
                if video_content_for_supabase:
                    if supabase_manager.save_video_file(video_session_id, video_file.name, video_content_for_supabase):
                        st.success("☁️ Video saved to cloud storage")
                    else:
                        st.warning("⚠️ Failed to save video to cloud storage, using local storage only")
            except Exception as e:
                st.warning(f"⚠️ Failed to save session data to cloud: {e}")
        
        # Store processing info for the video interface section
        st.session_state.pending_processing = {
            "video_session_id": video_session_id,
            "video_session_dir": video_session_dir,
            "temp_video_path": temp_video_path,
            "video_hash": video_hash
        }
        
        # Also set the current session ID immediately for session control display
        st.session_state.current_video_session = video_session_id

# Workflow Controls Section (Between First Part and Video Processing Interface)
st.markdown("---")  # Add a divider
st.markdown("### 🎯 Workflow Controls")

# Show workflow mode selection only after video upload
if video_file and not st.session_state.get('workflow_mode'):
    st.markdown("""
    <div class="info-box">
        <h4>ℹ️ Select a Workflow Mode</h4>
        <p>Choose a workflow mode from the controls below to begin processing videos.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Workflow Controls
    col_workflow1, col_workflow2 = st.columns(2)
    
    with col_workflow1:
        if st.button("🔍 Detect & Identify", use_container_width=True):
            st.session_state.workflow_mode = "detect_identify"
            # Update session in Supabase
            if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected() and 'pending_processing' in st.session_state:
                try:
                    supabase_manager.update_session_status(
                        st.session_state.pending_processing['video_session_id'], 
                        'detect_identify'
                    )
                except Exception as e:
                    st.warning(f"⚠️ Failed to update session status: {e}")
            st.success("✅ Switched to Detect & Identify mode")

    with col_workflow2:
        if st.button("💰 Detect, Identify & Payment", use_container_width=True):
            st.session_state.workflow_mode = "detect_identify_payment"
            # Update session in Supabase
            if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected() and 'pending_processing' in st.session_state:
                try:
                    supabase_manager.update_session_status(
                        st.session_state.pending_processing['video_session_id'], 
                        'detect_identify_payment'
                    )
                except Exception as e:
                    st.warning(f"⚠️ Failed to update session status: {e}")
            st.success("✅ Switched to Detect, Identify & Payment mode")

elif video_file and st.session_state.get('workflow_mode'):
    # Show current workflow mode with option to change
    st.markdown(f"""
    <div class="info-box">
        <h4>🎯 Current Workflow Mode</h4>
        <p><strong>{st.session_state.workflow_mode.replace('_', ' ').title()}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a button to change workflow mode for new video
    if st.button("🔄 Change Workflow Mode for New Video", use_container_width=True):
        st.session_state.workflow_mode = None
        st.success("🔄 Workflow mode reset. Please select a new mode.")
        st.rerun()
else:
    st.info("📤 Upload a video first to select a workflow mode.")


# Second Half - Video Processing Interface (No Columns)
st.markdown("---")  # Divider between halves
st.markdown("### 🎥 Video Processing Interface")

# Video processing interface - show when there's an active session or pending processing
if ('current_video_session' in st.session_state and st.session_state.get('workflow_mode')) or 'pending_processing' in st.session_state:
    
    # Handle pending processing first
    if 'pending_processing' in st.session_state and st.session_state.get('workflow_mode'):
        pending = st.session_state.pending_processing
        video_session_id = pending['video_session_id']
        video_session_dir = pending['video_session_dir']
        temp_video_path = pending['temp_video_path']
        video_hash = pending['video_hash']

        # Progress indicator
        with st.spinner("🔄 Initializing video processing..."):
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

        # Check if all required modules are available before processing
        if not ALL_MODULES_AVAILABLE:
            st.warning("""
            **⚠️ Running in Limited Mode**
            
            Some dependencies are missing, so video processing may not work properly.
            The app will attempt to run but may show error messages for unavailable features.
            """)
            # Decide workflow based on mode and video hash
            if st.session_state.workflow_mode == "detect_identify":
                # Check if we have existing data to identify against
                has_existing_data = video_hash in st.session_state.video_hashes.values() and len(existing_persons) > 0
                
                if has_existing_data:
                    st.markdown(f"""
                    <div class="session-card">
                        <h4>🔄 Identifying persons in Video Session {video_session_id}</h4>
                        <p><strong>File:</strong> {os.path.basename(temp_video_path)}</p>
                        <span class="status-indicator status-active"></span>Processing...
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state.current_video_session = video_session_id
                    identify_persons(st, base_faces_dir, temp_dir, video_session_dir, temp_video_path, video_session_id)
                else:
                    st.markdown(f"""
                    <div class="session-card">
                        <h4>🔍 Detecting persons in Video Session {video_session_id}</h4>
                        <p><strong>File:</strong> {os.path.basename(temp_video_path)}</p>
                        <span class="status-indicator status-active"></span>Processing...
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state.current_video_session = video_session_id
                    detect_persons(st, base_faces_dir, temp_dir, video_session_dir, temp_video_path, video_session_id)
                    st.session_state.video_hashes[video_session_id] = video_hash
                    save_video_hashes()
            elif st.session_state.workflow_mode == "detect_identify_payment":
                st.markdown(f"""
                <div class="session-card">
                    <h4>💰 Processing Video Session {video_session_id} (Detect, Identify & Payment)</h4>
                    <p><strong>File:</strong> {os.path.basename(temp_video_path)}</p>
                    <span class="status-indicator status-active"></span>Processing...
                </div>
                """, unsafe_allow_html=True)
                st.session_state.current_video_session = video_session_id
                
                # Check if we have existing data to identify against
                has_existing_data = video_hash in st.session_state.video_hashes.values() and len(existing_persons) > 0
                
                if has_existing_data:
                    identify_persons(st, base_faces_dir, temp_dir, video_session_dir, temp_video_path, video_session_id)
                else:
                    detect_persons(st, base_faces_dir, temp_dir, video_session_dir, temp_video_path, video_session_id)
                    st.session_state.video_hashes[video_session_id] = video_hash
                    save_video_hashes()
                detect_payments(st, temp_video_path, video_session_id)
        else:
            # All modules are available - process normally
            # Decide workflow based on mode and video hash
            if st.session_state.workflow_mode == "detect_identify":
                # Check if we have existing data to identify against
                has_existing_data = video_hash in st.session_state.video_hashes.values() and len(existing_persons) > 0
                
                if has_existing_data:
                    st.markdown(f"""
                    <div class="session-card">
                        <h4>🔄 Identifying persons in Video Session {video_session_id}</h4>
                        <p><strong>File:</strong> {os.path.basename(temp_video_path)}</p>
                        <span class="status-indicator status-active"></span>Processing...
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state.current_video_session = video_session_id
                    identify_persons(st, base_faces_dir, temp_dir, video_session_dir, temp_video_path, video_session_id)
                else:
                    st.markdown(f"""
                    <div class="session-card">
                        <h4>🔍 Detecting persons in Video Session {video_session_id}</h4>
                        <p><strong>File:</strong> {os.path.basename(temp_video_path)}</p>
                        <span class="status-indicator status-active"></span>Processing...
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state.current_video_session = video_session_id
                    detect_persons(st, base_faces_dir, temp_dir, video_session_dir, temp_video_path, video_session_id)
                    st.session_state.video_hashes[video_session_id] = video_hash
                    save_video_hashes()
            elif st.session_state.workflow_mode == "detect_identify_payment":
                st.markdown(f"""
                <div class="session-card">
                    <h4>💰 Processing Video Session {video_session_id} (Detect, Identify & Payment)</h4>
                    <p><strong>File:</strong> {os.path.basename(temp_video_path)}</p>
                    <span class="status-indicator status-active"></span>Processing...
                </div>
                """, unsafe_allow_html=True)
                st.session_state.current_video_session = video_session_id
                
                # Check if we have existing data to identify against
                has_existing_data = video_hash in st.session_state.video_hashes.values() and len(existing_persons) > 0
                
                if has_existing_data:
                    identify_persons(st, base_faces_dir, temp_dir, video_session_dir, temp_video_path, video_session_id)
                else:
                    detect_persons(st, base_faces_dir, temp_dir, video_session_dir, temp_video_path, video_session_id)
                    st.session_state.video_hashes[video_session_id] = video_hash
                    save_video_hashes()
                detect_payments(st, temp_video_path, video_session_id)

        # Clear pending processing
        del st.session_state.pending_processing
    
    # Continue with existing active session
    if 'current_video_session' in st.session_state and st.session_state.get('workflow_mode'):
        current_session_id = st.session_state.current_video_session
    
    # Video processing header
    if st.session_state.workflow_mode == "detect_identify":
        st.markdown("#### 🔍 Identify Mode")
        st.markdown("*Identifying persons based on previously detected data.*")
    elif st.session_state.workflow_mode == "detect_identify_payment":
        st.markdown("#### 💰 Detect, Identify & Payment Mode")
        st.markdown("*Processing video with person detection, identification, and payment analysis.*")
    
    # Video frame placeholder (this would be replaced with actual video processing)
    st.markdown("""
    <div style="background: #f0f0f0; padding: 2rem; border-radius: 10px; text-align: center; margin: 1rem 0;">
        <h4>🎬 Video Processing Interface</h4>
        <p><strong>Mode:</strong> {}</p>
    </div>
    """.format(st.session_state.workflow_mode.replace('_', ' ').title() if st.session_state.workflow_mode else "Not Set"), unsafe_allow_html=True)
    
    # Real-time statistics - only show when video is actively being processed
    if 'current_video_session' in st.session_state and st.session_state.get('workflow_mode'):
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        
        with col_stats1:
            st.metric("Total Unique Persons", "Processing...")
        
        with col_stats2:
            st.metric("Persons in Current Frame", "Processing...")
        
        with col_stats3:
            st.metric("Total Detections", "Processing...")
        
        # Summary statistics
        st.markdown("### 📊 Processing Summary")
        col_summary1, col_summary2, col_summary3 = st.columns(3)
        
        with col_summary1:
            st.markdown("**Unique Persons:** Processing...")
        
        with col_summary2:
            st.markdown("**Current Frame:** Processing...")
        
        with col_summary3:
            st.markdown("**Total Detections:** Processing...")
        
        # Session details - only show current session
        st.markdown("### 📋 Current Session Details")
        current_session_id = st.session_state.get('current_video_session')
        if current_session_id:
            # Count detected persons in current session
            detected_path = os.path.join(base_faces_dir, "Detected people", current_session_id)
            identified_path = os.path.join(base_faces_dir, "Identified people", current_session_id)
            detected_count = len([d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]) if os.path.exists(detected_path) else 0
            identified_count = len([d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]) if os.path.exists(identified_path) else 0
        
        st.markdown(f"""
                <div class="session-card">
                    <h5>📹 Current Session {current_session_id}</h5>
                    <p><strong>🔍 Detected:</strong> {detected_count} persons</p>
                    <p><strong>👤 Identified:</strong> {identified_count} persons</p>
                    <span class="status-indicator status-active"></span>Processing...
                </div>
                """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background: #f8f9fa; padding: 2rem; border-radius: 10px; text-align: center; margin: 1rem 0;">
        <h4>🎬 Video Processing Interface</h4>
        <p>Upload a video and select a workflow mode to start processing</p>
        <p>The video processing interface will appear here once you begin processing</p>
        </div>
        """, unsafe_allow_html=True)

# Third Half - Previously Processed Sessions (2 Columns, 10 Rows Grid)
st.markdown("---")  # Add a divider
st.markdown("### 📋 Previously Processed Sessions")

if os.path.exists(base_faces_dir):
    detected_sessions = [d for d in os.listdir(os.path.join(base_faces_dir, "Detected people")) if os.path.isdir(os.path.join(base_faces_dir, "Detected people", d))]
    identified_sessions = [d for d in os.listdir(os.path.join(base_faces_dir, "Identified people")) if os.path.isdir(os.path.join(base_faces_dir, "Identified people", d))]
    all_sessions = list(set(detected_sessions + identified_sessions))
    
    # Show total count near the heading
    if all_sessions:
        st.markdown(f"**Total Sessions:** {len(all_sessions)}")
        
        # Create a 2-column, 10-row grid layout
        for row in range(0, min(len(all_sessions), 20), 2):  # 20 sessions max (10 rows × 2 columns)
            col_left, col_right = st.columns(2)
            
            # Left column session
            if row < len(all_sessions):
                session_id = all_sessions[row]
                detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
                identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
                detected_count = len([d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]) if os.path.exists(detected_path) else 0
                identified_count = len([d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]) if os.path.exists(identified_path) else 0
                
                with col_left:
                    st.markdown(f"""
                    <div class="session-card">
                        <h5>📹 Session {session_id}</h5>
                        <p><strong>🔍 Detected:</strong> {detected_count} persons</p>
                        <p><strong>👤 Identified:</strong> {identified_count} persons</p>
                        <span class="status-indicator status-inactive"></span>Completed
                    </div>
                    """, unsafe_allow_html=True)
    
            # Right column session
            if row + 1 < len(all_sessions):
                session_id = all_sessions[row + 1]
                detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
                identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
                detected_count = len([d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]) if os.path.exists(detected_path) else 0
                identified_count = len([d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]) if os.path.exists(identified_path) else 0
                
                with col_right:
                    st.markdown(f"""
                    <div class="session-card">
                        <h5>📹 Session {session_id}</h5>
                        <p><strong>🔍 Detected:</strong> {detected_count} persons</p>
                        <p><strong>👤 Identified:</strong> {identified_count} persons</p>
                        <span class="status-indicator status-inactive"></span>Completed
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("📋 No previously processed sessions found.")
else:
    st.info("📋 No previously processed sessions found.")

# Fourth Half - Total Statistics Overview
st.markdown("---")  # Add a divider
st.markdown("### 📊 Total Statistics Overview")

# Calculate total statistics from existing session data
if os.path.exists(base_faces_dir):
    detected_sessions = [d for d in os.listdir(os.path.join(base_faces_dir, "Detected people")) if os.path.isdir(os.path.join(base_faces_dir, "Detected people", d))]
    identified_sessions = [d for d in os.listdir(os.path.join(base_faces_dir, "Identified people")) if os.path.isdir(os.path.join(base_faces_dir, "Identified people", d))]
    
    # Count processing sessions instead of person folders (consistent with table count logic)
    total_detected_sessions = len(detected_sessions)
    total_identified_sessions = len(identified_sessions)
    total_sessions = len(set(detected_sessions + identified_sessions))
    
    if total_detected_sessions > 0 or total_identified_sessions > 0:
        # Check if pandas and plotly are available for chart creation
        if PANDAS_AVAILABLE and PLOTLY_AVAILABLE:
            # Create data for pie chart
            chart_data = pd.DataFrame({
                'Category': ['Total Sessions', 'Detection Sessions', 'Identification Sessions'],
                'Count': [total_sessions, total_detected_sessions, total_identified_sessions]
            })
            
            # Create pie chart with count labels
            fig = px.pie(chart_data, values='Count', names='Category', 
                        title='Total Statistics Overview',
                        color_discrete_sequence=['#00b894', '#667eea', '#764ba2'])
            
            # Update the pie chart to show counts instead of percentages
            fig.update_traces(textinfo='label+value', textposition='inside')
            
            # Display pie chart
            st.plotly_chart(fig)
        else:
            # Fallback: display statistics as text
            st.markdown("### 📊 Statistics Summary")
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            with stat_col1:
                st.metric("Total Sessions", total_sessions)
            with stat_col2:
                st.metric("Detection Sessions", total_detected_sessions)
            with stat_col3:
                st.metric("Identification Sessions", total_identified_sessions)
    else:
        st.info("📊 No statistics available yet. Process some videos to see the overview.")
else:
    st.info("📊 No statistics available yet. Process some videos to see the overview.")

with col1:
    # Session Control Panel - moved to the far right
    st.markdown("### Session Control")
    
    # Session ID display - check for the actual video session ID
    current_session_id = st.session_state.get('current_video_session')
    pending_session_id = st.session_state.get('pending_processing', {}).get('video_session_id') if 'pending_processing' in st.session_state else None
    
    # Also check if we have a video file uploaded but not yet processed
    video_file = st.session_state.get('last_uploaded_video_hash')
    
    # Determine the active session ID with better logic
    if current_session_id:
        active_session_id = current_session_id
        session_status = "🟢 Active"
    elif pending_session_id:
        active_session_id = pending_session_id
        session_status = "⏳ Pending"
    elif video_file:
        # Get the latest uploaded video session ID
        if st.session_state.get('uploaded_videos'):
            latest_video = st.session_state.uploaded_videos[-1]
            active_session_id = latest_video.get('session_id', 'Unknown')
            session_status = "📤 Ready"
        else:
            active_session_id = "Video uploaded - select workflow mode"
            session_status = "📤 Ready"
    else:
        active_session_id = 'No active session'
        session_status = "⚪ Inactive"
    
    # Add a refresh button for session control
    if st.button("🔄 Refresh Session Status", key="refresh_session"):
        st.rerun()
    
    st.markdown(f"""
    <div style="background: var(--card-background); padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0; border: 1px solid var(--border-color);">
        <div style="font-size: 0.9rem; color: var(--text-color); margin-bottom: 0.5rem;"><strong>Session ID:</strong></div>
        <div style="background: #f0f0f0; padding: 0.5rem; border-radius: 5px; font-family: monospace; font-size: 0.8rem; color: #333;">{active_session_id}</div>
        <div style="font-size: 0.8rem; color: var(--text-color); margin-top: 0.3rem;">{session_status}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Debug information (can be removed later)
    if st.checkbox("🔧 Show Debug Info", key="debug_session"):
        st.write("**Debug Session State:**")
        st.write(f"- current_video_session: {st.session_state.get('current_video_session', 'None')}")
        st.write(f"- pending_processing: {st.session_state.get('pending_processing', 'None')}")
        st.write(f"- workflow_mode: {st.session_state.get('workflow_mode', 'None')}")
        st.write(f"- last_uploaded_video_hash: {st.session_state.get('last_uploaded_video_hash', 'None')}")
        st.write(f"- video_hashes: {list(st.session_state.get('video_hashes', {}).keys())}")
        st.write(f"- uploaded_videos: {st.session_state.get('uploaded_videos', [])}")
        st.write(f"- All session state keys: {list(st.session_state.keys())}")
        
        # Show the actual video session ID being used
        if st.session_state.get('uploaded_videos'):
            latest_video = st.session_state.uploaded_videos[-1]
            st.write(f"**Latest Video Session ID:** {latest_video.get('session_id', 'Unknown')}")
    
    # Clear All Data Button - full width
    if st.button("🗑️ Clear All Data", use_container_width=True, help="This will permanently delete all stored data (local and cloud)"):
        # Clear file system data
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
        
        # Clear Supabase data if available
        if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
            if supabase_manager.clear_all_data():
                st.success("🗑️ All data cleared (local + cloud storage)!")
            else:
                st.warning("⚠️ Local data cleared, but cloud data clearing failed")
                st.success("🗑️ Local data cleared!")
        else:
            st.success("🗑️ All local data cleared!")
        
        # Clear all session state
        st.session_state.clear()
        
        # Reinitialize session state
        st.session_state.uploaded_videos = []
        st.session_state.video_hashes = {}
        st.session_state.person_count = {}
        st.session_state.workflow_mode = None
        
        st.rerun()