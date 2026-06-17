import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. Konfigurasi Dasar ---
st.set_page_config(page_title="Dashboard ACS Terintegrasi", layout="wide", page_icon="🌤️")

# folder data di repositori Anda
DATA_DIR = "data" 

# Kamus Konfigurasi: Anda cukup menambah baris di sini untuk parameter baru
DATA_CONFIG = {
    "Temperatur": {"file": "rata_rata_persentase_temperature_2021_2025.xlsx", "unit": "°C"},
    "Visibility": {"file": "rata_rata_persentase_visibility_2021_2025.xlsx", "unit": "Meter"},
    "Cloud Height (HS)": {"file": "rata_rata_persentase_hs_2021_2025.xlsx", "unit": "ft"},
    "Relative Humidity": {"file": "rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx", "unit": "%"},
    "Temp Max/Min": {"file": "rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx", "unit": "°C"}
}

months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# --- 2. Fungsi Parser (Mesin Utama) ---
@st.cache_data
def load_climate_data(file_name):
    path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(path):
        return None, "File tidak ditemukan."
    
    try:
        xls = pd.ExcelFile(path)
        all_data = {}
        categories = []

        for month in months:
            if month in xls.sheet_names:
                df = pd.read_excel(path, sheet_name=month, header=None)
                
                # Cari baris "(GMT)" sebagai header kategori
                header_idx = df[df[0].astype(str).str.contains("\(GMT\)", case=False, na=False)].index
                if not header_idx.empty:
                    r = header_idx[0]
                    # Ambil kategori
                    current_cats = [str(c) for c in df.iloc[r, 1:] if pd.notna(c)]
                    if not categories: categories = current_cats
                    
                    # Cari baris "MEAN" sebagai data
                    mean_idx = df[df[0].astype(str).str.upper() == 'MEAN'].index
                    if not mean_idx.empty:
                        data_row = df.iloc[mean_idx[-1], 1:].values
                        # Konversi data ke angka
                        all_data[month] = pd.to_numeric(pd.Series(data_row), errors='coerce').fillna(0).tolist()
            
        return pd.DataFrame(all_data, index=categories).T, None
    except Exception as e:
        return None, str(e)

# --- 3. Antarmuka Dashboard ---
st.title("🌤️ Dashboard Aerodrome Climatological Summary (ACS)")
st.markdown("Analisis Klimatologi Data Operasional 2021-2025.")
st.divider()

# Sidebar Navigasi
param_key = st.sidebar.selectbox("Pilih Parameter:", list(DATA_CONFIG.keys()))
file_name = DATA_CONFIG[param_key]["file"]

# Proses Data
df, error = load_climate_data(file_name)

if error:
    st.error(f"Error pada file {file_name}: {error}")
    st.info("Pastikan file berada di folder `data/` dan formatnya sesuai standar.")
else:
    # Visualisasi
    st.subheader(f"Grafik {param_key}")
    fig = px.line(df, markers=True, labels={'index': 'Bulan', 'value': 'Persentase (%)', 'variable': 'Kategori'})
    fig.update_layout(hovermode="x unified", height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabel
    st.subheader("Data Tabel")
    st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
