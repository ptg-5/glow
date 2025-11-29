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
        min_dist = float('inf')
        closest_tone = "Unknown"
        for tone_name, (ref_s, ref_v) in self.tone_map.items():
            dist = math.sqrt((s_val - ref_s)**2 + (v_val - ref_v)**2)
            if dist < min_dist:
                min_dist = dist
                closest_tone = tone_name
        return closest_tone

    def determine_season(self, tone_name, is_warm, contrast):
        if is_warm:
            if any(t in tone_name for t in ['Pale', 'Light']): return "Spring Light"
            if any(t in tone_name for t in ['Bright', 'Vivid']): return "Spring Bright"
            if any(t in tone_name for t in ['Strong', 'Deep']): return "Autumn Deep"
            if any(t in tone_name for t in ['Soft', 'Dull', 'Light Grayish']): return "Autumn Mute"
            return "Autumn Deep"
        else:
            if any(t in tone_name for t in ['Pale', 'Light', 'Light Grayish']): return "Summer Light"
            if any(t in tone_name for t in ['Soft', 'Grayish', 'Dull']): return "Summer Mute"
            if 'Bright' in tone_name: return "Summer Bright"
            if any(t in tone_name for t in ['Vivid', 'Strong', 'Deep', 'Dark']): return "Winter Dark"
            return "Winter Bright"

class PersonalColorSystem:
    def __init__(self):
        print(">>> [Color] 시스템 초기화 중... (Pure MediaPipe)")
        self.pccs = PCCSAnalyzer()
        
        # YOLO 로드 부분 삭제됨
        self.detector = None 

        # MediaPipe Face Mesh 설정
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,       # 비디오 스트림이거나 연속 분석이면 False 권장
            max_num_faces=1,               # 얼굴 하나만 분석
            refine_landmarks=True,         # 눈동자 등 정밀 좌표
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.TH_B_WARM = 143.0

    def get_robust_stats(self, image, center_point, radius=10, is_eyebrow=False):
        x, y = center_point
        h, w, _ = image.shape
        
        if x < 0 or x >= w or y < 0 or y >= h:
            return None

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
        
        return {
            'L': np.median(l[mask]), 'a': np.median(a[mask]), 'b': np.median(b[mask]),
            'S': np.median(s[mask]), 'V': np.median(v[mask])
        }

    def analyze_frame(self, frame):
        """
        YOLO 없이 MediaPipe로만 얼굴 찾고 분석
        """
        h, w, _ = frame.shape
        
        # 1. MediaPipe 처리 (전체 이미지)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        # 얼굴을 못 찾았으면 종료
        if not results.multi_face_landmarks:
            return None

        # 첫 번째 감지된 얼굴의 랜드마크 가져오기
        lm = results.multi_face_landmarks[0].landmark
        
        # 좌표 변환 함수 (전체 해상도 기준)
        def get_pt(idx): 
            return (int(lm[idx].x * w), int(lm[idx].y * h))

        # Bounding Box 계산 (시각화용)
        x_list = [l.x for l in lm]
        y_list = [l.y for l in lm]
        x1, y1 = int(min(x_list) * w), int(min(y_list) * h)
        x2, y2 = int(max(x_list) * w), int(max(y_list) * h)

        # 주요 포인트 추출 (양볼, 턱, 눈썹)
        pt_cheek_l = get_pt(234)
        pt_cheek_r = get_pt(454)
        pt_chin = get_pt(152)
        pt_eyebrow = get_pt(65)

        # 3. 색상 통계 추출
        s_left = self.get_robust_stats(frame, pt_cheek_l)
        s_right = self.get_robust_stats(frame, pt_cheek_r)
        s_chin = self.get_robust_stats(frame, pt_chin)
        s_eyebrow = self.get_robust_stats(frame, pt_eyebrow, radius=5, is_eyebrow=True)

        if not (s_left and s_right and s_chin and s_eyebrow): return None

        # 4. 분석 (웜/쿨 판단)
        skin_stats = {}
        for k in ['L', 'a', 'b', 'S', 'V']:
            vals = [d[k] for d in [s_left, s_right, s_chin] if d]
            skin_stats[k] = np.mean(vals)

        contrast = abs(skin_stats['L'] - s_eyebrow['L'])
        is_warm = skin_stats['b'] > self.TH_B_WARM
        pccs_tone = self.pccs.get_closest_tone(skin_stats['S'], skin_stats['V'])
        final_season = self.pccs.determine_season(pccs_tone, is_warm, contrast)

        return {
            'bbox': (x1, y1, x2, y2),
            'points': [pt_cheek_l, pt_cheek_r, pt_chin, pt_eyebrow],
            'stats': skin_stats,
            'result': final_season,
            'is_warm': is_warm
        }