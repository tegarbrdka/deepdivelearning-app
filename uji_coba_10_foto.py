import os
import cv2
import csv
import sys
from deepface import DeepFace

video_path = r"f:\educlasify\backend\uploads\video_3m\f5d796c7-b58d-4dfe-8221-79e2a4a81f2c_0604(10).mp4"
output_dir = r"f:\educlasify\sampel_foto"
csv_path = r"f:\educlasify\hasil_tebakan_ai.csv"

os.makedirs(output_dir, exist_ok=True)

print("1. Mengekstrak 10 frame acak dari video...")
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print(f"Error: Tidak bisa membuka video {video_path}")
    sys.exit()

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
step = max(1, total_frames // 11)  # Bagi menjadi 11 bagian agar dapat 10 frame di tengah

extracted_files = []
for i in range(1, 11):
    frame_idx = i * step
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if ret:
        filename = f"foto_uji_{i:02d}.jpg"
        filepath = os.path.join(output_dir, filename)
        cv2.imwrite(filepath, frame)
        extracted_files.append(filename)

cap.release()
print(f"Berhasil mengekstrak {len(extracted_files)} foto ke folder {output_dir}")

print("\n2. Memulai proses ujian AI (DeepFace)...")
hasil_ujian = []

for filename in extracted_files:
    filepath = os.path.join(output_dir, filename)
    try:
        # Kita set enforce_detection=False agar tidak error jika wajah ngeblur
        analisis = DeepFace.analyze(img_path=filepath, actions=['emotion'], enforce_detection=False, silent=True)
        
        # DeepFace mereturn list jika mendeteksi banyak wajah, kita ambil wajah yang paling besar/pertama
        if isinstance(analisis, list):
            analisis = analisis[0]
            
        tebakan_ai = analisis['dominant_emotion']
        hasil_ujian.append([filename, tebakan_ai, "", ""])
        print(f" - {filename} ditebak: {tebakan_ai}")
    except Exception as e:
        hasil_ujian.append([filename, f"Gagal Deteksi", "", ""])
        print(f" - {filename}: Gagal dideteksi")

print("\n3. Menyimpan hasil ke CSV...")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Nama Foto", "Tebakan AI (Dominan)", "Kunci Jawaban Manual (Isi Sendiri)", "Status (Benar/Salah)"])
    writer.writerows(hasil_ujian)

print(f"\n✅ Uji coba selesai! Silakan buka folder f:\\educlasify\\sampel_foto untuk melihat 10 gambarnya.")
print(f"✅ Dan buka file f:\\educlasify\\hasil_tebakan_ai.csv untuk mengisi jawabannya!")
