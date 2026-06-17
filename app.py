import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard ACS Terintegrasi", layout="wide", page_icon="🌤️")

# --- KONFIGURASI ---
DATA_DIR = "data"
# Pastikan nama file di bawah sama PERSIS dengan yang ada di folder 'data'
DATA_MAP = {
    "Temperature": "rata_rata_persentase_temperature_2021_2025.xlsx",
    "Visibility": "rata_rata_persentase_visibility_2021_2025.xlsx",
    "Cloud Height (HS)": "rata_rata_persentase_hs_2021_2025.xlsx",
    "Wind Speed (WS)": "rata_rata_persentase_ws_2021_2025.xlsx",
    "Relative Humidity": "rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx",
    "Temp Max/Min": "rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx"
}

months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

def load_data(file_path):
    if not os.path.exists(file_path):
        return None, "File tidak ditemukan."
    
    try:
        xls = pd.ExcelFile(file_path)
        all_data = {}
        
        for month in months:
            if month in xls.sheet_names:
                df = pd.read_excel(file_path, sheet_name=month, header=None)
                
                # Cari baris yang mengandung 'MEAN' secara case-insensitive
                # Kita gunakan .str.contains(..., case=False) agar lebih fleksibel
                mask = df[0].astype(str).str.contains("MEAN", case=False, na=False)
                mean_rows = df[mask].index
                
                if not mean_rows.empty:
                    # Ambil baris terakhir yang mengandung kata MEAN
                    row_idx = mean_rows[-1]
                    # Ambil data dari kolom 1 ke kanan
                    data = df.iloc[row_idx, 1:].tolist()
                    # Bersihkan data: jadikan angka, jika error jadikan 0
                    all_data[month] = [float(pd.to_numeric(x, errors='coerce')) if pd.notna(x) else 0.0 for x in data]
                else:
                    # Jika tidak ketemu 'MEAN', beri data kosong agar script tidak crash
                    all_data[month] = [0.0] * 5 
        
        return pd.DataFrame(all_data).T, None
    except Exception as e:
        return None, str(e)

# --- ANTARMUKA ---
st.title("🌤️ Dashboard ACS Terintegrasi")
st.markdown("Analisis Klimatologi Data Operasional 2021-2025.")
st.divider() # Mengganti st.hr() yang salah

option = st.sidebar.selectbox("Pilih Parameter:", list(DATA_MAP.keys()))
file_name = DATA_MAP[option]
file_path = os.path.join(DATA_DIR, file_name)

df, error = load_data(file_path)

if error:
    st.error(f"Terjadi kesalahan: {error}")
    st.info("Pastikan file sudah terupload di folder 'data' di GitHub Anda.")
else:
    if df.empty:
        st.warning("Data berhasil dimuat tetapi tampak kosong. Periksa apakah baris 'MEAN' ada di file Excel.")
    else:
        st.subheader(f"Grafik {option}")
        fig = px.line(df, markers=True)
        fig.update_layout(hovermode="x unified", height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Data Tabel")
        st.dataframe(df.style.format("{:.2f}"))
