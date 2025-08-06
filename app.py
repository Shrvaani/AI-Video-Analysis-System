import streamlit as st
import os
import shutil
import uuid
import hashlib
import json
import time

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

# Helper function to safely list directory contents with retry logic
def safe_listdir(directory_path, max_retries=3):
    """Safely list directory contents with retry logic for resource unavailability errors"""
    for attempt in range(max_retries):
        try:
            if os.path.exists(directory_path):
                return os.listdir(directory_path)
            else:
                return []
        except OSError as e:
            if e.errno == 11 and attempt < max_retries - 1:  # Resource temporarily unavailable
                import time
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                continue
            else:
                st.warning(f"Warning: Could not access directory {directory_path}: {e}")
                return []
    return []

# Helper function to safely check if directory exists and has contents
def safe_directory_has_contents(directory_path, max_retries=3):
    """Safely check if directory exists and has contents with retry logic"""
    for attempt in range(max_retries):
        try:
            if os.path.exists(directory_path):
                contents = os.listdir(directory_path)
                return len([d for d in contents if os.path.isdir(os.path.join(directory_path, d))]) > 0
            else:
                return False
        except OSError as e:
            if e.errno == 11 and attempt < max_retries - 1:  # Resource temporarily unavailable
                import time
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                continue
            else:
                st.warning(f"Warning: Could not access directory {directory_path}: {e}")
                return False
    return False

# Setup folders and initialize session state globally
base_faces_dir = "known_faces"
temp_dir = "temp"
hash_file = "video_hashes.json"
os.makedirs(base_faces_dir, exist_ok=True)
os.makedirs(os.path.join(base_faces_dir, "Detected people"), exist_ok=True)
os.makedirs(os.path.join(base_faces_dir, "Identified people"), exist_ok=True)
os.makedirs(temp_dir, exist_ok=True)

# Initialize session state variables
if 'uploaded_videos' not in st.session_state:
    st.session_state.uploaded_videos = []
if 'person_count' not in st.session_state:
    st.session_state.person_count = {}
if 'video_hashes' not in st.session_state:
    st.session_state.video_hashes = {}
if 'workflow_mode' not in st.session_state:
    st.session_state.workflow_mode = "detect_identify"
if 'stop_processing' not in st.session_state:
    st.session_state.stop_processing = False

# Define processing state functions first
def save_processing_state(video_session_id, workflow_mode, video_path, progress=0):
    """Save processing state to persistent storage"""
    processing_state = {
        'video_session_id': video_session_id,
        'workflow_mode': workflow_mode,
        'video_path': video_path,
        'progress': progress,
        'timestamp': time.time(),
        'status': 'processing'
    }
    
    # Save to Supabase if available
    if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
        try:
            supabase_manager.save_processing_state(processing_state)
        except Exception as e:
            st.warning(f"⚠️ Could not save processing state to cloud: {e}")
    
    # Also save locally as backup
    state_file = os.path.join(temp_dir, f"processing_state_{video_session_id}.json")
    try:
        with open(state_file, 'w') as f:
            json.dump(processing_state, f)
    except Exception as e:
        st.warning(f"⚠️ Could not save processing state locally: {e}")

def load_processing_state(video_session_id):
    """Load processing state from persistent storage"""
    # Try to load from Supabase first
    if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
        try:
            state = supabase_manager.get_processing_state(video_session_id)
            if state:
                return state
        except Exception as e:
            st.warning(f"⚠️ Could not load processing state from cloud: {e}")
    
    # Fallback to local file
    state_file = os.path.join(temp_dir, f"processing_state_{video_session_id}.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"⚠️ Could not load processing state from local file: {e}")
    
    return None

def clear_processing_state(video_session_id):
    """Clear processing state from persistent storage"""
    # Clear from Supabase
    if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
        try:
            supabase_manager.clear_processing_state(video_session_id)
        except Exception as e:
            st.warning(f"⚠️ Could not clear processing state from cloud: {e}")
    
    # Clear local file
    state_file = os.path.join(temp_dir, f"processing_state_{video_session_id}.json")
    if os.path.exists(state_file):
        try:
            os.remove(state_file)
        except Exception as e:
            st.warning(f"⚠️ Could not clear local processing state: {e}")

def check_for_interrupted_processing():
    """Check if there's any interrupted processing that can be resumed"""
    # Check for any processing state files
    if os.path.exists(temp_dir):
        state_files = [f for f in os.listdir(temp_dir) if f.startswith('processing_state_') and f.endswith('.json')]
        for state_file in state_files:
            try:
                with open(os.path.join(temp_dir, state_file), 'r') as f:
                    state = json.load(f)
                
                # Check if processing was recent (within last 10 minutes)
                if time.time() - state.get('timestamp', 0) < 600:  # 10 minutes
                    return state
            except Exception as e:
                st.warning(f"⚠️ Could not read processing state file {state_file}: {e}")
    
    return None

# Check for interrupted processing on every page load
interrupted_state = check_for_interrupted_processing()
if interrupted_state:
    st.session_state.pending_processing = interrupted_state
    st.session_state.workflow_mode = interrupted_state.get('workflow_mode')
    st.session_state.current_video_session = interrupted_state.get('video_session_id')
    st.success(f"🔄 **Automatically resuming interrupted processing** for session {interrupted_state.get('video_session_id')}")
    st.info("The video processing will continue from where it left off.")

# Load or initialize video_hashes from file
if 'video_hashes' not in st.session_state:
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            st.session_state.video_hashes = json.load(f)
    else:
        st.session_state.video_hashes = {}
# Always try to load existing sessions from Supabase on every page load
if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
    try:
        all_sessions = supabase_manager.get_all_sessions()
        if all_sessions:
            # Only load sessions that have actually been processed (have person or payment data)
            processed_sessions = []
            for session in all_sessions:
                session_id = session['session_id']
                has_processed_data = False
                
                # Check if this session has actual processed data
                try:
                    persons_data = supabase_manager.get_persons_by_session(session_id)
                    payment_data = supabase_manager.get_payment_results(session_id)
                    
                    # Consider processed if there are persons OR payment data
                    if (persons_data and len(persons_data) > 0) or payment_data:
                        has_processed_data = True
                except Exception:
                    pass
                
                # Also check local file system as backup
                if not has_processed_data:
                    detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
                    identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
                    if os.path.exists(detected_path) and len([d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]) > 0:
                        has_processed_data = True
                    elif os.path.exists(identified_path) and len([d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]) > 0:
                        has_processed_data = True
                
                # Only include sessions that have actually been processed
                if has_processed_data:
                    processed_sessions.append(session)
            
            # Convert processed sessions to uploaded_videos format
            uploaded_videos = []
            for session in processed_sessions:
                uploaded_videos.append({
                    "video_path": f"supabase_session_{session['session_id']}",  # Placeholder path
                    "session_id": session['session_id'],
                    "hash": session['video_hash'],
                    "workflow_mode": session.get('workflow_mode', 'unknown'),
                    "created_at": session.get('created_at', 'unknown')
                })
            st.session_state.uploaded_videos = uploaded_videos
            
            # Also update video_hashes to include the processed sessions
            for session in processed_sessions:
                st.session_state.video_hashes[session['session_id']] = session['video_hash']
            
            # Show notification only if this is a fresh load (not already loaded)
            if 'data_loaded_notification' not in st.session_state:
                st.session_state.data_loaded_notification = True
                st.success(f"📊 Automatically loaded {len(uploaded_videos)} processed sessions from cloud storage")
        else:
            st.session_state.uploaded_videos = []
    except Exception as e:
        st.warning(f"⚠️ Failed to load existing sessions from cloud: {e}")
        if 'uploaded_videos' not in st.session_state:
            st.session_state.uploaded_videos = []
else:
    if 'uploaded_videos' not in st.session_state:
        st.session_state.uploaded_videos = []
    if 'person_count' not in st.session_state:
        st.session_state.person_count = {}
    if 'workflow_mode' not in st.session_state:
        st.session_state.workflow_mode = None  # Options: 'detect_identify' or 'payment_only'
    if 'stop_processing' not in st.session_state:
        st.session_state.stop_processing = False

# Save video_hashes to file when updated
def save_video_hashes():
    with open(hash_file, 'w') as f:
        json.dump(st.session_state.video_hashes, f)

# Function to check if we should force detection mode
def should_force_detection():
    return len(st.session_state.get('video_hashes', {})) == 0

# Function to comprehensively check session data
def check_session_data():
    """Comprehensive session data check for debugging"""
    st.subheader("🔍 Session Data Analysis")
    
    # Check current session state
    st.write("**Current Session State:**")
    st.write(f"- uploaded_videos count: {len(st.session_state.get('uploaded_videos', []))}")
    st.write(f"- video_hashes count: {len(st.session_state.get('video_hashes', {}))}")
    st.write(f"- workflow_mode: {st.session_state.get('workflow_mode', 'None')}")
    
    # Check Supabase data
    if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
        st.write("**Supabase Data:**")
        try:
            all_sessions = supabase_manager.get_all_sessions()
            st.write(f"- Total sessions in database: {len(all_sessions)}")
            
            if all_sessions:
                st.write("**Session Details:**")
                for i, session in enumerate(all_sessions):
                    session_id = session.get('session_id', 'Unknown')
                    workflow_mode = session.get('workflow_mode', 'unknown')
                    video_hash = session.get('video_hash', 'unknown')
                    created_at = session.get('created_at', 'unknown')
                    
                    st.write(f"**Session {i+1}: {session_id}**")
                    st.write(f"  - Workflow Mode: {workflow_mode}")
                    st.write(f"  - Video Hash: {video_hash}")
                    st.write(f"  - Created At: {created_at}")
                    
                    # Check person data
                    try:
                        persons_data = supabase_manager.get_persons_by_session(session_id)
                        detected_count = len([p for p in persons_data if p.get('detection_type') == 'detected'])
                        identified_count = len([p for p in persons_data if p.get('detection_type') == 'identified'])
                        st.write(f"  - Persons Data: {len(persons_data)} total")
                        st.write(f"  - Detected: {detected_count}")
                        st.write(f"  - Identified: {identified_count}")
                    except Exception as e:
                        st.write(f"  - Error getting persons data: {e}")
                    
                    # Check payment data
                    try:
                        payment_data = supabase_manager.get_payment_results(session_id)
                        if payment_data:
                            st.write(f"  - Payment Data: {payment_data}")
                        else:
                            st.write(f"  - Payment Data: None")
                    except Exception as e:
                        st.write(f"  - Error getting payment data: {e}")
                    
                    st.write("---")
        except Exception as e:
            st.error(f"Error accessing Supabase: {e}")
    else:
        st.write("**Supabase:** Not available")
    
    # Check local file system
    st.write("**Local File System:**")
    detected_path = os.path.join(base_faces_dir, "Detected people")
    identified_path = os.path.join(base_faces_dir, "Identified people")
    
    if os.path.exists(detected_path):
        detected_sessions = [d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]
        st.write(f"- Detected sessions: {len(detected_sessions)}")
        for session_id in detected_sessions:
            session_path = os.path.join(detected_path, session_id)
            person_count = len([d for d in os.listdir(session_path) if os.path.isdir(os.path.join(session_path, d))])
            st.write(f"  - Session {session_id}: {person_count} persons")
    else:
        st.write("- Detected people directory: Does not exist")
    
    if os.path.exists(identified_path):
        identified_sessions = [d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]
        st.write(f"- Identified sessions: {len(identified_sessions)}")
        for session_id in identified_sessions:
            session_path = os.path.join(identified_path, session_id)
            person_count = len([d for d in os.listdir(session_path) if os.path.isdir(os.path.join(session_path, d))])
            st.write(f"  - Session {session_id}: {person_count} persons")
    else:
        st.write("- Identified people directory: Does not exist")
    
    # Check processed videos
    st.write("**Processed Videos Analysis:**")
    processed_videos = get_processed_videos()
    st.write(f"- Processed videos count: {len(processed_videos)}")
    
    if processed_videos:
        for i, video_info in enumerate(processed_videos):
            session_id = video_info.get('session_id', 'Unknown')
            workflow_mode = video_info.get('workflow_mode', 'unknown')
            video_hash = video_info.get('hash', 'unknown')
            
            st.write(f"**Processed Video {i+1}: {session_id}**")
            st.write(f"  - Workflow Mode: {workflow_mode}")
            st.write(f"  - Video Hash: {video_hash}")
            st.write(f"  - Full Info: {video_info}")

# Function to get processed videos
def get_processed_videos():
    uploaded_videos = st.session_state.get('uploaded_videos', [])
    processed_videos = []
    
    for video_info in uploaded_videos:
        session_id = video_info.get('session_id')
        if session_id:
            # Check if this session has been processed by looking for data
            has_processed_data = False
            
            if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
                try:
                    # Check if there's any data in Supabase for this session
                    persons_data = supabase_manager.get_persons_by_session(session_id)
                    payment_data = supabase_manager.get_payment_results(session_id)
                    
                    # Consider processed if there are persons OR payment data
                    if (persons_data and len(persons_data) > 0) or payment_data:
                        has_processed_data = True
                except Exception:
                    pass
            
            # Fallback to local file system check
            if not has_processed_data:
                detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
                identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
                if os.path.exists(detected_path) and len([d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]) > 0:
                    has_processed_data = True
                elif os.path.exists(identified_path) and len([d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]) > 0:
                    has_processed_data = True
            
            # Only consider it processed if we actually found data
            # Remove the fallback that considered all uploaded videos as processed
            if has_processed_data:
                processed_videos.append(video_info)
    
    return processed_videos

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
    
    # Debug: Show database connection and data status
    if st.checkbox("🔧 Show Database Debug Info", key="debug_db"):
        st.subheader("🔍 Database Debug Information")
        
        # Check sessions table
        try:
            all_sessions = supabase_manager.get_all_sessions()
            st.write(f"**Sessions in database:** {len(all_sessions)}")
            if all_sessions:
                st.write("**Session IDs:**")
                for session in all_sessions:
                    st.write(f"- {session.get('session_id', 'Unknown')} (Mode: {session.get('workflow_mode', 'Unknown')})")
            else:
                st.write("❌ No sessions found in database")
        except Exception as e:
            st.error(f"❌ Error getting sessions: {e}")
        
        # Check persons table
        try:
            if all_sessions:
                total_persons = 0
                for session in all_sessions:
                    persons = supabase_manager.get_persons_by_session(session['session_id'])
                    total_persons += len(persons)
                st.write(f"**Total persons in database:** {total_persons}")
            else:
                st.write("**Total persons in database:** 0 (no sessions)")
        except Exception as e:
            st.error(f"❌ Error getting persons: {e}")
        
        # Check payment results
        try:
            payment_results = supabase_manager.get_all_payment_results()
            st.write(f"**Payment results in database:** {len(payment_results)}")
        except Exception as e:
            st.error(f"❌ Error getting payment results: {e}")
        
        # Show session state
        st.write("**Current session state:**")
        st.write(f"- uploaded_videos: {len(st.session_state.get('uploaded_videos', []))}")
        st.write(f"- video_hashes: {len(st.session_state.get('video_hashes', {}))}")
        st.write(f"- workflow_mode: {st.session_state.get('workflow_mode', 'None')}")
        
        # Show processed videos
        processed_videos = get_processed_videos()
        st.write(f"**Processed videos:** {len(processed_videos)}")
        if processed_videos:
            for video in processed_videos:
                st.write(f"- {video.get('session_id', 'Unknown')}")
else:
    st.warning("💾 **Local Storage**: Using local file system - Data will be lost on app restart")

# Data is now automatically loaded on every page refresh
# Debug info is available below if needed

# Main content area with right sidebar
col1, spacer, col2 = st.columns([1, 0.1, 1])

with col1:
    # Main content area
    # Upload Section
    st.markdown("### Video Upload")
    video_file = st.file_uploader("Choose a video file", type=["mp4", "avi", "mov"], help="Upload CCTV footage for analysis")

    # Workflow status and current mode - displayed as a bar below upload section, only after video upload
    if video_file:
        pass  # Removed the workflow mode selection info box

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
        
        # Set the current video session immediately when video is uploaded
        st.session_state.current_video_session = video_session_id
        
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

# Workflow Controls Section (Between First Part and Video Processing Interface)
st.markdown("---")  # Add a divider
st.markdown("### 🎯 Workflow Controls")

# Show workflow mode selection only after video upload
if video_file and not st.session_state.get('workflow_mode'):
    # Removed the workflow mode selection info box
    
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
        if st.button("💳 Payment Only", use_container_width=True):
            st.session_state.workflow_mode = "payment_only"
            # Update session in Supabase
            if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected() and 'pending_processing' in st.session_state:
                try:
                    supabase_manager.update_session_status(
                        st.session_state.pending_processing['video_session_id'], 
                        'payment_only'
                    )
                except Exception as e:
                    st.warning(f"⚠️ Failed to update session status: {e}")
            st.success("✅ Switched to Payment Only mode")

elif video_file and st.session_state.get('workflow_mode'):
    # Add a button to change workflow mode for new video
    if st.button("🔄 Change Workflow Mode for New Video", use_container_width=True):
        st.session_state.workflow_mode = None
        st.success("🔄 Workflow mode reset. Please select a new mode.")
        st.rerun()
else:
    # Removed the info message about uploading a video first
    pass

# Add Session Controls to col2 (right column)
with col2:
    # Session Control Panel - positioned near video upload
    st.markdown("### Session Control")
    
    # Session ID display - check for the actual video session ID
    current_session_id = st.session_state.get('current_video_session')
    pending_session_id = st.session_state.get('pending_processing', {}).get('video_session_id') if 'pending_processing' in st.session_state else None
    
    # Also check if we have a video file uploaded but not yet processed
    video_file = st.session_state.get('last_uploaded_video_hash')
    
    # Determine the active session ID - prioritize processing session ID
    if 'pending_processing' in st.session_state and st.session_state.get('workflow_mode'):
        # When processing, ALWAYS use the exact session ID from pending_processing
        active_session_id = st.session_state.pending_processing['video_session_id']
        session_status = "🟢 Processing"
    elif current_session_id:
        active_session_id = current_session_id
        session_status = "🟢 Active"
    elif st.session_state.get('current_video_session'):
        # Use the current video session ID (set when processing starts)
        active_session_id = st.session_state.current_video_session
        session_status = "🟢 Processing"
    elif video_file and st.session_state.get('uploaded_videos'):
        # Get the latest uploaded video session ID
        latest_video = st.session_state.uploaded_videos[-1]
        active_session_id = latest_video.get('session_id', 'Unknown')
        session_status = "📤 Ready"
    elif video_file:
        # Video uploaded but not yet added to uploaded_videos list
        active_session_id = "Video uploaded - select workflow mode"
        session_status = "📤 Ready"
    else:
        active_session_id = 'No active session'
        session_status = "⚪ Inactive"
    
    # Show status if we have a video but no session ID displayed
    if video_file and active_session_id == 'No active session':
        st.info("🔄 Video uploaded - select workflow mode to start processing")
    
    # Additional check: if we have uploaded videos, show the latest session ID
    if st.session_state.get('uploaded_videos') and active_session_id == 'No active session':
        latest_video = st.session_state.uploaded_videos[-1]
        if latest_video.get('session_id'):
            active_session_id = latest_video['session_id']
            session_status = "📤 Ready"
    
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
        
        # Show what session ID the session controls are using
        st.write(f"**Session Controls Active Session ID:** {active_session_id}")
        st.write(f"**Session Controls Status:** {session_status}")
        
        # Show what session ID video processing is using
        if 'pending_processing' in st.session_state:
            st.write(f"**Video Processing Session ID:** {st.session_state.pending_processing.get('video_session_id', 'None')}")
        else:
            st.write("**Video Processing Session ID:** No pending processing")
    
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
        supabase_cleared = False
        if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
            try:
                st.info("🗑️ Clearing cloud data...")
                if supabase_manager.clear_all_data():
                    supabase_cleared = True
                    st.success("🗑️ All data cleared (local + cloud storage)!")
                else:
                    st.warning("⚠️ Local data cleared, but cloud data clearing failed")
                    st.success("🗑️ Local data cleared!")
            except Exception as e:
                st.error(f"❌ Error clearing cloud data: {e}")
                st.success("🗑️ Local data cleared!")
        else:
            st.success("🗑️ All local data cleared!")
        
        # Clear all session state completely
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Reinitialize session state with clean values
        st.session_state.uploaded_videos = []
        st.session_state.video_hashes = {}
        st.session_state.person_count = {}
        st.session_state.workflow_mode = None
        st.session_state.last_uploaded_video_hash = None
        st.session_state.force_detection = True  # Force detection mode after clearing
        st.session_state.current_video_session = None
        st.session_state.pending_processing = {}
        st.session_state.stop_processing = False
        
        # Force clear the hash file as well
        if os.path.exists(hash_file):
            try:
                os.remove(hash_file)
            except:
                pass
        
        # Force reload the video hashes to ensure they're cleared
        st.session_state.video_hashes = {}
        
        st.rerun()


# Second Half - Video Processing (No Columns)
st.markdown("---")  # Divider between halves

# Video processing interface - show when there's an active session or pending processing
if ('current_video_session' in st.session_state and st.session_state.get('workflow_mode')) or 'pending_processing' in st.session_state:
    
    # Handle pending processing first
    if 'pending_processing' in st.session_state and st.session_state.get('workflow_mode'):
        # Force detection mode if no video hashes exist (fresh start after clear)
        if len(st.session_state.get('video_hashes', {})) == 0:
            st.session_state.force_detection = True
        pending = st.session_state.pending_processing
        video_session_id = pending['video_session_id']
        video_session_dir = pending['video_session_dir']
        temp_video_path = pending['temp_video_path']
        video_hash = pending['video_hash']

        # Progress indicator
        with st.spinner("🔄 Initializing video processing..."):
            # Force detection mode if no existing data
            if len(st.session_state.video_hashes) == 0:
                st.session_state.force_detection = True
            else:
                st.session_state.force_detection = False
            
            # Override workflow mode to force detection if needed (but not if payment_only is selected)
            if st.session_state.get('force_detection', False) and st.session_state.get('workflow_mode') != "payment_only":
                st.session_state.workflow_mode = "detect_identify"
            # Check existing data with stricter validation using safe file operations
            detected_people_dir = os.path.join(base_faces_dir, "Detected people")
            identified_people_dir = os.path.join(base_faces_dir, "Identified people")
            
            existing_detected_sessions = [d for d in safe_listdir(detected_people_dir) if os.path.isdir(os.path.join(detected_people_dir, d))]
            existing_identified_sessions = [d for d in safe_listdir(identified_people_dir) if os.path.isdir(os.path.join(identified_people_dir, d))]
            existing_sessions = set(existing_detected_sessions + existing_identified_sessions)
            existing_persons = set()
            
            for session_id in existing_sessions:
                detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
                identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
                
                if os.path.exists(detected_path):
                    person_dirs = safe_listdir(detected_path)
                    for pid in person_dirs:
                        person_path = os.path.join(detected_path, pid)
                        if os.path.isdir(person_path) and os.path.exists(os.path.join(person_path, "first_detection.jpg")):
                            existing_persons.add(pid)
                
                if os.path.exists(identified_path):
                    person_dirs = safe_listdir(identified_path)
                    for pid in person_dirs:
                        person_path = os.path.join(identified_path, pid)
                        if os.path.isdir(person_path) and os.path.exists(os.path.join(person_path, "first_detection.jpg")):
                            existing_persons.add(pid)
            
            # Debug: Show what we found (commented out for production)
            # st.write(f"**Debug - Existing Data Check:**")
            # st.write(f"- Existing detected sessions: {len(existing_detected_sessions)}")
            # st.write(f"- Existing identified sessions: {len(existing_identified_sessions)}")
            # st.write(f"- Existing persons: {len(existing_persons)}")
            # st.write(f"- Video hashes in session: {len(st.session_state.video_hashes)}")
            # st.write(f"- Current video hash: {video_hash}")

        # Check if all required modules are available before processing
        if not ALL_MODULES_AVAILABLE:
            st.warning("""
            Some dependencies are missing, so video processing may not work properly.
            The app will attempt to run but may show error messages for unavailable features.
            """)
        # Decide workflow based on mode and video hash
        st.write(f"🔍 DEBUG: Processing with workflow_mode: {st.session_state.workflow_mode}")
        if st.session_state.workflow_mode == "detect_identify":
            # Check if we have existing data to identify against
            # Fix: Check if this specific video hash has been processed before
            has_existing_data = False
            
            # Check if this exact video hash exists in our processed videos
            if video_hash in st.session_state.video_hashes.values():
                # This video has been processed before, check if we have person data
                has_existing_data = len(existing_persons) > 0
            else:
                # This is a new video, should always go to detection
                has_existing_data = False
            
            st.write(f"🔍 DEBUG: Video hash: {video_hash}")
            st.write(f"🔍 DEBUG: Existing persons: {len(existing_persons)}")
            st.write(f"🔍 DEBUG: Video hash in processed: {video_hash in st.session_state.video_hashes.values()}")
            st.write(f"🔍 DEBUG: Has existing data: {has_existing_data}")
            
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
                # Only save video hash AFTER successful processing
                # st.session_state.video_hashes[video_session_id] = video_hash
                # save_video_hashes()
        elif st.session_state.workflow_mode == "payment_only":
            st.markdown(f"""
            <div class="session-card">
                    <h4>💳 Payment Detection in Video Session {video_session_id}</h4>
                <p><strong>File:</strong> {os.path.basename(temp_video_path)}</p>
                <span class="status-indicator status-active"></span>Processing...
            </div>
            """, unsafe_allow_html=True)
            st.session_state.current_video_session = video_session_id
            # Save processing state before starting payment detection
            save_processing_state(video_session_id, st.session_state.workflow_mode, temp_video_path, 0)
            detect_payments(st, temp_video_path, video_session_id)
        else:
            # All modules are available - process normally
            # Decide workflow based on mode and video hash
            if st.session_state.workflow_mode == "detect_identify":
                # Check if we have existing data to identify against
                # Fix: Check if this specific video hash has been processed before
                has_existing_data = False
                
                # Check if this exact video hash exists in our processed videos
                if video_hash in st.session_state.video_hashes.values():
                    # This video has been processed before, check if we have person data
                    has_existing_data = len(existing_persons) > 0
                else:
                    # This is a new video, should always go to detection
                    has_existing_data = False
                
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
                    # Only save video hash AFTER successful processing
                    # st.session_state.video_hashes[video_session_id] = video_hash
                    # save_video_hashes()
            elif st.session_state.workflow_mode == "payment_only":
                st.markdown(f"""
                <div class="session-card">
                    <h4>💳 Payment Detection in Video Session {video_session_id}</h4>
                    <p><strong>File:</strong> {os.path.basename(temp_video_path)}</p>
                    <span class="status-indicator status-active"></span>Processing...
                </div>
                """, unsafe_allow_html=True)
                st.session_state.current_video_session = video_session_id
                detect_payments(st, temp_video_path, video_session_id)

        # Clear pending processing
        del st.session_state.pending_processing
        # Reset session controls update flag
        if 'session_controls_updated' in st.session_state:
            del st.session_state.session_controls_updated
    
    # Continue with existing active session
    if 'current_video_session' in st.session_state and st.session_state.get('workflow_mode'):
        current_session_id = st.session_state.current_video_session
    
    # Video processing - workflow mode is handled in the logic modules
    
    # Video processing interface - actual processing happens in the logic modules
    

    
    # Real-time statistics - only show when video is actively being processed
    if 'current_video_session' in st.session_state and st.session_state.get('workflow_mode'):
        if st.session_state.workflow_mode == "detect_identify":
            # Show person detection/identification metrics
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
            
    elif st.session_state.workflow_mode == "payment_only":
        # Show payment detection metrics
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        
        with col_stats1:
            st.metric("Cash Payments", "Processing...")
        
        with col_stats2:
            st.metric("Card Payments", "Processing...")
        
        with col_stats3:
            st.metric("Total Payments", "Processing...")
        
        # Summary statistics
        st.markdown("### 💳 Payment Detection Summary")
        col_summary1, col_summary2, col_summary3 = st.columns(3)
        
        with col_summary1:
            st.markdown("**Cash Payments:** Processing...")
        
        with col_summary2:
            st.markdown("**Card Payments:** Processing...")
        
        with col_summary3:
            st.markdown("**Total Payments:** Processing...")
        
        # Session details for payment mode
        st.markdown("### 📋 Payment Session Details")
        current_session_id = st.session_state.get('current_video_session')
        
        st.markdown(f"""
        <div class="session-card">
            <h5>💳 Payment Session {current_session_id}</h5>
            <p><strong>💰 Cash Payments:</strong> Processing...</p>
            <p><strong>💳 Card Payments:</strong> Processing...</p>
            <span class="status-indicator status-active"></span>Processing...
        </div>
        """, unsafe_allow_html=True)
else:
    # No active processing - show minimal interface
    pass

# Third Half - Previously Processed Sessions (2 Columns, 10 Rows Grid)
st.markdown("---")  # Add a divider
st.markdown("### 📋 Previously Processed Sessions")

# Add refresh button for session data
col_refresh1, col_refresh2, col_refresh3 = st.columns([1, 1, 2])
with col_refresh1:
    if st.button("🔄 Refresh Session Data", help="Reload session data from cloud storage"):
        if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
            try:
                all_sessions = supabase_manager.get_all_sessions()
                if all_sessions:
                    # Only load sessions that have actually been processed
                    processed_sessions = []
                    for session in all_sessions:
                        session_id = session['session_id']
                        has_processed_data = False
                        
                        # Check if this session has actual processed data
                        try:
                            persons_data = supabase_manager.get_persons_by_session(session_id)
                            payment_data = supabase_manager.get_payment_results(session_id)
                            
                            # Consider processed if there are persons OR payment data
                            if (persons_data and len(persons_data) > 0) or payment_data:
                                has_processed_data = True
                        except Exception:
                            pass
                        
                        # Also check local file system as backup
                        if not has_processed_data:
                            detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
                            identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
                            if os.path.exists(detected_path) and len([d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]) > 0:
                                has_processed_data = True
                            elif os.path.exists(identified_path) and len([d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]) > 0:
                                has_processed_data = True
                        
                        # Only include sessions that have actually been processed
                        if has_processed_data:
                            processed_sessions.append(session)
                    
                    # Convert processed sessions to uploaded_videos format
                    uploaded_videos = []
                    for session in processed_sessions:
                        uploaded_videos.append({
                            "video_path": f"supabase_session_{session['session_id']}",
                            "session_id": session['session_id'],
                            "hash": session['video_hash'],
                            "workflow_mode": session.get('workflow_mode', 'unknown'),
                            "created_at": session.get('created_at', 'unknown')
                        })
                    st.session_state.uploaded_videos = uploaded_videos
                    
                    # Update video_hashes
                    for session in processed_sessions:
                        st.session_state.video_hashes[session['session_id']] = session['video_hash']
                    
                    st.success(f"✅ Refreshed {len(uploaded_videos)} processed sessions from cloud storage")
                    st.rerun()
                else:
                    st.info("📋 No processed sessions found in cloud storage")
            except Exception as e:
                st.error(f"❌ Failed to refresh session data: {e}")
        else:
            st.warning("⚠️ Cloud storage not available")

with col_refresh2:
    if st.button("🔍 Check Session Data", help="Run comprehensive session data analysis"):
        check_session_data()

# Use the shared function to get processed videos
processed_videos = get_processed_videos()

if processed_videos:
    st.markdown(f"**Total Processed Sessions:** {len(processed_videos)}")
    
    # Temporary debug section to help identify the issue
    if st.checkbox("🔧 Show Session Debug Info", key="session_debug"):
        st.write("**Session Debug Information:**")
        for i, video_info in enumerate(processed_videos):
            session_id = video_info.get('session_id', 'Unknown')
            workflow_mode = video_info.get('workflow_mode', 'unknown')
            st.write(f"**Session {i+1}: {session_id}**")
            st.write(f"- Workflow Mode: {workflow_mode}")
            st.write(f"- Video Info: {video_info}")
            
            # Check Supabase data
            if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
                try:
                    persons_data = supabase_manager.get_persons_by_session(session_id)
                    payment_data = supabase_manager.get_payment_results(session_id)
                    st.write(f"- Persons Data: {len(persons_data) if persons_data else 0}")
                    st.write(f"- Payment Data: {payment_data}")
                except Exception as e:
                    st.write(f"- Error getting data: {e}")
    
    # Create a 2-column, 10-row grid layout
    for row in range(0, min(len(processed_videos), 20), 2):  # 20 sessions max (10 rows × 2 columns)
        col_left, col_right = st.columns(2)
        
        # Left column session
        if row < len(processed_videos):
            video_info = processed_videos[row]
            session_id = video_info.get('session_id', 'Unknown')
            video_name = video_info.get('video_path', 'Unknown').split('/')[-1] if video_info.get('video_path') else 'Unknown'
            workflow_mode = video_info.get('workflow_mode', 'unknown')
            
            # Get person counts from Supabase if available, otherwise from local files
            detected_count = 0
            identified_count = 0
            payment_count = 0
            
            if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
                try:
                    # Get person counts from Supabase
                    persons_data = supabase_manager.get_persons_by_session(session_id)
                    # Fix: Count all persons in the session, not just by detection_type
                    detected_count = len(persons_data) if persons_data else 0
                    identified_count = 0  # Will be updated if we have identification data
                    
                    # Get payment data
                    payment_data = supabase_manager.get_payment_results(session_id)
                    if payment_data:
                        payment_count = payment_data.get('total_payments', 0)
                except Exception as e:
                    # Fallback to local file system
                    detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
                    identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
                    detected_count = len([d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]) if os.path.exists(detected_path) else 0
                    identified_count = len([d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]) if os.path.exists(identified_path) else 0
            else:
                # Use local file system
                detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
                identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
                detected_count = len([d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]) if os.path.exists(detected_path) else 0
                identified_count = len([d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]) if os.path.exists(identified_path) else 0
            
            # Determine session type based on workflow mode and data
            session_type = "Unknown"
            
            # Debug: Log the workflow mode for troubleshooting
            if workflow_mode == "unknown" or workflow_mode is None:
                # Try to determine workflow mode from the data
                if payment_count > 0:
                    session_type = "Payment Detection"
                elif detected_count > 0 or identified_count > 0:
                    session_type = "Person Detection & Identification"
                else:
                    # Check if this session has any data at all
                    has_any_data = False
                    if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
                        try:
                            persons_data = supabase_manager.get_persons_by_session(session_id)
                            payment_data = supabase_manager.get_payment_results(session_id)
                            if (persons_data and len(persons_data) > 0) or payment_data:
                                has_any_data = True
                        except:
                            pass
                    
                    if has_any_data:
                        session_type = "Detection & Identification"
                    else:
                        session_type = "Incomplete Processing"
            elif workflow_mode == "payment_only":
                session_type = "Payment Detection"
            elif workflow_mode == "detect_identify":
                if detected_count > 0 and identified_count == 0:
                    session_type = "Person Detection"
                elif identified_count > 0 and detected_count == 0:
                    session_type = "Person Identification"
                elif detected_count > 0 and identified_count > 0:
                    session_type = "Mixed Detection & Identification"
                elif detected_count == 0 and identified_count == 0:
                    # Check if this session was actually processed but found no persons
                    session_type = "Detection (No Persons Found)"
                else:
                    session_type = "Detection & Identification"
            else:
                # Unknown workflow mode, try to determine from data
                if payment_count > 0:
                    session_type = "Payment Detection"
                elif detected_count > 0 or identified_count > 0:
                    session_type = "Person Detection & Identification"
                else:
                    session_type = "Incomplete Processing"

            with col_left:
                st.markdown(f"""
                <div class="session-card">
                    <h5>📹 Session {session_id}</h5>
                    <p><strong>📁 Type:</strong> {session_type}</p>
                    <p><strong>🔍 Detected:</strong> {detected_count} persons</p>
                    <p><strong>👤 Identified:</strong> {identified_count} persons</p>
                    {f'<p><strong>💳 Payments:</strong> {payment_count}</p>' if payment_count > 0 else ''}
                    <div style="display: flex; align-items: center; margin-top: 0.5rem;">
                        <span class="status-indicator status-inactive"></span>
                        <span style="margin-left: 0.5rem;">Completed</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
        # Right column session
        if row + 1 < len(processed_videos):
            video_info = processed_videos[row + 1]
            session_id = video_info.get('session_id', 'Unknown')
            video_name = video_info.get('video_path', 'Unknown').split('/')[-1] if video_info.get('video_path') else 'Unknown'
            workflow_mode = video_info.get('workflow_mode', 'unknown')
            
            # Get person counts from Supabase if available, otherwise from local files
            detected_count = 0
            identified_count = 0
            payment_count = 0
            
            if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
                try:
                    # Get person counts from Supabase
                    persons_data = supabase_manager.get_persons_by_session(session_id)
                    # Fix: Count all persons in the session, not just by detection_type
                    detected_count = len(persons_data) if persons_data else 0
                    identified_count = 0  # Will be updated if we have identification data
                    
                    # Get payment data
                    payment_data = supabase_manager.get_payment_results(session_id)
                    if payment_data:
                        payment_count = payment_data.get('total_payments', 0)
                except Exception as e:
                    # Fallback to local file system
                    detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
                    identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
                    detected_count = len([d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]) if os.path.exists(detected_path) else 0
                    identified_count = len([d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]) if os.path.exists(identified_path) else 0
            else:
                # Use local file system
                detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
                identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
                detected_count = len([d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]) if os.path.exists(detected_path) else 0
                identified_count = len([d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]) if os.path.exists(identified_path) else 0
                
            # Determine session type based on workflow mode and data
            session_type = "Unknown"
            
            # Debug: Log the workflow mode for troubleshooting
            if workflow_mode == "unknown" or workflow_mode is None:
                # Try to determine workflow mode from the data
                if payment_count > 0:
                    session_type = "Payment Detection"
                elif detected_count > 0 or identified_count > 0:
                    session_type = "Person Detection & Identification"
                else:
                    # Check if this session has any data at all
                    has_any_data = False
                    if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
                        try:
                            persons_data = supabase_manager.get_persons_by_session(session_id)
                            payment_data = supabase_manager.get_payment_results(session_id)
                            if (persons_data and len(persons_data) > 0) or payment_data:
                                has_any_data = True
                        except:
                            pass
                    
                    if has_any_data:
                        session_type = "Detection & Identification"
                    else:
                        session_type = "Incomplete Processing"
            elif workflow_mode == "payment_only":
                session_type = "Payment Detection"
            elif workflow_mode == "detect_identify":
                if detected_count > 0 and identified_count == 0:
                    session_type = "Person Detection"
                elif identified_count > 0 and detected_count == 0:
                    session_type = "Person Identification"
                elif detected_count > 0 and identified_count > 0:
                    session_type = "Mixed Detection & Identification"
                elif detected_count == 0 and identified_count == 0:
                    # Check if this session was actually processed but found no persons
                    session_type = "Detection (No Persons Found)"
                else:
                    session_type = "Detection & Identification"
            else:
                # Unknown workflow mode, try to determine from data
                if payment_count > 0:
                    session_type = "Payment Detection"
                elif detected_count > 0 or identified_count > 0:
                    session_type = "Person Detection & Identification"
                else:
                    session_type = "Incomplete Processing"

            with col_right:
                st.markdown(f"""
                <div class="session-card">
                    <h5>📹 Session {session_id}</h5>
                    <p><strong>📁 Type:</strong> {session_type}</p>
                    <p><strong>🔍 Detected:</strong> {detected_count} persons</p>
                    <p><strong>👤 Identified:</strong> {identified_count} persons</p>
                    {f'<p><strong>💳 Payments:</strong> {payment_count}</p>' if payment_count > 0 else ''}
                    <div style="display: flex; align-items: center; margin-top: 0.5rem;">
                        <span class="status-indicator status-inactive"></span>
                        <span style="margin-left: 0.5rem;">Completed</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
else:
    uploaded_videos = st.session_state.get('uploaded_videos', [])
    if uploaded_videos:
        st.info("📋 Videos uploaded but not yet processed. Start processing to see session data.")
    else:
        st.info("📋 No previously processed sessions found.")

# Fourth Half - Total Statistics Overview
st.markdown("---")  # Add a divider
st.markdown("### 📊 Total Statistics Overview")

# Calculate total statistics from the same processed videos list
processed_videos = get_processed_videos()

# Initialize variables to avoid NameError
total_sessions = 0
total_detected_sessions = 0
total_identified_sessions = 0
session_debug_info = []

if processed_videos:
    total_sessions = len(processed_videos)
    
    # Count detection and identification sessions
    total_detected_sessions = 0
    total_identified_sessions = 0
    
    # Debug: Track what we find for each session
    session_debug_info = []
    
    for video_info in processed_videos:
        session_id = video_info.get('session_id')
        if session_id:
            # Check if this session has any detected or identified persons
            session_has_detected = False
            session_has_identified = False
            debug_info = {"session_id": session_id, "detected": False, "identified": False, "method": ""}
            
            # First, try to get workflow mode from the session info
            workflow_mode = video_info.get('workflow_mode', 'unknown')
            debug_info["workflow_mode"] = workflow_mode
            
            # Always check local file system first for more reliable results
            detected_path = os.path.join(base_faces_dir, "Detected people", session_id)
            identified_path = os.path.join(base_faces_dir, "Identified people", session_id)
            
            # More robust checking for detected people
            if os.path.exists(detected_path):
                try:
                    detected_persons = [d for d in os.listdir(detected_path) if os.path.isdir(os.path.join(detected_path, d))]
                    session_has_detected = len(detected_persons) > 0
                    debug_info["detected_persons_count"] = len(detected_persons)
                except Exception as e:
                    session_has_detected = False
                    debug_info["detected_error"] = str(e)
            else:
                session_has_detected = False
            
            # More robust checking for identified people
            if os.path.exists(identified_path):
                try:
                    identified_persons = [d for d in os.listdir(identified_path) if os.path.isdir(os.path.join(identified_path, d))]
                    session_has_identified = len(identified_persons) > 0
                    debug_info["identified_persons_count"] = len(identified_persons)
                except Exception as e:
                    session_has_identified = False
                    debug_info["identified_error"] = str(e)
            else:
                session_has_identified = False
            
            # If local check didn't find anything, try Supabase as backup
            if not session_has_detected and not session_has_identified and SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
                try:
                    persons_data = supabase_manager.get_persons_by_session(session_id)
                    if persons_data:
                        session_has_detected = any(p.get('detection_type') == 'detected' for p in persons_data)
                        session_has_identified = any(p.get('detection_type') == 'identified' for p in persons_data)
                        debug_info["method"] = "supabase_backup"
                        debug_info["persons_count"] = len(persons_data)
                        debug_info["detected"] = session_has_detected
                        debug_info["identified"] = session_has_identified
                except Exception as e:
                    debug_info["supabase_error"] = str(e)
            
            debug_info["method"] = "local"
            debug_info["detected_path_exists"] = os.path.exists(detected_path)
            debug_info["identified_path_exists"] = os.path.exists(identified_path)
            debug_info["detected"] = session_has_detected
            debug_info["identified"] = session_has_identified
            
            # Categorize the session based on what type of processing was done
            # A session can be both detection and identification, so we count both
            if session_has_detected:
                total_detected_sessions += 1
            if session_has_identified:
                total_identified_sessions += 1
            
            # If we can't determine from file system, use workflow mode as fallback
            if not session_has_detected and not session_has_identified:
                if workflow_mode == "detect_identify":
                    # Assume it was a detection session if workflow was detect_identify
                    total_detected_sessions += 1
                    debug_info["categorized_by_workflow"] = "detect_identify"
                elif workflow_mode == "payment_only":
                    # Payment sessions don't count as detection or identification
                    debug_info["categorized_by_workflow"] = "payment_only"
                else:
                    # Unknown workflow mode, assume detection
                    total_detected_sessions += 1
                    debug_info["categorized_by_workflow"] = "unknown_assumed_detection"
            
            session_debug_info.append(debug_info)
    
    # Always show statistics if there are processed videos
    # Check if pandas and plotly are available for chart creation
    if PANDAS_AVAILABLE and PLOTLY_AVAILABLE:
        # Create data for pie chart - show three categories as originally requested
        if total_sessions > 0:
            # Calculate the metrics as originally requested
            total_detection_videos = 0  # Videos that performed detection (including mixed)
            total_identify_videos = 0   # Videos that performed identification (including mixed)
            
            for debug_info in session_debug_info:
                detected = debug_info.get("detected", False)
                identified = debug_info.get("identified", False)
                workflow_mode = debug_info.get("workflow_mode", "unknown")
                
                # Count detection videos (including mixed sessions)
                if detected or workflow_mode == "detect_identify":
                    total_detection_videos += 1
                
                # Count identification videos (including mixed sessions)
                if identified:
                    total_identify_videos += 1
            
            # Create data with the originally requested three categories
            chart_data = pd.DataFrame({
                'Category': ['Total Detection Videos', 'Total Identify Videos', 'Total Processed Videos'],
                'Count': [total_detection_videos, total_identify_videos, total_sessions]
            })
            
            # Filter out categories with 0 count to avoid showing empty slices
            chart_data_filtered = chart_data[chart_data['Count'] > 0].copy()
            
            # If we have no meaningful breakdown, show the total processed videos
            if len(chart_data_filtered) == 0:
                chart_data_filtered = pd.DataFrame({
                    'Category': ['Total Processed Videos'],
                    'Count': [total_sessions]
                })
            
            # Create pie chart with count labels
            fig = px.pie(chart_data_filtered, values='Count', names='Category', 
                        title='Session Processing Breakdown',
                        color_discrete_sequence=['#667eea', '#764ba2', '#f093fb'])
            
            # Update the pie chart to show counts instead of percentages
            fig.update_traces(textinfo='label+value', textposition='inside')
            
            # Display pie chart
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 No processing data available yet. Process some videos to see statistics.")

    # Show summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Detection Videos", total_detected_sessions)
    with col2:
        st.metric("Identification Videos", total_identified_sessions)
    with col3:
        st.metric("Total Processed Videos", total_sessions)
    
    # Temporary debug info to help troubleshoot
    if st.checkbox("🔍 Show Data Debug", key="temp_debug"):
        st.write("**Data Debug Info:**")
        st.write(f"- Total sessions: {total_sessions}")
        st.write(f"- Detection sessions: {total_detected_sessions}")
        st.write(f"- Identification sessions: {total_identified_sessions}")
        if total_sessions > 0 and PANDAS_AVAILABLE:
            st.write(f"- Chart data: {chart_data.to_dict('records')}")
        st.write(f"- PANDAS_AVAILABLE: {PANDAS_AVAILABLE}")
        st.write(f"- PLOTLY_AVAILABLE: {PLOTLY_AVAILABLE}")
        
        st.write("**Session Debug Details:**")
        for debug_info in session_debug_info:
            st.write(f"- Session {debug_info['session_id']}:")
            st.write(f"  - Method: {debug_info['method']}")
            st.write(f"  - Detected: {debug_info['detected']}")
            st.write(f"  - Identified: {debug_info['identified']}")
            if 'persons_count' in debug_info:
                st.write(f"  - Persons in DB: {debug_info['persons_count']}")
            if 'detected_persons_count' in debug_info:
                st.write(f"  - Detected persons count: {debug_info['detected_persons_count']}")
            if 'identified_persons_count' in debug_info:
                st.write(f"  - Identified persons count: {debug_info['identified_persons_count']}")
            if 'detected_path_exists' in debug_info:
                st.write(f"  - Detected path exists: {debug_info['detected_path_exists']}")
            if 'identified_path_exists' in debug_info:
                st.write(f"  - Identified path exists: {debug_info['identified_path_exists']}")
            if 'detected_error' in debug_info:
                st.write(f"  - Detected error: {debug_info['detected_error']}")
            if 'identified_error' in debug_info:
                st.write(f"  - Identified error: {debug_info['identified_error']}")
    
    # Add debug information for session counting
    if st.checkbox("🔧 Show Session Count Debug", key="debug_session_count"):
        st.write("**Session Count Debug Info:**")
        st.write(f"- Total processed sessions: {total_sessions}")
        st.write(f"- Detection sessions: {total_detected_sessions}")
        st.write(f"- Identification sessions: {total_identified_sessions}")
        st.write("**Individual Session Details:**")
        for i, video_info in enumerate(processed_videos):
            session_id = video_info.get('session_id')
            st.write(f"Session {i+1}: {session_id}")
            if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
                try:
                    persons_data = supabase_manager.get_persons_by_session(session_id)
                    detected_count = len([p for p in persons_data if p.get('detection_type') == 'detected'])
                    identified_count = len([p for p in persons_data if p.get('detection_type') == 'identified'])
                    st.write(f"  - Detected persons: {detected_count}")
                    st.write(f"  - Identified persons: {identified_count}")
                except Exception as e:
                    st.write(f"  - Error getting data: {e}")
else:
    # Fallback: display statistics as text when pandas/plotly not available
    st.markdown("### 📊 Statistics Summary")
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        st.metric("Total Sessions", total_sessions)
    with stat_col2:
        st.metric("Detection Sessions", total_detected_sessions)
    with stat_col3:
        st.metric("Identification Sessions", total_identified_sessions)
    
    uploaded_videos = st.session_state.get('uploaded_videos', [])
    if uploaded_videos:
        st.info("📊 Videos uploaded but not yet processed. Start processing to see statistics.")
    else:
        st.info("📊 No statistics available yet. Process some videos to see the overview.")