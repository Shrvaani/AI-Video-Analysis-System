import streamlit as st
import cv2
import os
import numpy as np
from ultralytics import YOLO
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

# Load YOLOv8 model (head detection model recommended)
model = YOLO("yolov8n.pt")  # You can replace this with a head detection model like "yolov8n_head.pt"

# Helper: Crop head area from bounding box
def crop_head(frame, box):
    x1, y1, x2, y2 = map(int, box)
    w = x2 - x1
    h = y2 - y1
    y2 = y1 + int(h * 0.4)
    head = frame[y1:y2, x1:x2]
    return head

# Helper: Create person folder and save first detection image
def create_person_folder_and_save_first_image(face_img, video_session_id, person_id, base_faces_dir):
    video_folder = os.path.join(base_faces_dir, "Detected people", video_session_id)
    person_folder = os.path.join(video_folder, person_id)
    os.makedirs(person_folder, exist_ok=True)
    first_detection_path = os.path.join(person_folder, "first_detection.jpg")
    cv2.imwrite(first_detection_path, face_img)
    return first_detection_path

# Helper: Save subsequent frame images for the person
def save_person_frame(face_img, video_session_id, person_id, frame_number, base_faces_dir):
    video_folder = os.path.join(base_faces_dir, "Detected people", video_session_id)
    person_folder = os.path.join(video_folder, person_id)
    os.makedirs(person_folder, exist_ok=True)
    frame_path = os.path.join(person_folder, f"frame_{frame_number:06d}.jpg")
    cv2.imwrite(frame_path, face_img)
    return frame_path

# Helper: Calculate distance between bounding boxes
def box_distance(box1, box2):
    cx1 = (box1[0] + box1[2]) / 2
    cy1 = (box1[1] + box1[3]) / 2
    cx2 = (box2[0] + box2[2]) / 2
    cy2 = (box2[1] + box2[3]) / 2
    return np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)

# Helper: Generate unique person ID
def generate_person_id():
    return f"person_{str(uuid.uuid4())[:8]}"

# Helper: Get count based on number of person_id folders
def get_person_count(person_id, video_session_id, base_faces_dir):
    video_folder = os.path.join(base_faces_dir, "Detected people", video_session_id)
    if os.path.exists(video_folder):
        person_folders = [d for d in os.listdir(video_folder) if os.path.isdir(os.path.join(video_folder, d))]
        return len([pid for pid in person_folders if pid == person_id])
    return 0

# Main detection function
def detect_persons(st, base_faces_dir, temp_dir, video_session_dir, video_path, video_session_id):
    st.subheader("Detect Mode")
    st.markdown("Upload a video to detect and assign IDs to persons.")

    with st.sidebar:
        max_distance = st.slider("Max Proximity Distance (pixels)", 10, 100, 50, 5,
                                help="Max distance for tracking the same person across frames")
        max_frame_gap = st.slider("Max Frame Gap", 10, 100, 30, 5,
                                 help="Max frames to consider for re-identification")

    if 'current_video_session' in st.session_state and st.button("Stop Current Video Processing"):
        st.session_state.stop_processing = True
        st.session_state.current_video_session = None
        st.success("🛑 Video processing stopped. You can now upload a new video.")
        st.rerun()

    if video_path and 'current_video_session' not in st.session_state:
        st.session_state.current_video_session = video_session_id
        st.success(f"**Video Session {video_session_id}:** Video processing started!")

    if 'current_video_session' in st.session_state and video_session_id == st.session_state.current_video_session:
        st.subheader(f"Processing Video Session {video_session_id}: {os.path.basename(video_path)}")

        person_registry = {}  # {person_id: {"box": (x1, y1, x2, y2), "frame_count": int, "last_seen": int}}
        current_frame_persons = {}  # {person_id: (x1, y1, x2, y2)} for the current frame
        detection_counter = 0
        
        video_session_folder = os.path.join(base_faces_dir, "Detected people", video_session_id)
        os.makedirs(video_session_folder, exist_ok=True)

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
            if st.session_state.stop_processing:
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

                    best_match_id = None
                    min_distance = float('inf')
                    current_box = (x1, y1, x2, y2)

                    for person_id, data in person_registry.items():
                        prev_box = data["box"]
                        distance = box_distance(current_box, prev_box)
                        if distance < min_distance and frame_counter - data["last_seen"] <= max_frame_gap:
                            min_distance = distance
                            best_match_id = person_id

                    if best_match_id and min_distance <= max_distance:
                        person_id = best_match_id
                        label = f"Known: {person_id}"
                        color = (0, 255, 0)
                        person_registry[person_id]["box"] = current_box
                        person_registry[person_id]["frame_count"] += 1
                        person_registry[person_id]["last_seen"] = frame_counter
                        save_person_frame(head_crop, video_session_id, person_id, frame_counter, base_faces_dir)
                    else:
                        if len(person_registry) < 6:
                            person_id = generate_person_id()
                            label = f"New: {person_id}"
                            color = (0, 0, 255)
                            first_detection_path = create_person_folder_and_save_first_image(
                                head_crop, video_session_id, person_id, base_faces_dir
                            )
                            
                            # Save to Supabase if available
                            if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
                                try:
                                    # Save person data
                                    supabase_manager.save_person_data(video_session_id, person_id, "detected")
                                    # Save first detection image
                                    supabase_manager.save_face_image(video_session_id, person_id, head_crop, "first_detection")
                                except Exception as e:
                                    st.warning(f"⚠️ Failed to save person data to cloud: {e}")
                            
                            person_registry[person_id] = {
                                "box": current_box,
                                "frame_count": 1,
                                "last_seen": frame_counter
                            }
                        else:
                            if best_match_id:
                                person_id = best_match_id
                                label = f"Known: {person_id}"
                                color = (0, 255, 0)
                                person_registry[person_id]["box"] = current_box
                                person_registry[person_id]["frame_count"] += 1
                                person_registry[person_id]["last_seen"] = frame_counter
                                save_person_frame(head_crop, video_session_id, person_id, frame_counter, base_faces_dir)
                            else:
                                person_id = min(person_registry.keys(), key=lambda pid: box_distance(current_box, person_registry[pid]["box"]))
                                label = f"Known: {person_id}"
                                color = (0, 255, 0)
                                person_registry[person_id]["box"] = current_box
                                person_registry[person_id]["frame_count"] += 1
                                person_registry[person_id]["last_seen"] = frame_counter
                                save_person_frame(head_crop, video_session_id, person_id, frame_counter, base_faces_dir)

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

        st.success(f"✅ Video Session {video_session_id} processing completed!")
        if person_registry:
            st.subheader("Person Detection Summary")
            summary_data = []
            payment_data = detect_payments(st, video_path, video_session_id) if 'workflow_mode' in st.session_state and st.session_state.workflow_mode == "detect_identify_payment" else None
            for person_id, data in person_registry.items():
                count = get_person_count(person_id, video_session_id, base_faces_dir)
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
known_faces/
└── Detected people/
    └── {video_session_id}/
{chr(10).join([f'    ├── {pid}/' + chr(10) + f'    │   ├── first_detection.jpg' + chr(10) + f'    │   └── frame_*.jpg ({data["frame_count"]} frames)' for pid, data in person_registry.items()])}
                """)
        
        if os.path.exists(video_session_dir):
            shutil.rmtree(video_session_dir)
        
        del st.session_state.current_video_session
        st.info("The video has been processed. Switch to Identify mode or upload a new video.")

    if not video_path and not st.session_state.uploaded_videos:
        st.write("Please upload a video to start detection.")
        if os.path.exists(base_faces_dir):
            existing_sessions = [d for d in os.listdir(os.path.join(base_faces_dir, "Detected people")) if os.path.isdir(os.path.join(base_faces_dir, "Detected people", d))]
            if existing_sessions:
                st.subheader("Previously Processed Video Sessions")
                for session_id in existing_sessions:
                    session_path = os.path.join(base_faces_dir, "Detected people", session_id)
                    person_folders = [d for d in os.listdir(session_path) if os.path.isdir(os.path.join(session_path, d))]
                    st.write(f"**Session {session_id}**: {len(person_folders)} unique persons detected")