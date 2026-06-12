import cv2
import numpy as np
import json
import sqlite3
import datetime
from ultralytics import YOLO

### 1. MEMUAT DATA MAPPING (JSON) & TANGGAPAN GARIS MASUK ###
try:
    with open('koordinat_parkir_3.json', 'r') as f:
        data_mapping = json.load(f)
except FileNotFoundError:
    print("Error: File koordinat_parkir_3.json tidak ditemukan. Jalankan mapping.py terlebih dahulu.")
    exit()

area_parkir_list = [np.array(area, np.int32) for area in data_mapping['petak_parkir']]
jumlah_petak = len(area_parkir_list)
print(f"Sistem siap memantau {jumlah_petak} petak parkir.")

# Mendapatkan garis masuk (entry line) untuk perhitungan
if 'garis_masuk' in data_mapping and len(data_mapping['garis_masuk']) == 2:
    garis_masuk = [tuple(p) for p in data_mapping['garis_masuk']]
else:
    garis_masuk = [(200, 550), (800, 550)]

# Helper untuk memeriksa tabrakan/persilangan garis (Line Crossing)
def ccw(A, B, C):
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def intersect(A, B, C, D):
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

### 2. INISIALISASI MODEL & VIDEO ###
model = YOLO('yolov8n.pt')
cap = cv2.VideoCapture('video_parkir.mp4') 
kelas_kendaraan = [2, 3, 5, 7] # 2: Mobil, 3: Motor, 5: Bus, 7: Truk

### 3. PENGATURAN LOGIKA TEMPORAL & JENDELA TAMPILAN ###
batas_waktu_frame = 30
tracker_waktu = {i: 0 for i in range(jumlah_petak)}
status_akhir = {i: "KOSONG" for i in range(jumlah_petak)}

# Inisialisasi pelacakan kendaraan masuk
posisi_sebelumnya = {}   # track_id -> (cx, cy)
kendaraan_terhitung = set() # Set ID kendaraan yang sudah dihitung masuk
total_masuk = 0

# Memuat total_masuk sebelumnya dari database
try:
    conn = sqlite3.connect('parkir.db')
    cursor = conn.cursor()
    cursor.execute("SELECT total_masuk FROM status_kamera WHERE id_kamera = 'Kamera_03'")
    row = cursor.fetchone()
    if row is not None and row[0] is not None:
        total_masuk = row[0]
    conn.close()
except Exception as e:
    print(f"Gagal memuat total_masuk dari database: {e}")

# Membuat jendela tampilan yang bisa diubah ukurannya (resizeable)
nama_jendela = "Smart Parking (Kamera 03)"
cv2.namedWindow(nama_jendela, cv2.WINDOW_NORMAL)
cv2.resizeWindow(nama_jendela, 800, 600) 

### 4. LOOPING PEMROSESAN VIDEO ###
while True:
    ret, frame = cap.read()
    if not ret:
        # Loop video kembali ke frame pertama untuk simulasi berkelanjutan
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        posisi_sebelumnya.clear()
        kendaraan_terhitung.clear()
        continue
        
    frame = cv2.resize(frame, (1024, 768))
    kendaraan_di_petak = {i: False for i in range(jumlah_petak)}
    
    # Deteksi & Tracking AI
    results = model.track(frame, persist=True, stream=True, verbose=False)
    
    for r in results:
        boxes = r.boxes
        if boxes is not None:
            xyxy = boxes.xyxy.cpu().numpy() if boxes.xyxy is not None else []
            cls = boxes.cls.cpu().numpy() if boxes.cls is not None else []
            ids = boxes.id.cpu().numpy() if boxes.id is not None else [None] * len(xyxy)
            
            for idx, box_coords in enumerate(xyxy):
                cls_id = int(cls[idx])
                if cls_id in kelas_kendaraan:
                    x1, y1, x2, y2 = map(int, box_coords)
                    cx = int((x1 + x2) / 2)
                    cy = int(y2) # Titik ban menyentuh aspal
                    
                    # Visualisasi titik kuning untuk kalibrasi mapping
                    cv2.circle(frame, (cx, cy), 8, (0, 255, 255), -1) 
                    
                    # Cek perpotongan titik ban dengan poligon parkir
                    for i, area in enumerate(area_parkir_list):
                        hasil_cek = cv2.pointPolygonTest(area, (cx, cy), False)
                        if hasil_cek >= 0:
                            kendaraan_di_petak[i] = True
                            break 
                    
                    # Cek Garis Masuk (Line Crossing) jika tracker ID tersedia
                    track_id = int(ids[idx]) if ids[idx] is not None else None
                    if track_id is not None:
                        if track_id in posisi_sebelumnya:
                            prev_cx, prev_cy = posisi_sebelumnya[track_id]
                            # Jika memotong garis masuk
                            if intersect((prev_cx, prev_cy), (cx, cy), garis_masuk[0], garis_masuk[1]):
                                if track_id not in kendaraan_terhitung:
                                    kendaraan_terhitung.add(track_id)
                                    total_masuk += 1
                                    print(f"[Kamera 03] Kendaraan masuk! ID: {track_id}, Total: {total_masuk}")
                        # Simpan posisi terbaru
                        posisi_sebelumnya[track_id] = (cx, cy)

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

    # Gambar Garis Masuk (Magenta) di Video
    cv2.line(frame, garis_masuk[0], garis_masuk[1], (255, 0, 255), 3)
    cv2.putText(frame, "ENTRY LINE", (garis_masuk[0][0], garis_masuk[0][1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

    ### 6. PENGIRIMAN DATA KE DATABASE SQLITE ###
    try:
        conn = sqlite3.connect('parkir.db')
        cursor = conn.cursor()
        waktu_sekarang = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Sertakan total_masuk saat update agar tidak di-overwrite menjadi 0 atau default
        cursor.execute('''
        INSERT OR REPLACE INTO status_kamera (id_kamera, total_kosong, total_terisi, total_masuk, waktu_update)
        VALUES ('Kamera_03', ?, ?, ?, ?)
        ''', (total_kosong, total_terisi, total_masuk, waktu_sekarang))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Terjadi kesalahan database: {e}")

    ### 7. DASHBOARD OVERLAY DI VIDEO ###
    cv2.rectangle(frame, (20, 20), (450, 150), (0, 0, 0), -1)
    cv2.putText(frame, f"TOTAL PETAK PANTAU: {jumlah_petak}", (35, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"KOSONG: {total_kosong}  |  TERISI: {total_terisi}", (35, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(frame, f"TOTAL MASUK: {total_masuk}", (35, 130), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow(nama_jendela, frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()