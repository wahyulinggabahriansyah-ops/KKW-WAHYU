from ultralytics import YOLO
import cv2

# Mengunduh dan memuat model YOLOv8 versi 'nano' (yolov8n.pt)
# Versi 'nano' adalah yang paling ringan dan sangat lancar dijalankan tanpa GPU
model = YOLO('yolov8n.pt')

# Menjalankan deteksi pada gambar contoh bawaan dari Ultralytics
# Parameter show=True akan otomatis menampilkan jendela hasil deteksi
results = model.predict(source='https://ultralytics.com/images/bus.jpg', show=True)

# Menahan jendela agar tidak langsung tertutup sampai Anda menekan sembarang tombol
cv2.waitKey(0)
cv2.destroyAllWindows()