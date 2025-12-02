import cv2
import numpy as np
import mediapipe as mp
import math

class PCCSAnalyzer:
    def __init__(self):
        self.tone_map = {
            'Pale': (30, 240), 'Light': (60, 220), 'Bright': (130, 200), 'Vivid': (180, 180),
            'Soft': (60, 170), 'Dull': (100, 140), 'Strong': (160, 150),
            'Light Grayish': (30, 190), 'Grayish': (30, 120),
            'Dark': (90, 80), 'Deep': (160, 60), 'Dark Grayish': (40, 50)
        }

    def get_closest_tone(self, s_val, v_val):
        return min(self.tone_map, key=lambda k: math.hypot(s_val-self.tone_map[k][0], v_val-self.tone_map[k][1]))

    def determine_season(self, tone_name, is_warm, contrast):
        base = "Warm" if is_warm else "Cool"
        if is_warm:
            if any(t in tone_name for t in ['Pale', 'Light']): return f"Spring Light"
            if any(t in tone_name for t in ['Bright', 'Vivid']): return f"Spring Bright"
            if any(t in tone_name for t in ['Strong', 'Deep']): return f"Autumn Deep"
            if any(t in tone_name for t in ['Soft', 'Dull', 'Light Grayish']): return f"Autumn Mute"
            return f"Autumn Deep"
        else:
            if any(t in tone_name for t in ['Pale', 'Light', 'Light Grayish']): return f"Summer Light"
            if any(t in tone_name for t in ['Soft', 'Grayish', 'Dull']): return f"Summer Mute"
            if 'Bright' in tone_name: return f"Summer Bright"
            if any(t in tone_name for t in ['Vivid', 'Strong', 'Deep', 'Dark']): return f"Winter Dark"
            return f"Winter Bright"

class PersonalColorSystem:
    def __init__(self):
        self.pccs = PCCSAnalyzer()
        
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False, # [중요] 실시간 비디오용 설정
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.TH_B_WARM = 138.0 

    def get_robust_stats(self, image, center_point, radius=10, is_eyebrow=False):
        x, y = center_point
        h, w, _ = image.shape
        x_min, x_max = max(0, x-radius), min(w, x+radius)
        y_min, y_max = max(0, y-radius), min(h, y+radius)
        roi = image[y_min:y_max, x_min:x_max]
        if roi.size == 0: return None

        lab_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2Lab)
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        l, a, b = cv2.split(lab_roi)
        hh, s, v = cv2.split(hsv_roi)
        
        mask = np.ones_like(l, dtype=bool)
        if not is_eyebrow:
            median_a = np.median(a)
            mask = np.abs(a - median_a) < 10 
        if np.sum(mask) < 5: mask[:] = True
        
        return {'L': np.median(l[mask]), 'b': np.median(b[mask]), 'S': np.median(s[mask]), 'V': np.median(v[mask])}

    def analyze_frame(self, frame):
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks: return None

        lm = results.multi_face_landmarks[0].landmark
        def get_pt(idx): return (int(lm[idx].x * w), int(lm[idx].y * h))

        xs = [l.x for l in lm]; ys = [l.y for l in lm]
        x1, y1 = int(min(xs)*w), int(min(ys)*h)
        x2, y2 = int(max(xs)*w), int(max(ys)*h)

        points = [get_pt(234), get_pt(454), get_pt(152), get_pt(65)]
        
        s_left = self.get_robust_stats(frame, points[0])
        s_right = self.get_robust_stats(frame, points[1])
        s_chin = self.get_robust_stats(frame, points[2])
        s_eyebrow = self.get_robust_stats(frame, points[3], radius=5, is_eyebrow=True)

        if not (s_left and s_right and s_chin and s_eyebrow): return None

        skin_stats = {}
        for k in ['L', 'b', 'S', 'V']:
            vals = [d[k] for d in [s_left, s_right, s_chin] if d]
            skin_stats[k] = np.mean(vals)

        contrast = abs(skin_stats['L'] - s_eyebrow['L'])
        is_warm = skin_stats['b'] > self.TH_B_WARM
        pccs_tone = self.pccs.get_closest_tone(skin_stats['S'], skin_stats['V'])
        final_season = self.pccs.determine_season(pccs_tone, is_warm, contrast)

        return {
            'bbox': (x1, y1, x2, y2),
            'points': points,
            'result': final_season,
            'is_warm': is_warm,
            'stats': skin_stats
        }