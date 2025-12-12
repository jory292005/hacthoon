import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import threading
from moraqab_system import MoraqabSystem

class MoraqabGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("نظام مرقاب - Moraqab System")
        self.root.geometry("1200x800")
        
        self.system = MoraqabSystem()
        self.video_thread = None
        self.running = False
        self.current_frame = None
        
        self.create_widgets()
        
    def create_widgets(self):
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(control_frame, text="📁 اختيار ملف فيديو", 
                  command=self.select_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📹 تشغيل الكاميرا", 
                  command=self.start_camera).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏹ إيقاف", 
                  command=self.stop_processing).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="✅ جاهز", font=('Arial', 11, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        video_frame = ttk.Frame(self.root)
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.video_label = ttk.Label(video_frame, background='black')
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        info_frame = ttk.Frame(self.root, padding="10")
        info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        
        ttk.Label(info_frame, text="📊 إحصائيات النظام", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        self.stats_text = tk.Text(info_frame, width=35, height=12, 
                                 font=('Arial', 10), bg='#f0f0f0')
        self.stats_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(info_frame, text="🚨 التنبيهات المكتشفة", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        self.alerts_text = tk.Text(info_frame, width=35, height=18, 
                                  font=('Arial', 9), bg='#fff5f5')
        self.alerts_text.pack(fill=tk.BOTH, expand=True)
        
        self._update_initial_stats()
        
    def _update_initial_stats(self):
        stats = """
السلوكيات المراقبة:

🥊 شجار - قرب شديد مع حركة
🔥 حريق - كشف ألوان نارية
💥 سقوط/حادث - توقف مفاجئ
👥 تجمع مشبوه - تجمع كبير

الحالة: في انتظار الفيديو...
        """
        self.stats_text.insert(1.0, stats)
        
    def select_video(self):
        filepath = filedialog.askopenfilename(
            title="اختر ملف فيديو",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.webm")]
        )
        if filepath:
            self.start_processing(filepath)
    
    def start_camera(self):
        self.start_processing(0)
    
    def start_processing(self, source):
        if self.running:
            messagebox.showwarning("تحذير", "النظام يعمل بالفعل")
            return
        
        self.running = True
        self.status_label.config(text="⚙️ جاري المعالجة...")
        self.alerts_text.delete(1.0, tk.END)
        self.video_thread = threading.Thread(target=self.process_video, args=(source,))
        self.video_thread.daemon = True
        self.video_thread.start()
    
    def process_video(self, source):
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            self.status_label.config(text="❌ خطأ: لا يمكن فتح المصدر")
            self.running = False
            return
        
        frame_count = 0
        alert_count = 0
        behavior_counts = {'fighting': 0, 'fire': 0, 'fall': 0, 'crowd': 0}
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            self.system.alert_system.add_frame_to_buffer(frame)
            
            results = self.system.model(frame, verbose=False)
            detections = self.system.extract_detections(results)
            tracked_objects = self.system.tracker.update(detections)
            behaviors = self.system.behavior_detector.detect_behaviors(tracked_objects, frame)
            
            for behavior in behaviors:
                alert_count += 1
                behavior_type = behavior['type']
                if behavior_type in behavior_counts:
                    behavior_counts[behavior_type] += 1
                self.system.alert_system.trigger_alert(behavior, frame)
                self.add_alert(behavior)
            
            display_frame = self.system.draw_annotations(frame, tracked_objects, behaviors)
            self.update_video_display(display_frame)
            self.update_stats(frame_count, alert_count, len(tracked_objects), behavior_counts)
        
        cap.release()
        self.running = False
        self.status_label.config(text="⏹ متوقف")
    
    def update_video_display(self, frame):
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (800, 600))
            img = Image.fromarray(frame_resized)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        except:
            pass
    
    def update_stats(self, frames, alerts, objects, behavior_counts):
        self.stats_text.delete(1.0, tk.END)
        stats = f"""
📊 الإحصائيات:

الإطارات المعالجة: {frames}
إجمالي التنبيهات: {alerts}
الكائنات المتتبعة: {objects}

🔍 التنبيهات حسب النوع:

🥊 شجار: {behavior_counts.get('fighting', 0)}
🔥 حريق: {behavior_counts.get('fire', 0)}
💥 سقوط/حادث: {behavior_counts.get('fall', 0)}
👥 تجمع مشبوه: {behavior_counts.get('crowd', 0)}
        """
        self.stats_text.insert(1.0, stats)
    
    def add_alert(self, behavior):
        behavior_names = {
            'fighting': '🥊 شجار',
            'fire': '🔥 حريق',
            'fall': '💥 سقوط/حادث',
            'crowd': '👥 تجمع مشبوه'
        }
        
        behavior_name = behavior_names.get(behavior['type'], behavior['type'])
        severity_emoji = '🔴' if behavior['severity'] == 'critical' else '🟡'
        alert_text = f"{severity_emoji} {behavior_name}\n   {behavior.get('details', '')}\n\n"
        
        self.alerts_text.insert(1.0, alert_text)
        
        lines = self.alerts_text.get(1.0, tk.END).split('\n')
        if len(lines) > 30:
            self.alerts_text.delete(f"{len(lines)-30}.0", tk.END)
    
    def stop_processing(self):
        self.running = False
        self.system.stop()
        self.status_label.config(text="⏹ متوقف")

def main():
    root = tk.Tk()
    app = MoraqabGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
