import streamlit as st
import sqlite3
import pandas as pd
import time

st.set_page_config(page_title="Papan Parkir Digital", layout="centered")

st.markdown("""
<style>
    .led-container { background-color: #000000; padding: 30px; border-radius: 15px; border: 4px solid #333; text-align: center; font-family: 'Courier New', Courier, monospace; }
    .teks-judul { color: #FFFFFF; font-size: 40px; margin-bottom: 20px; }
    .teks-kosong { color: #00FF00; font-size: 70px; font-weight: bold; margin: 0; }
    .teks-terisi { color: #FF0000; font-size: 70px; font-weight: bold; margin: 0; }
</style>
""", unsafe_allow_html=True)

st.title("🚦 SIMULASI PAPAN INFORMASI")
placeholder = st.empty()

while True:
    try:
        # Menghubungkan ke database dan membaca data
        conn = sqlite3.connect('parkir.db')
        
        # Query cerdas: Langsung menjumlahkan (SUM) kolom dari semua kamera yang terdaftar
        df = pd.read_sql_query("SELECT SUM(total_kosong) as kosong, SUM(total_terisi) as terisi FROM status_kamera", conn)
        conn.close()
        
        # Mengekstrak angka jika database tidak kosong
        if not df.empty and pd.notna(df['kosong'][0]):
            total_kosong = int(df['kosong'][0])
            total_terisi = int(df['terisi'][0])
        else:
            total_kosong, total_terisi = 0, 0
            
    except Exception as e:
        total_kosong, total_terisi = 0, 0

    # Merender ulang tampilan antarmuka
    with placeholder.container():
        st.markdown(f"""
        <div class="led-container">
            <div class="teks-judul">INFO PARKIR JALAN</div>
            <div class="teks-kosong">KOSONG : {total_kosong}</div>
            <div class="teks-terisi">TERISI : {total_terisi}</div>
        </div>
        """, unsafe_allow_html=True)
    
    time.sleep(1)