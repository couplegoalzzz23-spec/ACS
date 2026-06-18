import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Konfigurasi Halaman Web Dashboard
st.set_page_config(
    page_title="Dashboard ACS Terintegrasi BMKG", 
    layout="wide", 
    page_icon="🌤️"
)

st.title("📊 Dashboard Aerodrome Climatological Summary (ACS)")
st.subheader("Analisis Klimatologi Cuaca Operasional Pangkalan Udara Periode 2021-2025")
st.markdown("---")

# Daftar bulan standar untuk sinkronisasi data sheet dan indeks
months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# 2. Fungsi Universal Pembaca Data ACS (Akurat & Tahan Banting)
@st.cache_data
def load_acs_generic_data(file_name):
    # Mengarah langsung ke folder 'data' sesuai struktur di GitHub
    file_path = os.path.join("data", file_name)
    
    if not os.path.exists(file_path):
        return None, None
        
    try:
        xls = pd.ExcelFile(file_path)
        actual_sheets = xls.sheet_names
    except Exception as e:
        return None, None

    # Mencari sheet bulan pertama yang valid untuk mendeteksi struktur kolom/kategori
    sample_sheet = next((s for s in actual_sheets if s.strip().lower() in [m.lower() for m in months]), actual_sheets[0])
    try:
        df_sample = pd.read_excel(file_path, sheet_name=sample_sheet, header=None)
    except Exception:
        return None, None
    
    # Mengunci pencarian baris header berdasarkan letak teks '(GMT)'
    header_row_idx = df_sample[df_sample[0].astype(str).str.strip().str.upper() == '(GMT)'].index
    
    if len(header_row_idx) > 0:
        r = header_row_idx[0]
        # Mengambil nama rentang kategori (kolom 1 hingga akhir)
        categories = [str(df_sample.iloc[r, c]).strip() for c in range(1, len(df_sample.columns)) 
                      if pd.notna(df_sample.iloc[r, c]) and str(df_sample.iloc[r, c]).strip() != '']
    else:
        # Fallback/Cadangan jika teks (GMT) tidak ditemukan
        categories = [f"Kategori {i}" for i in range(1, len(df_sample.columns))]

    # Inisialisasi wadah data
    data_kategori = {k: [] for k in categories}
    
    # Ekstraksi nilai baris 'MEAN' dari setiap sheet bulan
    for month in months:
        matched_sheet = next((s for s in actual_sheets if s.strip().lower() == month.lower()), None)
        
        if matched_sheet:
            try:
                df = pd.read_excel(file_path, sheet_name=matched_sheet, header=None)
                # Cari baris nilai rata-rata/MEAN gabungan 2021-2025
                mean_rows = df[df[0].astype(str).str.strip().str.upper() == 'MEAN'].index.tolist()
                
                if mean_rows:
                    target_row = mean_rows[-1] # Ambil baris MEAN paling bawah
                    for idx, kategori in enumerate(categories, start=1):
                        if idx < len(df.columns):
                            val = df.iloc[target_row, idx]
                            # Pembersihan data anomali atau kosong
                            if pd.isna(val) or (isinstance(val, (int, float)) and val > 100):
                                val = 0.0
                            data_kategori[kategori].append(round(float(val), 2))
                        else:
                            data_kategori[kategori].append(0.0)
                else:
                    for kategori in categories: data_kategori[kategori].append(0.0)
            except Exception:
                for kategori in categories: data_kategori[kategori].append(0.0)
        else:
            for kategori in categories: data_kategori[kategori].append(0.0)
            
    df_final = pd.DataFrame(data_kategori, index=months)
    return df_final, categories

# Fungsi pembantu untuk membuat visualisasi meteogram standar (Line Chart)
def plot_meteogram(df, title, y_label, var_label):
    fig = px.line(df, x=df.index, y=df.columns, markers=True,
                  labels={'index': 'Bulan', 'value': y_label, 'variable': var_label},
                  template="plotly_white")
    fig.update_layout(hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)', height=500)
    return fig

# 3. Membuat Sistem Tab Navigasi untuk 6 Parameter Konten Utama
tabs = st.tabs([
    "🌡️ Temperatur", 
    "👁️ Visibility", 
    "☁️ Cloud Height (HS)", 
    "💨 Wind Speed (WS)", 
    "💧 Relative Humidity (RH)", 
    "📈 Temp Max & Min"
])

# --- TAB 1: TEMPERATUR ---
with tabs[0]:
    st.markdown("### 1. Distribusi Persentase Temperatur Bulanan")
    file_temp = 'rata_rata_persentase_temperature_2021_2025.xlsx'
    df_temp, _ = load_acs_generic_data(file_temp)
    
    if df_temp is not None and not df_temp.empty:
        fig_temp = plot_meteogram(df_temp, "Meteogram Temperatur", "Persentase (%)", "Rentang Suhu (°C)")
        st.plotly_chart(fig_temp, use_container_width=True)
        st.dataframe(df_temp.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info(f"💡 File `data/{file_temp}` tidak ditemukan atau strukturnya tidak sesuai.")

# --- TAB 2: VISIBILITY ---
with tabs[1]:
    st.markdown("### 2. Distribusi Persentase Visibility Bulanan")
    file_vis = 'rata_rata_persentase_visibility_2021_2025.xlsx'
    df_vis, _ = load_acs_generic_data(file_vis)
    
    if df_vis is not None and not df_vis.empty:
        fig_vis = plot_meteogram(df_vis, "Meteogram Visibility", "Persentase (%)", "Jarak Pandang (m)")
        st.plotly_chart(fig_vis, use_container_width=True)
        st.dataframe(df_vis.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info(f"💡 File `data/{file_vis}` tidak ditemukan atau strukturnya tidak sesuai.")

# --- TAB 3: CLOUD HEIGHT (HS) ---
with tabs[2]:
    st.markdown("### 3. Distribusi Persentase Cloud Height (HS) Bulanan")
    file_hs = 'rata_rata_persentase_hs_2021_2025.xlsx'
    df_hs, _ = load_acs_generic_data(file_hs)
    
    if df_hs is not None and not df_hs.empty:
        fig_hs = plot_meteogram(df_hs, "Meteogram Tinggi Awan", "Persentase (%)", "Tinggi Dasar Awan (ft)")
        st.plotly_chart(fig_hs, use_container_width=True)
        st.dataframe(df_hs.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info(f"💡 File `data/{file_hs}` tidak ditemukan atau strukturnya tidak sesuai.")

# --- TAB 4: WIND SPEED (WS) ---
with tabs[3]:
    st.markdown("### 4. Distribusi Persentase Wind Speed Bulanan")
    file_ws = 'rata_rata_persentase_ws_2021_2025.xlsx'
    df_ws, _ = load_acs_generic_data(file_ws)
    
    if df_ws is not None and not df_ws.empty:
        # Transformasi bentuk data ke format 'long' agar optimal untuk visualisasi distribusi frekuensi
        df_ws_long = df_ws.reset_index().rename(columns={'index': 'Bulan'}).melt(id_vars='Bulan', var_name='Kategori_WS', value_name='Persentase')
        
        # Menggunakan grafik batang bertumpuk (Stacked Bar) sebagai representasi distribusi frekuensi arah/kecepatan angin bulanan yang sangat interaktif
        fig_ws = px.bar(df_ws_long, x='Bulan', y='Persentase', color='Kategori_WS',
                        title="Distribusi Persentase Klasifikasi Kecepatan Angin",
                        labels={'Persentase': 'Persentase (%)', 'Kategori_WS': 'Rentang Kecepatan / Arah'},
                        template="plotly_white")
        fig_ws.update_layout(height=500, barmode='stack', plot_bgcolor='rgba(0,0,0,0)')
        
        st.plotly_chart(fig_ws, use_container_width=True)
        st.dataframe(df_ws.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info(f"💡 File `data/{file_ws}` tidak ditemukan atau strukturnya tidak sesuai.")

# --- TAB 5: RELATIVE HUMIDITY (RH) ---
with tabs[4]:
    st.markdown("### 5. Distribusi Persentase Relative Humidity (RH) Bulanan")
    file_rh = 'rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx'
    df_rh, _ = load_acs_generic_data(file_rh)
    
    if df_rh is not None and not df_rh.empty:
        fig_rh = plot_meteogram(df_rh, "Meteogram Kelembaban Udara (RH)", "Persentase (%)", "Rentang Kelembaban (%)")
        st.plotly_chart(fig_rh, use_container_width=True)
        st.dataframe(df_rh.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info(f"💡 File `data/{file_rh}` tidak ditemukan atau strukturnya tidak sesuai.")

# --- TAB 6: TEMPERATUR MAKSIMUM & MINIMUM ---
with tabs[5]:
    st.markdown("### 6. Distribusi Persentase Temperatur Maksimum & Minimum Bulanan")
    file_tmaxmin = 'rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx'
    df_tmaxmin, _ = load_acs_generic_data(file_tmaxmin)
    
    if df_tmaxmin is not None and not df_tmaxmin.empty:
        fig_tmaxmin = plot_meteogram(df_tmaxmin, "Meteogram Ekstremitas Suhu (Tmax/Tmin)", "Persentase (%)", "Kategori Suhu (°C)")
        st.plotly_chart(fig_tmaxmin, use_container_width=True)
        st.dataframe(df_tmaxmin.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info(f"💡 File `data/{file_tmaxmin}` tidak ditemukan atau strukturnya tidak sesuai.")
