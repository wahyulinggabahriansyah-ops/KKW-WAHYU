import streamlit as st
import sqlite3
import pandas as pd
import time
import base64

# Mengonversi logo PTDI STTD menjadi base64 agar dapat dimuat oleh Streamlit secara lokal
logo_base64 = ""
try:
    with open("logo PTDI STTD.png", "rb") as image_file:
        logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
except Exception as e:
    pass

st.set_page_config(page_title="Papan Parkir Digital", layout="centered")

st.markdown("""
<style>
    * {
        font-family: 'Times New Roman', Times, serif !important;
    }
    .led-container { position: relative; background-color: #000000; padding: 50px 30px 45px 30px; border-radius: 15px; border: 4px solid #333; text-align: center; }
    .teks-judul { color: #FFFFFF; font-size: 40px; font-weight: bold; margin-top: 10px; margin-bottom: 25px; padding-left: 80px; padding-right: 80px; line-height: 1.2; }
    .teks-kosong { color: #00FF00; font-size: 70px; font-weight: bold; margin: 20px 0 10px 0; line-height: 1.2; }
    .teks-terisi { color: #FF0000; font-size: 70px; font-weight: bold; margin: 10px 0 20px 0; line-height: 1.2; }
</style>
""", unsafe_allow_html=True)

st.title("SIMULASI PAPAN INFORMASI")
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
            <img src="data:image/png;base64,{logo_base64}" width="75" style="position: absolute; top: 15px; right: 15px; object-fit: contain;">
            <div class="teks-judul">INFORMASI PARKIR ON STREET</div>
            <div class="teks-kosong">KOSONG : {total_kosong}</div>
            <div class="teks-terisi">TERISI : {total_terisi}</div>
        </div>
        """, unsafe_allow_html=True)
    
    time.sleep(1)