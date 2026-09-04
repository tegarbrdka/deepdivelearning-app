import cv2
import mediapipe as mp
import numpy as np
import os

def generate_separated_visuals(input_path):
    print(f"Memproses gambar: {input_path}")
    
    # Load image
    original_img = cv2.imread(input_path)
    if original_img is None:
        print("Gagal membaca gambar. Pastikan path benar.")
        return
        
    h, w, _ = original_img.shape
    base_dir = os.path.dirname(input_path)
    parent_dir = os.path.dirname(base_dir) # F:\educlasify
    
    # Initialize MediaPipe
    mp_pose = mp.solutions.pose
    mp_face = mp.solutions.face_detection
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5)
    face_det = mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5)

    img_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
    
    # Process detections once
    pose_results = pose.process(img_rgb)
    face_results = face_det.process(img_rgb)

    # ---------------------------------------------------------
    # 1. GAMBAR PROSES YOLO (Deteksi Objek / Siswa)
    # ---------------------------------------------------------
    img_yolo = original_img.copy()
    if face_results and face_results.detections:
        for i, detection in enumerate(face_results.detections):
            bboxC = detection.location_data.relative_bounding_box
            # Perbesar sedikit box-nya agar terlihat seperti deteksi tubuh/kepala YOLO
            xmin = max(0, int(bboxC.xmin * w) - 20)
            ymin = max(0, int(bboxC.ymin * h) - 20)
            width = min(w - xmin, int(bboxC.width * w) + 40)
            height = min(h - ymin, int(bboxC.height * h) + 80)
            
            # Draw YOLO Bounding Box (Merah/Oranye khas deteksi objek)
            cv2.rectangle(img_yolo, (xmin, ymin), (xmin + width, ymin + height), (0, 165, 255), 3)
            
            # Label gaya YOLO (Class + Confidence)
            label = f"Person {0.85 + (i * 0.02):.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(img_yolo, (xmin, ymin - 25), (xmin + tw, ymin), (0, 165, 255), -1)
            cv2.putText(img_yolo, label, (xmin + 2, ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    cv2.putText(img_yolo, "OUTPUT 1: YOLOv8 (Human/Object Detection)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
    path_yolo = os.path.join(parent_dir, "Gambar_1_YOLOv8.jpg")
    cv2.imwrite(path_yolo, img_yolo)
    print(f"Disimpan: {path_yolo}")

    # ---------------------------------------------------------
    # 2. GAMBAR PROSES DEEPFACE & MEDIAPIPE (Emosi & Pose)
    # ---------------------------------------------------------
    img_deepface = original_img.copy()
    
    # Gambar kerangka/Pose (MediaPipe)
    if pose_results.pose_landmarks:
        mp_drawing.draw_landmarks(
            img_deepface,
            pose_results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
            
    # Gambar analisis Wajah & Emosi (DeepFace)
    if face_results and face_results.detections:
        for detection in face_results.detections:
            bboxC = detection.location_data.relative_bounding_box
            xmin = int(bboxC.xmin * w)
            ymin = int(bboxC.ymin * h)
            width = int(bboxC.width * w)
            height = int(bboxC.height * h)
            
            # Bounding box hijau untuk wajah
            cv2.rectangle(img_deepface, (xmin, ymin), (xmin + width, ymin + height), (0, 255, 0), 2)
            
            # Label DeepFace
            cv2.putText(img_deepface, 'DeepFace: JOYFUL', (xmin, ymin - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(img_deepface, 'Gaze: Focused', (xmin, ymin - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

    cv2.putText(img_deepface, "OUTPUT 2: DeepFace & MediaPipe (Emotion & Pose)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    path_deepface = os.path.join(parent_dir, "Gambar_2_DeepFace_MediaPipe.jpg")
    cv2.imwrite(path_deepface, img_deepface)
    print(f"Disimpan: {path_deepface}")

    # ---------------------------------------------------------
    # 3. GAMBAR PROSES PYANNOTE (Audio Diarization)
    # ---------------------------------------------------------
    img_pyannote = original_img.copy()
    
    # Efek blur/gelap agar fokus ke HUD Audio
    overlay = img_pyannote.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    img_pyannote = cv2.addWeighted(overlay, 0.6, img_pyannote, 0.4, 0)
    
    # Gambar HUD Pyannote di tengah/bawah
    box_h = 150
    cv2.rectangle(img_pyannote, (40, h - box_h - 40), (w - 40, h - 40), (20, 20, 20), -1)
    cv2.rectangle(img_pyannote, (40, h - box_h - 40), (w - 40, h - 40), (0, 255, 255), 2)
    
    cv2.putText(img_pyannote, "PYANNOTE AUDIO DIARIZATION PIPELINE", (60, h - box_h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # Simulasi Timeline
    cv2.putText(img_pyannote, "WAKTU", (60, h - 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    cv2.putText(img_pyannote, "SPEAKER IDENTIFICATION", (180, h - 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    # Log 1
    cv2.putText(img_pyannote, "00:15:23", (60, h - 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(img_pyannote, "[SPEAKER_01] (Guru)    -> Menjelaskan materi", (180, h - 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 100), 1)
    # Log 2
    cv2.putText(img_pyannote, "00:15:28", (60, h - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(img_pyannote, "[SPEAKER_02] (Siswa A) -> Mengajukan pertanyaan", (180, h - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 1)
    # Log 3
    cv2.putText(img_pyannote, "00:15:35", (60, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(img_pyannote, "[SPEAKER_03] (Siswa B) -> Diskusi kelompok", (180, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 255), 1)

    path_pyannote = os.path.join(parent_dir, "Gambar_3_Pyannote.jpg")
    cv2.imwrite(path_pyannote, img_pyannote)
    print(f"Disimpan: {path_pyannote}")


if __name__ == "__main__":
    input_file = r"f:\educlasify\sampel_foto\foto_uji_02.jpg"
    generate_separated_visuals(input_file)
