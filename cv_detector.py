import cv2
import numpy as np
import time
import argparse
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser(description="SmartLight CV Perception Pipeline")
    parser.add_argument("--input", type=str, default="traffic.mp4", help="Path to input traffic video")
    parser.add_argument("--output", type=str, default="processed_traffic.mp4", help="Path to save processed video")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="YOLOv8 model weight")
    parser.add_argument("--no-display", action="store_true", help="Disable GUI display window")
    args = parser.parse_args()

    # Load YOLOv8 model
    print(f"Loading YOLOv8 model: {args.model}...")
    model = YOLO(args.model)
    # COCO Class IDs for vehicles: 2 (car), 3 (motorcycle), 5 (bus), 7 (truck)
    VEHICLE_CLASSES = [2, 3, 5, 7]
    class_names = {2: "Car", 3: "Moto", 5: "Bus", 7: "Truck"}

    # Open video capture
    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        print(f"Error: Could not open input video {args.input}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or cap.get(3))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or cap.get(4))
    fps = cap.get(cv2.CAP_PROP_FPS) or cap.get(5)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or cap.get(7))
    print(f"Video loaded: {width}x{height} @ {fps:.2f} FPS ({total_frames} total frames)")

    # Define normalized ROIs for lanes (polygons)
    # Left Lane (Lane 1), Middle Lane (Lane 2), Right Lane (Lane 3)
    # Scaled as percentage of width (x) and height (y)
    normalized_rois = {
        "Lane_Left": np.array([[0.05, 0.95], [0.28, 0.45], [0.42, 0.45], [0.18, 0.95]], dtype=np.float32),
        "Lane_Center": np.array([[0.25, 0.95], [0.44, 0.45], [0.52, 0.45], [0.58, 0.95]], dtype=np.float32),
        "Lane_Right": np.array([[0.65, 0.95], [0.54, 0.45], [0.65, 0.45], [0.95, 0.95]], dtype=np.float32)
    }

    # Denormalize ROIs to pixel coordinates
    rois = {}
    for name, norm_poly in normalized_rois.items():
        pixel_poly = (norm_poly * [width, height]).astype(np.int32)
        rois[name] = pixel_poly

    # Output video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output, fourcc, fps, (width, height))

    # Color Palette (harmonious RGB colors)
    COLORS = {
        "Lane_Left": (67, 181, 75),      # Green
        "Lane_Center": (60, 162, 230),    # Soft Gold
        "Lane_Right": (255, 158, 64),     # Light Blue/Teal
        "Default": (178, 171, 168)        # Muted Gray
    }

    frame_count = 0
    total_processing_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        start_time = time.time()
        frame_count += 1

        # Create overlay for transparent ROI polygons
        overlay = frame.copy()
        for name, poly in rois.items():
            cv2.fillPoly(overlay, [poly], COLORS[name])
        # Blend overlay (alpha = 0.25)
        cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)

        # Draw ROI borders
        for name, poly in rois.items():
            cv2.polylines(frame, [poly], isClosed=True, color=COLORS[name], thickness=2)

        # Run YOLOv8 detection
        results = model(frame, verbose=False)[0]

        # Initialize counts for this frame
        counts = {name: 0 for name in rois.keys()}

        # Process detections
        for box in results.boxes:
            cls_id = int(box.cls[0].item())
            if cls_id not in VEHICLE_CLASSES:
                continue

            conf = box.conf[0].item()
            # Bounding box coordinates
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, xyxy)

            # Center bottom point of the bounding box
            cx = (x1 + x2) // 2
            cy = y2

            # Determine which ROI the vehicle is in
            assigned_lane = None
            for name, poly in rois.items():
                if cv2.pointPolygonTest(poly, (float(cx), float(cy)), False) >= 0:
                    assigned_lane = name
                    counts[name] += 1
                    break

            # Draw bounding box and label
            color = COLORS[assigned_lane] if assigned_lane else COLORS["Default"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw contact point
            cv2.circle(frame, (cx, cy), 5, color, -1)

            # Text label
            label = f"{class_names[cls_id]} {conf:.2f}"
            cv2.putText(frame, label, (x1, max(y1 - 8, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

        # End timer for speed calculation
        end_time = time.time()
        processing_time = end_time - start_time
        total_processing_time += processing_time
        current_fps = 1.0 / processing_time if processing_time > 0 else 0

        # Draw HUD (Heads-Up Display)
        # Background card for counts (top-left)
        hud_bg = frame.copy()
        cv2.rectangle(hud_bg, (10, 10), (320, 210), (20, 20, 20), -1)
        cv2.addWeighted(hud_bg, 0.75, frame, 0.25, 0, frame)

        # Title
        cv2.putText(frame, "SmartLight Perception MVP", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.line(frame, (20, 45), (310, 45), (100, 100, 100), 1)

        # Counts
        y_offset = 75
        for name, count in counts.items():
            cv2.putText(frame, f"{name.replace('_', ' ')}:", (25, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1, cv2.LINE_AA)
            cv2.putText(frame, f"{count}", (180, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLORS[name], 2, cv2.LINE_AA)
            y_offset += 30

        # Stats
        cv2.line(frame, (20, y_offset - 10), (310, y_offset - 10), (100, 100, 100), 1)
        cv2.putText(frame, f"FPS: {current_fps:.1f}", (25, y_offset + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Frame: {frame_count}/{total_frames}", (150, y_offset + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

        # Save processed frame
        out.write(frame)

        # Show GUI if enabled
        if not args.no_display:
            cv2.imshow("SmartLight CV Pipeline", frame)
            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # Clean up
    cap.release()
    out.release()
    if not args.no_display:
        cv2.destroyAllWindows()

    avg_fps = frame_count / total_processing_time if total_processing_time > 0 else 0
    print(f"\nProcessing Complete!")
    print(f"Processed video saved to: {args.output}")
    print(f"Total Frames Processed: {frame_count}")
    print(f"Average Processing Speed: {avg_fps:.2f} FPS")

if __name__ == "__main__":
    main()
