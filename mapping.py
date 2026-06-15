import cv2
import numpy as np
import json
import os

# 1. INPUT PARAMETER INTERAKTIF DI TERMINAL
print("====================================================")
print("     SISTEM PEMETAAN SEMI-OTOMATIS (HOMOGRAFI)       ")
print("====================================================")

# Input Nomor Kamera
try:
    kamera_input = input("Masukkan Nomor Kamera (1, 2, 3, 4, dst.) [Default: 4]: ").strip()
    kamera_num = int(kamera_input) if kamera_input else 4
except ValueError:
    kamera_num = 4

# Tentukan nama file JSON berdasarkan kamera
if kamera_num == 1:
    json_filename = "koordinat_parkir_1.json"
else:
    json_filename = f"koordinat_parkir_{kamera_num}.json"

# Input Jumlah Petak yang Ingin Dibuat
try:
    petak_input = input("Masukkan Jumlah Total Petak Berdampingan [Default: 3]: ").strip()
    jumlah_petak_target = int(petak_input) if petak_input else 3
except ValueError:
    jumlah_petak_target = 3

# Input Lebar Fisik Petak (Meter)
try:
    lebar_input = input("Masukkan Lebar Fisik Petak (Meter) [Default: 2.3]: ").strip()
    lebar_m = float(lebar_input) if lebar_input else 2.3
except ValueError:
    lebar_m = 2.3

# Input Panjang Fisik Petak (Meter)
try:
    panjang_input = input("Masukkan Panjang Fisik Petak (Meter) [Default: 5.0]: ").strip()
    panjang_m = float(panjang_input) if panjang_input else 5.0
except ValueError:
    panjang_m = 5.0

print("\n--- Konfigurasi Pemetaan ---")
print(f"File Output    : {json_filename}")
print(f"Target Petak   : {jumlah_petak_target} petak berdampingan")
print(f"Ukuran Fisik   : {lebar_m}m x {panjang_m}m (Lebar x Panjang)")
print("====================================================\n")

# List untuk menyimpan semua petak dan titik klik sementara
semua_petak = []
titik_sekarang = []
homography_done = False
frame_original = None
frame_copy = None

# Fungsi klik mouse untuk menentukan petak referensi pertama
def draw_polygon(event, x, y, flags, param):
    global titik_sekarang, semua_petak, homography_done, frame_copy
    
    if homography_done:
        return  # Jika pemetaan otomatis sudah selesai, abaikan klik selanjutnya
        
    if event == cv2.EVENT_LBUTTONDOWN:
        titik_sekarang.append((x, y))
        # Gambar titik lingkaran merah
        cv2.circle(frame_copy, (x, y), 6, (0, 0, 255), -1)
        
        # Beri nomor urutan klik di layar
        cv2.putText(frame_copy, str(len(titik_sekarang)), (x + 10, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # Gambar garis hijau penghubung titik sementara
        if len(titik_sekarang) > 1:
            cv2.line(frame_copy, titik_sekarang[-2], titik_sekarang[-1], (0, 255, 0), 2)
            
        # Jika sudah 4 titik, lakukan kalkulasi Homografi
        if len(titik_sekarang) == 4:
            # Tutup garis poligon petak pertama
            cv2.line(frame_copy, titik_sekarang[-1], titik_sekarang[0], (0, 255, 0), 2)
            
            print("[INFO] Petak acuan pertama berhasil direkam. Menghitung Homografi...")
            
            try:
                # Koordinat piksel layar (Image Plane)
                # Urutan: 1. Kiri-Atas, 2. Kiri-Bawah, 3. Kanan-Bawah, 4. Kanan-Atas
                pts_image = np.array(titik_sekarang, dtype=np.float32)
                
                # Koordinat meter dunia nyata (Ground Plane)
                pts_real = np.array([
                    [0, 0],              # Kiri Atas
                    [0, panjang_m],      # Kiri Bawah
                    [lebar_m, panjang_m],  # Kanan Bawah
                    [lebar_m, 0]         # Kanan Atas
                ], dtype=np.float32)
                
                # Hitung matriks transformasi dari Real-to-Image langsung
                H_inv = cv2.getPerspectiveTransform(pts_real, pts_image)
                
                # Hasilkan N petak secara otomatis berdampingan ke arah kanan (sumbu X positif)
                semua_petak = []
                for idx in range(jumlah_petak_target):
                    x_start = idx * lebar_m
                    x_end = (idx + 1) * lebar_m
                    
                    # Koordinat meter untuk petak ke-idx
                    pts_new_real = np.array([
                        [x_start, 0],
                        [x_start, panjang_m],
                        [x_end, panjang_m],
                        [x_end, 0]
                    ], dtype=np.float32).reshape(-1, 1, 2)
                    
                    # Proyeksikan kembali ke piksel layar
                    pts_new_image = cv2.perspectiveTransform(pts_new_real, H_inv)
                    petak_piksel = pts_new_image.reshape(4, 2).astype(int).tolist()
                    semua_petak.append(petak_piksel)
                
                # Gambarkan hasil semua petak otomatis di layar dengan warna Cyan cerah
                for i, area in enumerate(semua_petak):
                    pts_arr = np.array(area, np.int32)
                    # Gunakan warna kuning/cyan cerah untuk petak otomatis
                    cv2.polylines(frame_copy, [pts_arr], isClosed=True, color=(255, 255, 0), thickness=2)
                    cv2.putText(frame_copy, f"P{i+1} ({lebar_m}mx{panjang_m}m)", (area[0][0], area[0][1] - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                
                homography_done = True
                print(f"\n[SUKSES] Berhasil membuat {jumlah_petak_target} petak secara otomatis!")
                print("Tekan 'q' untuk MENYIMPAN hasil, atau 'r' untuk RESET dan menggambar ulang.")
                
            except Exception as e:
                print(f"[ERROR] Gagal menghitung homografi: {e}")
                print("Silakan tekan 'r' untuk reset dan klik ulang dengan teliti.")
                
        cv2.imshow("Pemetaan Semi-Otomatis", frame_copy)

# Memuat Video Pengujian (Selalu menggunakan video_parkir.mp4)
video_filename = "video_parkir.mp4"

cap = cv2.VideoCapture(video_filename)
ret, frame = cap.read()

if not ret:
    print(f"Error: Video '{video_filename}' tidak dapat dibaca!")
else:
    # Resize ke 1024x768 (Standar Projek) agar akurat
    frame = cv2.resize(frame, (1024, 768))
    frame_original = frame.copy()
    frame_copy = frame.copy()
    
    cv2.imshow("Pemetaan Semi-Otomatis", frame_copy)
    cv2.setMouseCallback("Pemetaan Semi-Otomatis", draw_polygon)
    
    print("====================================================")
    print("PETUNJUK PENGGUNAAN MOUSE:")
    print("Klik 4 kali secara BERURUTAN pada Petak Acuan Pertama:")
    print("  1. Klik Kiri Atas")
    print("  2. Klik Kiri Bawah")
    print("  3. Klik Kanan Bawah")
    print("  4. Klik Kanan Atas")
    print("----------------------------------------------------")
    print("TOMBOL KEYBOARD:")
    print("  'q' - Simpan koordinat ke JSON & keluar")
    print("  'r' - Reset gambar / klik ulang")
    print("====================================================")
    
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            # Reset pemetaan
            titik_sekarang = []
            semua_petak = []
            homography_done = False
            frame_copy = frame_original.copy()
            cv2.imshow("Pemetaan Semi-Otomatis", frame_copy)
            print("\n[RESET] Klik direset. Silakan gambar ulang petak acuan pertama...")
            
    cv2.destroyAllWindows()
    cap.release()
    
    # Menyimpan data koordinat ke file JSON
    if len(semua_petak) > 0:
        data_json = {"petak_parkir": semua_petak}
        with open(json_filename, "w") as f:
            json.dump(data_json, f, indent=4)
        print(f"\nBerhasil! {len(semua_petak)} petak parkir telah disimpan ke '{json_filename}'.")
    else:
        print("\nTidak ada petak yang dipetakan.")