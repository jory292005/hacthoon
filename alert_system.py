import cv2
import os
from datetime import datetime
import pygame

class AlertSystem:
    def __init__(self, output_dir="alerts"):
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "images")
        self.videos_dir = os.path.join(output_dir, "videos")
        
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)
        
        pygame.mixer.init()
        self.alert_sound = None
        try:
            self.alert_sound = pygame.mixer.Sound("alert.wav")
        except:
            pass
        
        self.video_buffer = []
        self.buffer_size = 150
        self.alert_count = 0
        
        self.severity_colors = {
            'critical': (0, 0, 255),
            'medium': (0, 165, 255),
            'low': (0, 255, 255)
        }
        
        self.behavior_names = {
            'fighting': 'شجار',
            'fire': 'حريق',
            'fall': 'سقوط/حادث',
            'crowd': 'تجمع مشبوه'
        }
    
    def trigger_alert(self, behavior, frame):
        self.alert_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        behavior_type = behavior['type']
        
        self._play_sound()
        image_path = self._save_image(frame, behavior, timestamp)
        video_path = self._save_video(behavior, timestamp)
        
        return {
            'image': image_path,
            'video': video_path,
            'behavior': behavior,
            'timestamp': timestamp
        }
    
    def _play_sound(self):
        if self.alert_sound:
            try:
                self.alert_sound.play()
            except:
                pass
    
    def _save_image(self, frame, behavior, timestamp):
        annotated_frame = frame.copy()
        
        behavior_type = behavior['type']
        severity = behavior.get('severity', 'medium')
        location = behavior.get('location', (0, 0))
        details = behavior.get('details', '')
        
        color = self.severity_colors.get(severity, (0, 255, 0))
        behavior_name = self.behavior_names.get(behavior_type, behavior_type)
        
        cv2.circle(annotated_frame, location, 15, color, -1)
        cv2.rectangle(annotated_frame, 
                     (location[0]-60, location[1]-60),
                     (location[0]+60, location[1]+60),
                     color, 4)
        
        y_offset = 40
        cv2.putText(annotated_frame, f"{behavior_name}", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
        y_offset += 40
        cv2.putText(annotated_frame, f"Severity: {severity}", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        y_offset += 35
        cv2.putText(annotated_frame, f"{details}", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        filename = f"{behavior_type}_{timestamp}.jpg"
        filepath = os.path.join(self.images_dir, filename)
        cv2.imwrite(filepath, annotated_frame)
        
        return filepath
    
    def _save_video(self, behavior, timestamp):
        if len(self.video_buffer) < 30:
            return None
        
        behavior_type = behavior['type']
        filename = f"{behavior_type}_{timestamp}.mp4"
        filepath = os.path.join(self.videos_dir, filename)
        
        frame_height, frame_width = self.video_buffer[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filepath, fourcc, 30, (frame_width, frame_height))
        
        for frame in self.video_buffer[-150:]:
            out.write(frame)
        
        out.release()
        return filepath
    
    def add_frame_to_buffer(self, frame):
        self.video_buffer.append(frame.copy())
        if len(self.video_buffer) > self.buffer_size:
            self.video_buffer.pop(0)
    
    def get_alert_count(self):
        return self.alert_count
    
    def reset_count(self):
        self.alert_count = 0
