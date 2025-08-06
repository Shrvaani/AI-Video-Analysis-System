import cv2
import numpy as np
import csv
import os
from ultralytics import YOLO

# Import Supabase manager if available
try:
    from supabase_config import supabase_manager
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    supabase_manager = None

# Initialize models with error handling
model1 = None
model2 = None
class_names = {}
CLASS_IDS = {"cash": 1, "card": 2}  # Matches YAML: cash=1, card=2

try:
    model1 = YOLO("best.pt")  # General-purpose model
    class_names = model1.names
except Exception as e:
    print(f"Warning: Could not load best.pt model: {e}")
    model1 = None

try:
    model2 = YOLO("card_cash_hand_best.pt")  # Model trained on cash and card
except Exception as e:
    print(f"Warning: Could not load card_cash_hand_best.pt model: {e}")
    model2 = None

# Payment detection function
def detect_payments(st, video_path, video_session_id):
    st.subheader(f"Payment Detection in Video Session {video_session_id}: {os.path.basename(video_path)}")
    st.markdown("Detecting cash and card payments in the video.")

    # Check if models are available
    if model1 is None and model2 is None:
        st.error("❌ Payment detection models are not available!")
        st.info("Please ensure the model files (best.pt and card_cash_hand_best.pt) are present in the application directory.")
        return None

    payment_type = None
    first_cash_detected = False
    first_card_detected = False
    cash_payments = 0
    card_payments = 0
    tracked_centroids = {}  # Track centroids across frames: {centroid: (cls_id, frame_count, confidence)}
    payment_events = []  # Track all payment events for better analysis

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        st.error("Error: Could not open video file.")
        return None

    stframe = st.empty()
    progress_bar = st.progress(0)
    frame_counter = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames == 0:
        st.error("Error: Video file appears to be empty or corrupted.")
        cap.release()
        return None

    st.info(f"Processing {total_frames} frames for payment detection...")

    # Add real-time metrics display
    col1, col2, col3 = st.columns(3)
    with col1:
        cash_display = st.empty()
    with col2:
        card_display = st.empty()
    with col3:
        total_display = st.empty()

    while cap.isOpened():
        if st.session_state.get('stop_processing'):
            break

        ret, frame = cap.read()
        if not ret:
            break

        current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

        # Run YOLO inference with available models
        all_dets = []
        
        try:
            if model1 is not None:
                results1 = model1(frame, conf=0.4)  # Increased confidence threshold
                all_dets.extend(results1[0].boxes.data.tolist())
            
            if model2 is not None:
                results2 = model2(frame, conf=0.4)  # Increased confidence threshold
                all_dets.extend(results2[0].boxes.data.tolist())
        except Exception as e:
            st.warning(f"Warning: Error during model inference on frame {current_frame}: {e}")
            continue

        # Apply non-maximum suppression (NMS) manually
        if all_dets:
            try:
                boxes = [[int(x1), int(y1), int(x2 - x1), int(y2 - y1)] for _, x1, y1, x2, y2, _ in all_dets]
                scores = [float(confidence) for _, _, _, _, _, confidence in all_dets]
                classes = [int(cls_id) for cls_id, _, _, _, _, _ in all_dets]
                indices = cv2.dnn.NMSBoxes(boxes, scores, 0.4, 0.5)  # Adjusted NMS parameters
                if len(indices) > 0:
                    all_dets = [all_dets[i] for i in indices.flatten()]
                else:
                    all_dets = []
            except Exception as e:
                st.warning(f"Warning: Error during NMS on frame {current_frame}: {e}")
                all_dets = []

        for det in all_dets:
            try:
                cls_id, x1, y1, x2, y2, confidence = map(float, det)
                cls_id = int(cls_id)
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                # Only process cash and card detections with high confidence
                if cls_id not in [CLASS_IDS["cash"], CLASS_IDS["card"]] or confidence < 0.4:
                    continue

                center = (x1 + x2) // 2, (y1 + y2) // 2
                center_key = f"{center[0]}_{center[1]}"

                # Improved tracking logic to prevent duplicate counting
                if center_key in tracked_centroids:
                    prev_cls_id, prev_frame, prev_confidence = tracked_centroids[center_key]
                    # Only count as new if it's a different class or significantly different confidence
                    if (prev_cls_id == cls_id and 
                        current_frame - prev_frame < 15 and  # Reduced frame gap
                        abs(confidence - prev_confidence) < 0.1):  # Similar confidence
                        continue

                tracked_centroids[center_key] = (cls_id, current_frame, confidence)

                # Determine payment type based on class ID
                if cls_id == CLASS_IDS["cash"]:
                    payment_label = "Cash Payment"
                    color = (0, 165, 255)  # Orange
                    if not first_cash_detected:
                        first_cash_detected = True
                        if payment_type is None:
                            payment_type = "Cash Payment"
                    cash_payments += 1
                    payment_events.append({
                        "type": "cash",
                        "frame": current_frame,
                        "confidence": confidence,
                        "center": center
                    })
                elif cls_id == CLASS_IDS["card"]:
                    payment_label = "Card Payment"
                    color = (255, 0, 255)  # Purple
                    if not first_card_detected:
                        first_card_detected = True
                        if payment_type is None:
                            payment_type = "Card Payment"
                    card_payments += 1
                    payment_events.append({
                        "type": "card",
                        "frame": current_frame,
                        "confidence": confidence,
                        "center": center
                    })

                label = f"{payment_label} (Conf: {confidence:.2f})"
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            except Exception as e:
                st.warning(f"Warning: Error processing detection on frame {current_frame}: {e}")
                continue

        # Display frame every 10 frames to avoid overwhelming the UI
        if frame_counter % 10 == 0:
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                stframe.image(frame_rgb, channels="RGB", use_container_width=True)
                
                # Update real-time metrics
                cash_display.metric("Cash Payments", cash_payments)
                card_display.metric("Card Payments", card_payments)
                total_display.metric("Total Payments", cash_payments + card_payments)
            except Exception as e:
                st.warning(f"Warning: Error displaying frame {current_frame}: {e}")

        frame_counter += 1
        progress_bar.progress(frame_counter / total_frames)

    cap.release()

    # Check if processing was stopped
    if st.session_state.get('stop_processing'):
        st.warning("🛑 Payment detection was stopped by user.")
        st.session_state.stop_processing = False
        return None

    # Post-processing: Analyze payment events to improve accuracy
    if payment_events:
        # Group nearby events to avoid double counting
        filtered_events = []
        for event in payment_events:
            is_duplicate = False
            for existing in filtered_events:
                if (event["type"] == existing["type"] and 
                    abs(event["frame"] - existing["frame"]) < 30 and  # Within 30 frames
                    abs(event["center"][0] - existing["center"][0]) < 50 and  # Within 50 pixels
                    abs(event["center"][1] - existing["center"][1]) < 50):
                    is_duplicate = True
                    break
            if not is_duplicate:
                filtered_events.append(event)
        
        # Recalculate counts based on filtered events
        cash_payments = len([e for e in filtered_events if e["type"] == "cash"])
        card_payments = len([e for e in filtered_events if e["type"] == "card"])
        
        # Determine payment type based on first detected payment
        if filtered_events:
            first_event = min(filtered_events, key=lambda x: x["frame"])
            payment_type = "Cash Payment" if first_event["type"] == "cash" else "Card Payment"

    total_payments = cash_payments + card_payments
    st.success(f"✅ Payment Detection Completed!")
    st.info(f"**Results:** Total Payments = {total_payments}, Cash Payments = {cash_payments}, Card Payments = {card_payments}")

    # Save summary to CSV
    try:
        csv_filename = f"payment_summary_{video_session_id}.csv"
        with open(csv_filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Metric", "Count"])
            writer.writerow(["Total Payments", total_payments])
            writer.writerow(["Cash Payments", cash_payments])
            writer.writerow(["Card Payments", card_payments])
            st.success(f"📊 Payment summary saved to {csv_filename}")
    except Exception as e:
        st.warning(f"Warning: Could not save payment summary: {e}")

    # Save payment results to Supabase if available
    if SUPABASE_AVAILABLE and supabase_manager and supabase_manager.is_connected():
        try:
            payment_data = {
                "total_payments": total_payments,
                "cash_payments": cash_payments,
                "card_payments": card_payments
            }
            if supabase_manager.save_payment_results(video_session_id, payment_data):
                st.success("☁️ Payment results saved to cloud storage")
            else:
                st.warning("⚠️ Failed to save payment results to cloud storage")
        except Exception as e:
            st.warning(f"⚠️ Cloud storage error: {e}")

    if payment_type:
        st.write(f"**Consolidated Report:** First payment detected is {payment_type}")
    else:
        st.write("**Consolidated Report:** No cash or card payment detected in the video")

    # Clear the current video session to signal completion
    if 'current_video_session' in st.session_state:
        del st.session_state.current_video_session
    
    # Clear processing state
    try:
        from app import clear_processing_state
        clear_processing_state(video_session_id)
    except:
        pass  # Ignore if function not available
    
    # Force UI refresh
    st.rerun()

    return {"total_payments": total_payments, "cash_payments": cash_payments, "card_payments": card_payments}