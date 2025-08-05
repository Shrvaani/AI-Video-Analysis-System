import streamlit as st
import cv2
import os
import numpy as np
from ultralytics import YOLO
from skimage.metrics import structural_similarity as ssim
import uuid
import shutil
from payment_detection_logic import detect_payments

# Import Supabase manager if available
try:
    from supabase_config import supabase_manager
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    supabase_manager = None

# Load YOLOv8 model for real-time detection in identify mode
model = YOLO("yolov8n.pt")

# Helper: Crop head area from bounding box
def crop_head(frame, box):
    x1, y1, x2, y2 = map(int, box)
    w = x2 - x1
    h = y2 - y1
    y2 = y1 + int(h * 0.4)
    head = frame[y1:y2, x1:x2]
    return head

# Helper: Load and preprocess image
def load_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    img = cv2.resize(img, (100, 100))
    return img

# Helper: Compare two images using SSIM
def compare_images(img1, img2, threshold=0.7):
    if img1 is None or img2 is None:
        return False
    similarity, _ = ssim(img1, img2, full=True)
    return similarity > threshold

# Helper: Get all image paths for a person
def get_person_images(video_session_id, person_id, base_dir, is_detected=True):
    top_dir = "Detected people" if is_detected else "Identified people"
    person_folder = os.path.join(base_dir, top_dir, video_session_id, person_id)
    if not os.path.exists(person_folder):
        return []
    images = [os.path.join(person_folder, f) for f in os.listdir(person_folder) if f.endswith(('.jpg', '.jpeg'))]
    return images

# Helper: Save person frame
def save_person_frame(face_img, video_session_id, person_id, frame_number, base_dir, is_detected=True):
    top_dir = "Identified people"
    video_folder = os.path.join(base_dir, top_dir, video_session_id)
    person_folder = os.path.join(video_folder, person_id)
    os.makedirs(person_folder, exist_ok=True)
    frame_path = os.path.join(person_folder, f"frame_{frame_number:06d}.jpg")
    cv2.imwrite(frame_path, face_img)
    return frame_path

# Helper: Count the number of sessions where a person_id appears
def count_person_sessions(person_id, base_dir):
    session_count = 0
    detected_sessions = [d for d in os.listdir(os.path.join(base_dir, "Detected people")) if os.path.isdir(os.path.join(base_dir, "Detected people", d))]
    identified_sessions = [d for d in os.listdir(os.path.join(base_dir, "Identified people")) if os.path.isdir(os.path.join(base_dir, "Identified people", d))]
    for session_id in detected_sessions:
        detected_path = os.path.join(base_dir, "Detected people", session_id, person_id)
        if os.path.exists(detected_path):
            session_count += 1
    for session_id in identified_sessions:
        identified_path = os.path.join(base_dir, "Identified people", session_id, person_id)
        if os.path.exists(identified_path):
            session_count += 1
    return session_count

# Main identification function
def identify_persons(st, base_dir, temp_dir, video_session_dir, video_path, video_session_id):
    st.subheader("Identify Mode")
    st.markdown("Identifying persons based on previously detected data.")

    if 'current_video_session' in st.session_state and st.button("Stop Current Video Processing", key=f"stop_button_{video_session_id}"):
        st.session_state.stop_processing = True
        st.session_state.current_video_session = None
        st.success("🛑 Video processing stopped. You can now upload a new video.")
        st.rerun()

    if video_path and 'current_video_session' not in st.session_state:
        st.session_state.current_video_session = video_session_id
        st.success(f"**Video Session {video_session_id}:** Identification started!")

    if video_session_id == st.session_state.current_video_session:
        st.subheader(f"Processing Video Session {video_session_id}: {os.path.basename(video_path)}")

        person_registry = {}  # {person_id: {"box": (x1, y1, x2, y2), "frame_count": int, "last_seen": int}}
        current_frame_persons = {}  # {person_id: (x1, y1, x2, y2)} for the current frame
        detection_counter = 0

        cap = cv2.VideoCapture(video_path)
        stframe = st.empty()
        progress_bar = st.progress(0)
        frame_counter = 0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            unique_persons_display = st.empty()
        with col2:
            current_frame_display = st.empty()
        with col3:
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

                    best_known_match_id = None
                    best_similarity = 0

                    # Check all existing detected persons
                    detected_sessions = [d for d in os.listdir(os.path.join(base_dir, "Detected people")) if os.path.isdir(os.path.join(base_dir, "Detected people", d))]
                    for session_id in detected_sessions:
                        for pid in os.listdir(os.path.join(base_dir, "Detected people", session_id)):
                            stored_images = get_person_images(session_id, pid, base_dir, is_detected=True)
                            for stored_img_path in stored_images:
                                stored_img = load_image(stored_img_path)
                                if stored_img is not None and new_img is not None:
                                    similarity = ssim(new_img, stored_img, full=True)[0]
                                    if similarity > best_similarity and similarity > 0.7:
                                        best_similarity = similarity
                                        best_known_match_id = pid

                    if best_known_match_id:
                        person_id = best_known_match_id
                        label = f"Known: {person_id}"
                        color = (0, 255, 0)
                        if person_id not in person_registry:
                            person_registry[person_id] = {"box": current_box, "frame_count": 1, "last_seen": frame_counter}
                            
                            # Save to Supabase if available (only for new identifications in this session)
                            if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
                                try:
                                    # Save person data
                                    supabase_manager.save_person_data(video_session_id, person_id, "identified")
                                    # Save first identification image
                                    supabase_manager.save_face_image(video_session_id, person_id, head_crop, "first_identification")
                                except Exception as e:
                                    st.warning(f"⚠️ Failed to save person data to cloud: {e}")
                        else:
                            person_registry[person_id]["box"] = current_box
                            person_registry[person_id]["frame_count"] += 1
                            person_registry[person_id]["last_seen"] = frame_counter
                        # Update count based on total sessions where person appears
                        st.session_state.person_count[person_id] = count_person_sessions(person_id, base_dir) + 1
                        save_person_frame(head_crop, video_session_id, person_id, frame_counter, base_dir, is_detected=False)
                    else:
                        continue  # Skip unmatched detections in identification mode

                    current_frame_persons[person_id] = current_box

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    cv2.rectangle(frame, (x1, y1 - text_size[1] - 10), (x1 + text_size[0], y1), color, -1)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)

            stats_text = [
                f"Total Unique Persons: {len(person_registry)}",
                f"Persons in Current Frame: {len(current_frame_persons)}",
                f"Frame: {frame_counter}/{total_frames}"
            ]
            for i, text in enumerate(stats_text):
                cv2.putText(frame, text, (10, 30 + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            unique_persons_display.metric("Unique Persons", len(person_registry))
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

        st.success(f"✅ Video Session {video_session_id} identification completed!")
        if person_registry:
            st.subheader("Person Identification Summary")
            summary_data = []
            payment_data = detect_payments(st, video_path, video_session_id) if 'workflow_mode' in st.session_state and st.session_state.workflow_mode == "detect_identify_payment" else None
            for person_id, data in person_registry.items():
                count = st.session_state.person_count.get(person_id, count_person_sessions(person_id, base_dir) + 1)
                validated_frame_count = min(data['frame_count'], total_frames) if data['frame_count'] is not None else 0
                person_summary = {
                    "Person ID": person_id,
                    "Count": np.int64(count),
                    "First Seen (Frame)": np.int64(max(0, data['last_seen'] - validated_frame_count + 1)),
                    "Last Seen (Frame)": np.int64(data['last_seen']),
                    "Total Appearances": np.int64(validated_frame_count),
                }
                if payment_data:
                    person_summary.update({
                        "Cash Payments": np.int64(payment_data.get("cash_payments", 0)),
                        "Card Payments": np.int64(payment_data.get("card_payments", 0)),
                        "Total Payments": np.int64(payment_data.get("total_payments", 0))
                    })
                summary_data.append(person_summary)
            st.table(summary_data)
            with st.expander("View Folder Structure"):
                st.code(f"""
{base_dir}/
    └── Identified people/
        └── {video_session_id}/
{chr(10).join([f'    └── Identified people/{video_session_id}/' + chr(10) + f'        ├── {pid}/' + chr(10) + f'        │   ├── first_detection.jpg' + chr(10) + f'        │   └── frame_*.jpg ({data["frame_count"]} frames)' for pid, data in person_registry.items()])}
                """)
        
        if os.path.exists(video_session_dir):
            shutil.rmtree(video_session_dir)
        
        del st.session_state.current_video_session
        st.info("The video has been identified. Upload a new video for detection or the same video again for re-identification.")

    if not video_path and not st.session_state.uploaded_videos:
        st.write("Please upload a video to start identification.")
        if os.path.exists(base_dir):
            identified_sessions = [d for d in os.listdir(os.path.join(base_dir, "Identified people")) if os.path.isdir(os.path.join(base_dir, "Identified people", d))]
            if identified_sessions:
                st.subheader("Previously Identified Video Sessions")
                for session_id in identified_sessions:
                    session_path = os.path.join(base_dir, "Identified people", session_id)
                    person_folders = [d for d in os.listdir(session_path) if os.path.isdir(os.path.join(session_path, d))]
                    st.write(f"**Session {session_id}**: {len(person_folders)} persons identified")