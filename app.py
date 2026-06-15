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

# Mengonversi logo Perhubungan menjadi base64 agar dapat dimuat oleh Streamlit secara lokal
logo_kemenhub_base64 = ""
try:
    with open("logo Perhubungan.png", "rb") as image_file:
        logo_kemenhub_base64 = base64.b64encode(image_file.read()).decode('utf-8')
except Exception as e:
    pass

# Mengonversi foto BG STTD menjadi base64 agar dapat dimuat oleh Streamlit secara lokal sebagai latar belakang
bg_sttd_base64 = ""
bg_mime = "image/jpeg"
try:
    with open("BG STTD.png", "rb") as image_file:
        bg_sttd_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        bg_mime = "image/png"
except Exception as e:
    try:
        with open("BG STTD.jpeg", "rb") as image_file:
            bg_sttd_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            bg_mime = "image/jpeg"
    except Exception as e2:
        pass

st.set_page_config(page_title="Papan Parkir Digital", layout="wide")

# Inject latar belakang gambar BG STTD dengan efek buram (blur) sekitar 75%
if bg_sttd_base64:
    st.markdown(f"""
    <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainViewContainer"] {{
            background: transparent !important;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            top: -10px;
            left: -10px;
            width: calc(100vw + 20px);
            height: calc(100vh + 20px);
            background-image: url("data:{bg_mime};base64,{bg_sttd_base64}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            filter: blur(5px);
            opacity: 0.75;
            z-index: -1;
        }}
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Anton&family=Orbitron:wght@600;800;900&family=Share+Tech+Mono&display=swap');
    
    * {
        font-family: 'Orbitron', 'Share Tech Mono', monospace !important;
    }
    
    h1 {
        font-family: 'Anton', 'Impact', sans-serif !important;
        font-size: 64px !important;
        text-align: center !important;
        margin-bottom: 30px !important;
        font-weight: 900 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
    }
    
    .main {
        background: transparent !important;
    }
    
    .main .block-container {
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding-top: 3rem !important;
        background: transparent !important;
    }
    
    .led-container { 
        position: relative; 
        background-color: #1e1e1e; 
        padding: 60px 40px; 
        border-radius: 15px; 
        border: 6px solid #FFCC00; 
        text-align: center; 
        max-width: 1100px;
        margin: 0 auto;
    }
    
    .teks-judul { 
        color: #FFFFFF; 
        font-size: 52px; 
        font-weight: 900; 
        margin-top: 30px; 
        margin-bottom: 40px; 
        padding-left: 130px; 
        padding-right: 130px; 
        letter-spacing: 2px;
        line-height: 1.2; 
    }
    
    .teks-kosong { 
        color: #00FF00; 
        font-size: 110px; 
        font-weight: 900; 
        margin: 20px 0; 
        letter-spacing: 4px;
        line-height: 1.1; 
    }
    
    .teks-terisi { 
        color: #FF0000; 
        font-size: 110px; 
        font-weight: 900; 
        margin: 20px 0; 
        letter-spacing: 4px;
        line-height: 1.1; 
    }
</style>
""", unsafe_allow_html=True)

st.title("SIMULASI PAPAN INFORMASI")
placeholder = st.empty()

# Sidebar untuk data internal / admin (Dibuat sekali di luar loop agar stabil dan tidak kedip)
st.sidebar.markdown("### 🔒 PANEL ADMIN (INTERNAL)")

# Tombol reset diletakkan di sidebar
if st.sidebar.button("Reset Total Kumulatif", key="btn_reset"):
    try:
        conn = sqlite3.connect('parkir.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE status_kamera SET total_masuk = 0")
        conn.commit()
        conn.close()
        st.sidebar.success("Berhasil di-reset ke 0!")
    except Exception as e:
        st.sidebar.error(f"Gagal mereset: {e}")

# Metric placeholder diletakkan di sidebar untuk update real-time
sidebar_metric_placeholder = st.sidebar.empty()

while True:
    try:
        # Menghubungkan ke database dan membaca data
        conn = sqlite3.connect('parkir.db')
        
        # Query cerdas: Langsung menjumlahkan (SUM) kolom dari semua kamera yang terdaftar
        df = pd.read_sql_query("SELECT SUM(total_kosong) as kosong, SUM(total_terisi) as terisi, SUM(total_masuk) as masuk FROM status_kamera", conn)
        conn.close()
        
        # Mengekstrak angka jika database tidak kosong
        if not df.empty and pd.notna(df['kosong'][0]):
            total_kosong = int(df['kosong'][0])
            total_terisi = int(df['terisi'][0])
            total_masuk = int(df['masuk'][0]) if pd.notna(df['masuk'][0]) else 0
        else:
            total_kosong, total_terisi, total_masuk = 0, 0, 0
            
    except Exception as e:
        total_kosong, total_terisi, total_masuk = 0, 0, 0

    # Merender ulang tampilan utama (Papan LED)
    with placeholder.container():
        st.markdown(f"""
        <div class="led-container">
            <img src="data:image/png;base64,{logo_kemenhub_base64}" width="115" style="position: absolute; top: 25px; left: 25px; object-fit: contain;">
            <img src="data:image/png;base64,{logo_base64}" width="115" style="position: absolute; top: 25px; right: 25px; object-fit: contain;">
            <div class="teks-judul">INFORMASI PARKIR ON STREET</div>
            <div class="teks-kosong">KOSONG : {total_kosong}</div>
            <div class="teks-terisi">TERISI : {total_terisi}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Merender ulang tampilan sidebar (Panel Admin / Internal)
    with sidebar_metric_placeholder.container():
        st.metric(label="Total Kumulatif Kendaraan Parkir", value=total_masuk)
        
    time.sleep(1)