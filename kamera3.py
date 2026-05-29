import cv2
import numpy as np
import json
import sqlite3
import datetime
from ultralytics import YOLO

### 1. MEMUAT DATA MAPPING (JSON) ###
try:
    with open('koordinat_parkir_3.json', 'r') as f:
        data_mapping = json.load(f)
except FileNotFoundError:
    print("Error: File koordinat_parkir.json tidak ditemukan. Jalankan mapping.py terlebih dahulu.")
    exit()

area_parkir_list = [np.array(area, np.int32) for area in data_mapping['petak_parkir']]
jumlah_petak = len(area_parkir_list)
print(f"Sistem siap memantau {jumlah_petak} petak parkir.")

### 2. INISIALISASI MODEL & VIDEO ###
model = YOLO('yolov8n.pt')
cap = cv2.VideoCapture('video_parkir.mp4') 
kelas_kendaraan = [2, 3, 5, 7] # 2: Mobil, 3: Motor, 5: Bus, 7: Truk

### 3. PENGATURAN LOGIKA TEMPORAL & JENDELA TAMPILAN ###
batas_waktu_frame = 30
tracker_waktu = {i: 0 for i in range(jumlah_petak)}
status_akhir = {i: "KOSONG" for i in range(jumlah_petak)}

# Membuat jendela tampilan yang bisa diubah ukurannya (resizeable)
nama_jendela = "Smart Parking (Kamera 03)"
cv2.namedWindow(nama_jendela, cv2.WINDOW_NORMAL)
# Atur ukuran jendela yang muncul di layar monitor (bebas disesuaikan)
cv2.resizeWindow(nama_jendela, 800, 600) 

### 4. LOOPING PEMROSESAN VIDEO ###
while True:
    ret, frame = cap.read()
    if not ret:
        print("Video selesai diputar.")
        break
        
    # PENTING: Resolusi ini (1024x768) TIDAK BOLEH diubah agar koordinat json tetap akurat
    frame = cv2.resize(frame, (1024, 768))
    kendaraan_di_petak = {i: False for i in range(jumlah_petak)}
    
    # Deteksi AI
    results = model.predict(frame, stream=True, verbose=False)
    
    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            
            if cls_id in kelas_kendaraan:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx = int((x1 + x2) / 2)
                cy = int(y2) # Titik ban menyentuh aspal
                
                # Visualisasi titik kuning untuk kalibrasi mapping
                cv2.circle(frame, (cx, cy), 8, (0, 255, 255), -1) 
                
                # Cek perpotongan titik ban dengan poligon
                for i, area in enumerate(area_parkir_list):
                    hasil_cek = cv2.pointPolygonTest(area, (cx, cy), False)
                    if hasil_cek >= 0:
                        kendaraan_di_petak[i] = True
                        break 

    ### 5. EVALUASI TIMER & VISUALISASI PER PETAK ###
    total_kosong = 0
    total_terisi = 0
    
    for i, area in enumerate(area_parkir_list):
        if kendaraan_di_petak[i]:
            tracker_waktu[i] += 1
        else:
            tracker_waktu[i] = 0
            
        if tracker_waktu[i] >= batas_waktu_frame:
            status_akhir[i] = "TERISI"
            warna_petak = (0, 0, 255) # Merah
            total_terisi += 1
        else:
            status_akhir[i] = "KOSONG"
            warna_petak = (0, 255, 0) # Hijau
            total_kosong += 1
            
        cv2.polylines(frame, [area], isClosed=True, color=warna_petak, thickness=2)
        cv2.putText(frame, f"P{i+1}", (area[0][0], area[0][1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, warna_petak, 2)

    ### 6. PENGIRIMAN DATA KE DATABASE SQLITE ###
    try:
        conn = sqlite3.connect('parkir.db')
        cursor = conn.cursor()
        waktu_sekarang = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Menggunakan INSERT OR REPLACE agar tahan banting jika baris belum ada
        cursor.execute('''
        INSERT OR REPLACE INTO status_kamera (id_kamera, total_kosong, total_terisi, waktu_update)
        VALUES ('Kamera_03', ?, ?, ?)
        ''', (total_kosong, total_terisi, waktu_sekarang))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Terjadi kesalahan database: {e}")

    ### 7. DASHBOARD OVERLAY DI VIDEO ###
    cv2.rectangle(frame, (20, 20), (450, 110), (0, 0, 0), -1)
    cv2.putText(frame, f"TOTAL PETAK PANTAU: {jumlah_petak}", (35, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"KOSONG: {total_kosong}  |  TERISI: {total_terisi}", (35, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Menggunakan nama_jendela yang sudah diset di atas
    cv2.imshow(nama_jendela, frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()