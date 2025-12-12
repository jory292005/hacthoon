import cv2
import numpy as np
from collections import defaultdict

class BehaviorDetector:
    def __init__(self):
        self.person_history = defaultdict(list)
        self.last_positions = {}
        self.speeds = {}
        self.frame_count = 0
        self.alert_cooldown = {}
        self.cooldown_frames = 30
        self.vehicle_classes = [2, 3, 5, 7]

    def detect_behaviors(self, tracked_objects, frame):
        behaviors = []
        self.frame_count += 1

        persons = [obj for obj in tracked_objects if obj['class'] == 0]
        vehicles = [obj for obj in tracked_objects if obj['class'] in self.vehicle_classes]

        behaviors.extend(self._detect_fighting(persons))
        behaviors.extend(self._detect_fire(frame))
        behaviors.extend(self._detect_fall(persons, vehicles))
        behaviors.extend(self._detect_crowd(persons))

        for obj in tracked_objects:
            self.last_positions[obj['id']] = obj['center']

        return self._filter_cooldown(behaviors)

    def _detect_fighting(self, persons):
        behaviors = []

        for i, p1 in enumerate(persons):
            x1, y1 = p1['center']
            pid1 = p1['id']

            for p2 in persons[i+1:]:
                x2, y2 = p2['center']
                pid2 = p2['id']
                distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)

                if distance < 100:
                    if pid1 in self.last_positions and pid2 in self.last_positions:
                        prev_x1, prev_y1 = self.last_positions[pid1]
                        prev_x2, prev_y2 = self.last_positions[pid2]
                        speed1 = np.sqrt((x1 - prev_x1)**2 + (y1 - prev_y1)**2)
                        speed2 = np.sqrt((x2 - prev_x2)**2 + (y2 - prev_y2)**2)

                        if (speed1 > 20 or speed2 > 20) and distance < 80:
                            behaviors.append({
                                'type': 'fighting',
                                'severity': 'critical',
                                'location': ((x1 + x2)//2, (y1 + y2)//2),
                                'details': f'{distance:.0f}px, {max(speed1, speed2):.0f}px/s',
                                'key': f'fighting_{pid1}_{pid2}'
                            })

        return behaviors

    def _detect_fire(self, frame):
        behaviors = []
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        lower_orange = np.array([10, 100, 100])
        upper_orange = np.array([25, 255, 255])

        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)

        fire_mask = cv2.bitwise_or(mask_red1, mask_red2)
        fire_mask = cv2.bitwise_or(fire_mask, mask_orange)

        fire_pixels = cv2.countNonZero(fire_mask)
        total_pixels = frame.shape[0] * frame.shape[1]
        fire_ratio = fire_pixels / total_pixels

        if fire_pixels > 2000 and fire_ratio > 0.01:
            contours, _ = cv2.findContours(fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    cx, cy = frame.shape[1] // 2, frame.shape[0] // 2

                behaviors.append({
                    'type': 'fire',
                    'severity': 'critical',
                    'location': (cx, cy),
                    'details': f'{fire_pixels}, {fire_ratio*100:.1f}%',
                    'key': 'fire_detected'
                })

        return behaviors

    def _detect_fall(self, persons, vehicles):
        behaviors = []

        for person in persons:
            pid = person['id']
            px, py = person['center']

            for vehicle in vehicles:
                vx, vy = vehicle['center']
                distance = np.sqrt((px - vx)**2 + (py - vy)**2)

                if distance < 160:
                    behaviors.append({
                        'type': 'fall',
                        'severity': 'critical',
                        'location': (px, py),
                        'details': f'{distance:.0f}px',
                        'key': f'car_hit_{pid}'
                    })

            if pid in self.last_positions:
                prev_x, prev_y = self.last_positions[pid]
                speed = np.sqrt((px - prev_x)**2 + (py - prev_y)**2)

                if pid in self.speeds:
                    prev_speed = self.speeds[pid]
                    if prev_speed > 80 and speed < 20:
                        behaviors.append({
                            'type': 'fall',
                            'severity': 'critical',
                            'location': (px, py),
                            'details': f'{prev_speed:.0f}->{speed:.0f}',
                            'key': f'fall_{pid}'
                        })

                self.speeds[pid] = speed

        return behaviors

    def _detect_crowd(self, persons):
        behaviors = []
        if len(persons) >= 6:
            positions = [p['center'] for p in persons]

            for i, pos1 in enumerate(positions):
                x1, y1 = pos1
                nearby = 0

                for j, pos2 in enumerate(positions):
                    if i != j:
                        x2, y2 = pos2
                        distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                        if distance < 150:
                            nearby += 1

                if nearby >= 4:
                    behaviors.append({
                        'type': 'crowd',
                        'severity': 'medium',
                        'location': (x1, y1),
                        'details': str(len(persons)),
                        'key': 'crowd_detected'
                    })
                    break

        return behaviors

    def _filter_cooldown(self, behaviors):
        filtered = []

        for behavior in behaviors:
            key = behavior.get('key', behavior['type'])

            if key not in self.alert_cooldown:
                self.alert_cooldown[key] = self.frame_count
                filtered.append(behavior)
            elif self.frame_count - self.alert_cooldown[key] > self.cooldown_frames:
                self.alert_cooldown[key] = self.frame_count
                filtered.append(behavior)

        return filtered
