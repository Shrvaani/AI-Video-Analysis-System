import streamlit as st
import cv2
import numpy as np
import os
import shutil
import uuid
from ultralytics import YOLO
from skimage.metrics import structural_similarity as ssim
from PIL import Image
import io

# Import Supabase manager if available
try:
    from supabase_config import supabase_manager
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    supabase_manager = None

# Initialize YOLO model
try:
    model = YOLO("yolov8n.pt")
except Exception as e:
    st.error(f"Error loading YOLO model: {e}")
    model = None

def crop_head(frame, box):
    """Crop the head region from a person detection"""
    x1, y1, x2, y2 = box
    # Crop head region (upper 1/3 of the person)
    head_height = int((y2 - y1) * 0.3)
    head_y1 = y1
    head_y2 = y1 + head_height
    head_crop = frame[head_y1:head_y2, x1:x2]
    return head_crop

def load_image(image_path):
    """Load image for comparison"""
    try:
        if isinstance(image_path, str):
            if os.path.exists(image_path):
                return cv2.imread(image_path)
            else:
                return None
        else:
            # Handle numpy array
            return image_path
    except Exception as e:
        st.warning(f"Error loading image: {e}")
        return None

def get_person_images(video_session_id, person_id, base_dir, is_detected=True):
    """Get all images for a person from a specific session"""
    folder_type = "Detected people" if is_detected else "Identified people"
    person_folder = os.path.join(base_dir, folder_type, video_session_id, person_id)
    if os.path.exists(person_folder):
        images = [os.path.join(person_folder, f) for f in os.listdir(person_folder) if f.endswith(('.jpg', '.jpeg'))]
        return images
    return []

def save_person_frame(face_img, video_session_id, person_id, frame_number, base_dir, is_detected=True):
    """Save a person's face image"""
    folder_type = "Detected people" if is_detected else "Identified people"
    person_folder = os.path.join(base_dir, folder_type, video_session_id, person_id)
    os.makedirs(person_folder, exist_ok=True)
    
    frame_path = os.path.join(person_folder, f"frame_{frame_number}.jpg")
    cv2.imwrite(frame_path, face_img)
    return frame_path

def generate_person_id():
    """Generate a unique person ID"""
    return f"person_{str(uuid.uuid4())[:8]}"

def box_distance(box1, box2):
    """Calculate distance between two bounding boxes"""
    center1 = ((box1[0] + box1[2]) // 2, (box1[1] + box1[3]) // 2)
    center2 = ((box2[0] + box2[2]) // 2, (box2[1] + box2[3]) // 2)
    return np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)

def mixed_detection_identification(st, base_dir, temp_dir, video_session_dir, video_path, video_session_id):
    """Mixed mode: Detect new people and identify existing people in the same video"""
    st.subheader("🔄 Mixed Detection & Identification Mode")
    st.markdown("Detecting new people and identifying existing people in the same video.")

    if 'current_video_session' in st.session_state and st.button("Stop Current Video Processing", key=f"stop_button_{video_session_id}"):
        st.session_state.stop_processing = True
        st.session_state.current_video_session = None
        st.success("🛑 Video processing stopped. You can now upload a new video.")
        st.rerun()

    if video_path and 'current_video_session' not in st.session_state:
        st.session_state.current_video_session = video_session_id
        st.success(f"**Video Session {video_session_id}:** Mixed detection and identification started!")

    if video_session_id == st.session_state.current_video_session:
        st.subheader(f"Processing Video Session {video_session_id}: {os.path.basename(video_path)}")

        # Initialize tracking
        person_registry = {}  # {person_id: {"box": (x1, y1, x2, y2), "frame_count": int, "last_seen": int, "type": "new" or "existing"}}
        current_frame_persons = {}  # {person_id: (x1, y1, x2, y2)} for the current frame
        detection_counter = 0
        
        # Create session folders
        detected_folder = os.path.join(base_dir, "Detected people", video_session_id)
        identified_folder = os.path.join(base_dir, "Identified people", video_session_id)
        os.makedirs(detected_folder, exist_ok=True)
        os.makedirs(identified_folder, exist_ok=True)

        # Load existing known faces for identification
        known_faces = {}
        existing_sessions = []
        
        # Check if directories exist and get existing sessions
        detected_people_dir = os.path.join(base_dir, "Detected people")
        identified_people_dir = os.path.join(base_dir, "Identified people")
        
        if os.path.exists(detected_people_dir):
            existing_sessions.extend([d for d in os.listdir(detected_people_dir) if os.path.isdir(os.path.join(detected_people_dir, d))])
        
        if os.path.exists(identified_people_dir):
            existing_sessions.extend([d for d in os.listdir(identified_people_dir) if os.path.isdir(os.path.join(identified_people_dir, d))])
        
        # Remove duplicates and current session
        existing_sessions = list(set(existing_sessions))
        if video_session_id in existing_sessions:
            existing_sessions.remove(video_session_id)
        
        st.info(f"🔍 Found {len(existing_sessions)} existing sessions to check for known faces")
        
        for session_id in existing_sessions:
            detected_path = os.path.join(base_dir, "Detected people", session_id)
            identified_path = os.path.join(base_dir, "Identified people", session_id)
            
            # Load faces from detected people
            if os.path.exists(detected_path):
                for person_id in os.listdir(detected_path):
                    person_path = os.path.join(detected_path, person_id)
                    if os.path.isdir(person_path):
                        images = get_person_images(session_id, person_id, base_dir, is_detected=True)
                        if images:
                            known_faces[f"detected_{person_id}"] = images
                            st.write(f"📸 Loaded {len(images)} images for detected person: {person_id} from session {session_id}")
            
            # Load faces from identified people
            if os.path.exists(identified_path):
                for person_id in os.listdir(identified_path):
                    person_path = os.path.join(identified_path, person_id)
                    if os.path.isdir(person_path):
                        images = get_person_images(session_id, person_id, base_dir, is_detected=False)
                        if images:
                            known_faces[f"identified_{person_id}"] = images
                            st.write(f"📸 Loaded {len(images)} images for identified person: {person_id} from session {session_id}")
        
        st.success(f"✅ Loaded {len(known_faces)} known faces from existing sessions")
        
        if not known_faces:
            st.warning("⚠️ No existing faces found. All people will be classified as new.")

        cap = cv2.VideoCapture(video_path)
        stframe = st.empty()
        progress_bar = st.progress(0)
        frame_counter = 0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            new_persons_display = st.empty()
        with col2:
            existing_persons_display = st.empty()
        with col3:
            current_frame_display = st.empty()
        with col4:
            total_detections_display = st.empty()

        while cap.isOpened():
            if st.session_state.get('stop_processing'):
                break

            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame)
            current_frame_persons.clear()

            for det in results[0].boxes.data:
                cls_id = int(det[5])
                if cls_id == 0:  # Class 0 = person
                    x1, y1, x2, y2 = map(int, det[:4])
                    head_crop = crop_head(frame, (x1, y1, x2, y2))

                    if head_crop.size == 0:
                        continue

                    temp_img_path = os.path.join(temp_dir, f"temp_detection_{detection_counter}.jpg")
                    cv2.imwrite(temp_img_path, head_crop)
                    detection_counter += 1

                    current_box = (x1, y1, x2, y2)
                    new_img = load_image(temp_img_path)

                    # Try to identify as existing person
                    best_known_match_id = None
                    best_similarity = 0
                    match_debug_info = []

                    for person_id, stored_images in known_faces.items():
                        for stored_img_path in stored_images:
                            stored_img = load_image(stored_img_path)
                            if stored_img is not None and new_img is not None:
                                try:
                                    similarity = ssim(new_img, stored_img, full=True)[0]
                                    match_debug_info.append(f"{person_id}: {similarity:.3f}")
                                    if similarity > best_similarity and similarity > 0.5:  # Lowered threshold from 0.7 to 0.5
                                        best_similarity = similarity
                                        best_known_match_id = person_id
                                except Exception as e:
                                    st.warning(f"Error calculating similarity: {e}")
                                    continue

                    # Debug: Show top 3 matches if any
                    if match_debug_info:
                        match_debug_info.sort(key=lambda x: float(x.split(': ')[1]), reverse=True)
                        top_matches = match_debug_info[:3]
                        st.write(f"🔍 Frame {frame_counter} - Top matches: {', '.join(top_matches)}")

                    if best_known_match_id:
                        # Existing person identified
                        person_id = best_known_match_id
                        label = f"Known: {person_id} (Sim: {best_similarity:.3f})"
                        color = (0, 255, 0)  # Green for identified
                        person_type = "existing"
                        
                        if person_id not in person_registry:
                            person_registry[person_id] = {
                                "box": current_box,
                                "frame_count": 1,
                                "last_seen": frame_counter,
                                "type": person_type
                            }
                            # Save first identification image
                            save_person_frame(head_crop, video_session_id, person_id, frame_counter, base_dir, is_detected=False)
                            st.success(f"✅ Identified existing person: {person_id} (similarity: {best_similarity:.3f})")
                        else:
                            person_registry[person_id]["box"] = current_box
                            person_registry[person_id]["frame_count"] += 1
                            person_registry[person_id]["last_seen"] = frame_counter
                            save_person_frame(head_crop, video_session_id, person_id, frame_counter, base_dir, is_detected=False)
                    else:
                        # New person detected
                        # Check if this person is already being tracked in current video
                        best_match_id = None
                        min_distance = float('inf')
                        
                        for tracked_id, data in person_registry.items():
                            if data["type"] == "new":  # Only match with new people
                                prev_box = data["box"]
                                distance = box_distance(current_box, prev_box)
                                if distance < min_distance and frame_counter - data["last_seen"] <= 30:  # 30 frame gap
                                    min_distance = distance
                                    best_match_id = tracked_id

                        if best_match_id and min_distance <= 50:  # 50 pixel threshold
                            # Continue tracking existing new person
                            person_id = best_match_id
                            label = f"New: {person_id}"
                            color = (255, 0, 0)  # Red for new
                            person_registry[person_id]["box"] = current_box
                            person_registry[person_id]["frame_count"] += 1
                            person_registry[person_id]["last_seen"] = frame_counter
                            save_person_frame(head_crop, video_session_id, person_id, frame_counter, base_dir, is_detected=True)
                        else:
                            # New person detected
                            person_id = generate_person_id()
                            label = f"New: {person_id}"
                            color = (255, 0, 0)  # Red for new
                            person_type = "new"
                            person_registry[person_id] = {
                                "box": current_box,
                                "frame_count": 1,
                                "last_seen": frame_counter,
                                "type": person_type
                            }
                            # Save first detection image
                            save_person_frame(head_crop, video_session_id, person_id, frame_counter, base_dir, is_detected=True)
                            st.info(f"🆕 Detected new person: {person_id}")

                    current_frame_persons[person_id] = current_box

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    cv2.rectangle(frame, (x1, y1 - text_size[1] - 10), (x1 + text_size[0], y1), color, -1)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)

            # Update metrics
            new_persons = len([p for p in person_registry.values() if p["type"] == "new"])
            existing_persons = len([p for p in person_registry.values() if p["type"] == "existing"])
            
            stats_text = [
                f"New Persons: {new_persons}",
                f"Existing Persons: {existing_persons}",
                f"Current Frame: {len(current_frame_persons)}",
                f"Frame: {frame_counter}/{total_frames}"
            ]
            for i, text in enumerate(stats_text):
                cv2.putText(frame, text, (10, 30 + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            new_persons_display.metric("New Persons", new_persons)
            existing_persons_display.metric("Existing Persons", existing_persons)
            current_frame_display.metric("Current Frame", len(current_frame_persons))
            total_detections_display.metric("Total Detections", detection_counter)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            stframe.image(frame_rgb, channels="RGB", use_container_width=True)

            frame_counter += 1
            progress_bar.progress(frame_counter / total_frames)

        cap.release()

        # Check if processing was stopped
        if st.session_state.get('stop_processing'):
            st.warning("🛑 Video processing was stopped by user.")
            st.session_state.stop_processing = False
            return

        st.success(f"✅ Video Session {video_session_id} mixed processing completed!")
        
        if person_registry:
            st.subheader("Mixed Detection & Identification Summary")
            summary_data = []
            
            for person_id, data in person_registry.items():
                person_type = data["type"]
                person_summary = {
                    "Person ID": person_id,
                    "Type": "🆕 New" if person_type == "new" else "👤 Existing",
                    "First Seen (Frame)": np.int64(max(0, data['last_seen'] - data['frame_count'] + 1)),
                    "Last Seen (Frame)": np.int64(data['last_seen']),
                    "Total Appearances": np.int64(data['frame_count']),
                }
                summary_data.append(person_summary)
            
            st.table(summary_data)
            
            # Summary statistics
            new_count = len([p for p in person_registry.values() if p["type"] == "new"])
            existing_count = len([p for p in person_registry.values() if p["type"] == "existing"])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🆕 New People Detected", new_count)
            with col2:
                st.metric("👤 Existing People Identified", existing_count)
            with col3:
                st.metric("📊 Total People", len(person_registry))

        if os.path.exists(video_session_dir):
            shutil.rmtree(video_session_dir)
        
        del st.session_state.current_video_session
        st.info("The video has been processed in mixed mode. Upload a new video for more processing.")

    if not video_path and not st.session_state.uploaded_videos:
        st.write("Please upload a video to start mixed detection and identification.") 