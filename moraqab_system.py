import cv2
import sys
from ultralytics import YOLO
from tracker import ObjectTracker
from behavior_detector import BehaviorDetector
from alert_system import AlertSystem

class MoraqabSystem:
    def __init__(self):
        print("تهيئة نظام مرقاب...")
        print("تحميل نموذج YOLOv8n...")
        self.model = YOLO('yolov8n.pt')
        self.tracker = ObjectTracker()
        self.behavior_detector = BehaviorDetector()
        self.alert_system = AlertSystem()
        self.running = False
        print("تم تهيئة النظام بنجاح!")

    def extract_detections(self, results):
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls = int(box.cls[0])   # رقم الكلاس الحقيقي (COCO)

                if conf > 0.5:
                    detections.append({
                        'bbox': (int(x1), int(y1), int(x2), int(y2)),
                        'confidence': conf,
                        'class': cls       # إرسال رقم الكلاس
                    })
        return detections

    def draw_annotations(self, frame, tracked_objects, behaviors):
        display_frame = frame.copy()

        for obj in tracked_objects:
            x1, y1, x2, y2 = obj['bbox']
            cx, cy = obj['center']

            color = (0, 255, 0)
            if obj['class'] == 0:   # 0 = person
                color = (255, 0, 0)

            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(display_frame, (cx, cy), 5, color, -1)
            cv2.putText(display_frame, f"ID:{obj['id']}",
                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        for i, behavior in enumerate(behaviors):
            y_pos = 30 + (i * 30)
            behavior_names = {
                'fighting': 'شجار',
                'fire': 'حريق',
                'fall': 'سقوط',
                'crowd': 'تجمع'
            }
            text = f"{behavior_names.get(behavior['type'], behavior['type'])}"
            cv2.putText(display_frame, text, (10, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        return display_frame

    def stop(self):
        self.running = False
