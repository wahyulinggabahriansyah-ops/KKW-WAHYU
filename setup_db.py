import sqlite3

# Membuat (atau membuka jika sudah ada) file database bernama parkir.db
conn = sqlite3.connect('parkir.db')
cursor = conn.cursor()

# Membuat tabel untuk menyimpan status dari berbagai kamera
cursor.execute('''
CREATE TABLE IF NOT EXISTS status_kamera (
    id_kamera TEXT PRIMARY KEY,
    total_kosong INTEGER,
    total_terisi INTEGER,
    total_masuk INTEGER DEFAULT 0,
    waktu_update DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# Logika Migrasi: Cek apakah kolom total_masuk sudah ada di database lama
try:
    cursor.execute("SELECT total_masuk FROM status_kamera LIMIT 1")
except sqlite3.OperationalError:
    # Kolom belum ada, tambahkan kolom total_masuk secara dinamis
    cursor.execute("ALTER TABLE status_kamera ADD COLUMN total_masuk INTEGER DEFAULT 0")
    print("Migrasi: Kolom 'total_masuk' berhasil ditambahkan ke tabel 'status_kamera'.")

# Mendaftarkan 'Kamera_01', 'Kamera_02', dan 'Kamera_03' sebagai nilai awal jika belum terdaftar
for id_kamera in ['Kamera_01', 'Kamera_02', 'Kamera_03']:
    cursor.execute('''
    INSERT OR IGNORE INTO status_kamera (id_kamera, total_kosong, total_terisi, total_masuk, waktu_update)
    VALUES (?, 0, 0, 0, CURRENT_TIMESTAMP)
    ''', (id_kamera,))

conn.commit()
conn.close()

print("Berhasil! Database 'parkir.db' siap digunakan.")