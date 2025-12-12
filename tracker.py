import numpy as np
from collections import defaultdict


class ObjectTracker:
    def __init__(self):
        self.next_id = 1
        self.tracked_objects = {}
        self.max_disappeared = 30
        self.disappeared = defaultdict(int)

    def update(self, detections):
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    del self.tracked_objects[object_id]
                    del self.disappeared[object_id]
            return list(self.tracked_objects.values())

        input_centroids = []
        input_boxes = []
        input_classes = []

        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            input_centroids.append((cx, cy))
            input_boxes.append(det['bbox'])
            input_classes.append(det['class'])

        if len(self.tracked_objects) == 0:
            for i in range(len(input_centroids)):
                self._register(input_centroids[i], input_boxes[i], input_classes[i])
        else:
            object_ids = list(self.tracked_objects.keys())
            object_centroids = [obj['center'] for obj in self.tracked_objects.values()]

            D = np.zeros((len(object_centroids), len(input_centroids)))
            for i, oc in enumerate(object_centroids):
                for j, ic in enumerate(input_centroids):
                    D[i, j] = np.sqrt((oc[0] - ic[0]) ** 2 + (oc[1] - ic[1]) ** 2)

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                if D[row, col] > 100:
                    continue

                object_id = object_ids[row]
                self.tracked_objects[object_id]['center'] = input_centroids[col]
                self.tracked_objects[object_id]['bbox'] = input_boxes[col]
                self.disappeared[object_id] = 0

                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(D.shape[0])) - used_rows
            unused_cols = set(range(D.shape[1])) - used_cols

            for row in unused_rows:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    del self.tracked_objects[object_id]
                    del self.disappeared[object_id]

            for col in unused_cols:
                self._register(input_centroids[col], input_boxes[col], input_classes[col])

        return list(self.tracked_objects.values())

    def _register(self, centroid, bbox, obj_class):
        self.tracked_objects[self.next_id] = {
            'id': self.next_id,
            'center': centroid,
            'bbox': bbox,
            'class': obj_class
        }
        self.disappeared[self.next_id] = 0
        self.next_id += 1
