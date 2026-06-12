import cv2
import numpy as np
import json
import sqlite3
import datetime
from ultralytics import YOLO

### 1. MEMUAT DATA MAPPING (JSON) ###
try:
    with open('koordinat_parkir_2.json', 'r') as f:
        data_mapping = json.load(f)
except FileNotFoundError:
    print("Error: File koordinat_parkir_2.json tidak ditemukan. Jalankan mapping.py terlebih dahulu.")
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
tracker_terisi = {i: 0 for i in range(jumlah_petak)}
tracker_kosong = {i: 0 for i in range(jumlah_petak)}
status_akhir = {i: "KOSONG" for i in range(jumlah_petak)}

# Inisialisasi total masuk parkir kumulatif
total_masuk = 0
last_written_value = 0

# Memuat total_masuk sebelumnya dari database
try:
    conn = sqlite3.connect('parkir.db')
    cursor = conn.cursor()
    cursor.execute("SELECT total_masuk FROM status_kamera WHERE id_kamera = 'Kamera_02'")
    row = cursor.fetchone()
    if row is not None and row[0] is not None:
        total_masuk = row[0]
        last_written_value = row[0]
    conn.close()
except Exception as e:
    print(f"Gagal memuat total_masuk dari database: {e}")

# Membuat jendela tampilan yang bisa diubah ukurannya (resizeable)
nama_jendela = "Smart Parking (Kamera 02)"
cv2.namedWindow(nama_jendela, cv2.WINDOW_NORMAL)
cv2.resizeWindow(nama_jendela, 800, 600) 

### 4. LOOPING PEMROSESAN VIDEO ###
while True:
    ret, frame = cap.read()
    if not ret:
        print("Video selesai diputar. Mereset status terisi ke 0 (kumulatif total masuk tetap disimpan)...")
        total_terisi = 0
        total_kosong = jumlah_petak
        waktu_sekarang = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            conn = sqlite3.connect('parkir.db')
            cursor = conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO status_kamera (id_kamera, total_kosong, total_terisi, total_masuk, waktu_update)
            VALUES ('Kamera_02', ?, ?, ?, ?)
            ''', (total_kosong, total_terisi, total_masuk, waktu_sekarang))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Gagal mengupdate database saat video selesai: {e}")
            
        # Loop video kembali ke frame pertama
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        # Reset filter temporal dan status akhir
        tracker_terisi = {i: 0 for i in range(jumlah_petak)}
        tracker_kosong = {i: 0 for i in range(jumlah_petak)}
        status_akhir = {i: "KOSONG" for i in range(jumlah_petak)}
        continue
        
    frame = cv2.resize(frame, (1024, 768))
    kendaraan_di_petak = {i: False for i in range(jumlah_petak)}
    
    # Deteksi AI (Menggunakan predict biasa, sangat cepat dan stabil)
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
            tracker_terisi[i] += 1
            tracker_kosong[i] = 0
        else:
            tracker_kosong[i] += 1
            tracker_terisi[i] = 0
            
        # Logika transisi status parkir
        if tracker_terisi[i] >= batas_waktu_frame:
            # Jika status sebelumnya KOSONG, berarti kendaraan baru masuk parkir di petak ini
            if status_akhir[i] == "KOSONG":
                total_masuk += 1
                print(f"[Kamera 02] Petak P{i+1} TERISI! Total kendaraan parkir: {total_masuk}")
            status_akhir[i] = "TERISI"
            
        elif tracker_kosong[i] >= batas_waktu_frame:
            status_akhir[i] = "KOSONG"
            
        # Visualisasi warna petak berdasarkan status akhir yang stabil
        if status_akhir[i] == "TERISI":
            warna_petak = (0, 0, 255) # Merah
            total_terisi += 1
        else:
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
        
        # Sinkronisasi total_masuk dengan database (agar sensitif terhadap tombol reset di streamlit)
        cursor.execute("SELECT total_masuk FROM status_kamera WHERE id_kamera = 'Kamera_02'")
        row = cursor.fetchone()
        db_total_masuk = row[0] if (row is not None and row[0] is not None) else 0
        
        # Jika database di-reset secara eksternal (menjadi 0 padahal sebelumnya kita sudah menulis nilai > 0)
        if db_total_masuk == 0 and last_written_value > 0:
            total_masuk = 0
            last_written_value = 0
        elif db_total_masuk > total_masuk:
            total_masuk = db_total_masuk
            last_written_value = db_total_masuk
            
        # Sertakan total_masuk saat update agar terus terakumulasi di database
        cursor.execute('''
        INSERT OR REPLACE INTO status_kamera (id_kamera, total_kosong, total_terisi, total_masuk, waktu_update)
        VALUES ('Kamera_02', ?, ?, ?, ?)
        ''', (total_kosong, total_terisi, total_masuk, waktu_sekarang))
        
        last_written_value = total_masuk
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
    cv2.putText(frame, f"TOTAL KENDARAAN PARKIR: {total_masuk}", (35, 130), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow(nama_jendela, frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()