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
    waktu_update DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# Mendaftarkan 'Kamera_01' sebagai nilai awal
cursor.execute('''
INSERT OR REPLACE INTO status_kamera (id_kamera, total_kosong, total_terisi, waktu_update)
VALUES ('Kamera_01', 0, 0, CURRENT_TIMESTAMP)
''')

conn.commit()
conn.close()

print("Berhasil! Database 'parkir.db' siap digunakan.")