import cv2
import numpy as np
import json

# List untuk menyimpan semua petak dan titik sementara
semua_petak = []
titik_sekarang = []

def draw_polygon(event, x, y, flags, param):
    global titik_sekarang, semua_petak
    
    if event == cv2.EVENT_LBUTTONDOWN:
        titik_sekarang.append((x, y))
        cv2.circle(frame_copy, (x, y), 5, (0, 0, 255), -1)
        
        # Gambar garis antar titik untuk petak yang sedang digambar
        if len(titik_sekarang) > 1:
            cv2.line(frame_copy, titik_sekarang[-2], titik_sekarang[-1], (0, 255, 0), 2)
            
        # Jika sudah 4 titik, tutup poligon dan simpan ke list
        if len(titik_sekarang) == 4:
            cv2.line(frame_copy, titik_sekarang[-1], titik_sekarang[0], (0, 255, 0), 2)
            semua_petak.append(titik_sekarang.copy())
            print(f"Petak {len(semua_petak)} berhasil direkam: {titik_sekarang}")
            titik_sekarang = [] # Reset list untuk mulai menggambar petak berikutnya
            
        cv2.imshow("Pemetaan Banyak Petak", frame_copy)

# Inisialisasi Video (Pastikan nama file sesuai)
video_path = 'video_parkir.mp4' 
cap = cv2.VideoCapture(video_path)
ret, frame = cap.read()

if not ret:
    print("Error: Video gagal dibaca!")
else:
    frame = cv2.resize(frame, (1024, 768))
    frame_copy = frame.copy()
    
    cv2.imshow("Pemetaan Banyak Petak", frame_copy)
    cv2.setMouseCallback("Pemetaan Banyak Petak", draw_polygon)

    print("=========================================")
    print("INSTRUKSI MULTI-MAPPING:")
    print("1. Klik 4 kali untuk membentuk SATU petak parkir.")
    print("2. Ulangi langkah 1 untuk petak lainnya di jalan tersebut.")
    print("3. Tekan tombol 'q' jika semua petak sudah selesai dipetakan.")
    print("=========================================")

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cv2.destroyAllWindows()
    cap.release()
    
    # Menyimpan data koordinat ke file JSON
    if len(semua_petak) > 0:
        data_json = {"petak_parkir": semua_petak}
        with open("koordinat_parkir_3.json", "w") as f:
            json.dump(data_json, f, indent=4)
        print(f"\nBerhasil! {len(semua_petak)} petak parkir telah disimpan ke 'koordinat_parkir_3.json'.")
    else:
        print("\nTidak ada petak yang dipetakan.")