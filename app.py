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

# Daftar bulan standar
months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# 2. Fungsi Universal Pembaca Data ACS (Super Tahan Banting)
@st.cache_data
def load_acs_generic_data(file_name):
    file_path = os.path.join("data", file_name)
    
    if not os.path.exists(file_path):
        return None, None
        
    try:
        xls = pd.ExcelFile(file_path)
        actual_sheets = xls.sheet_names
    except Exception:
        return None, None

    # --- TAHAP 1: MENCARI HEADER/KATEGORI ---
    sample_sheet = next((s for s in actual_sheets if s.strip().lower() in [m.lower() for m in months]), actual_sheets[0])
    try:
        df_sample = pd.read_excel(file_path, sheet_name=sample_sheet, header=None)
    except Exception:
        return None, None
    
    # Deteksi baris header (mencari keyword umum atau baris dengan teks terbanyak)
    keywords_header = ['(GMT)', 'WAKTU', 'JAM', 'KATEGORI']
    header_row_idx = df_sample[df_sample[0].astype(str).str.strip().str.upper().isin(keywords_header)].index
    
    r = 0
    if len(header_row_idx) > 0:
        r = header_row_idx[0]
    else:
        # Fallback: Cari baris dengan jumlah kolom terisi terbanyak (biasanya ini adalah baris kategori)
        max_cols = 0
        for i in range(min(10, len(df_sample))):
            cols = [str(val).strip() for val in df_sample.iloc[i].values if pd.notna(val) and str(val).strip() != '']
            if len(cols) > max_cols:
                max_cols = len(cols)
                r = i

    categories = [str(df_sample.iloc[r, c]).strip() for c in range(1, len(df_sample.columns)) 
                  if pd.notna(df_sample.iloc[r, c]) and str(df_sample.iloc[r, c]).strip() != '']
    
    if not categories:
        categories = [f"Kategori {i}" for i in range(1, len(df_sample.columns))]

    # --- TAHAP 2: EKSTRAKSI DATA PER BULAN ---
    data_kategori = {k: [] for k in categories}
    
    for month in months:
        matched_sheet = next((s for s in actual_sheets if s.strip().lower() == month.lower() or s.strip().lower() == month[:3].lower()), None)
        
        if matched_sheet:
            try:
                df = pd.read_excel(file_path, sheet_name=matched_sheet, header=None)
                
                # Deteksi baris target (mencari MEAN, RATA-RATA, JUMLAH, TOTAL)
                col0_clean = df[0].astype(str).str.strip().str.upper()
                keywords_target = ['MEAN', 'RATA-RATA', 'RATA', 'JUMLAH', 'TOTAL', 'AVERAGE']
                
                target_row = -1
                for kw in keywords_target:
                    match = df[col0_clean.str.contains(kw, na=False)].index.tolist()
                    if match:
                        target_row = match[-1]
                        break
                
                # Jika tidak ada kata kunci, ambil baris numerik paling bawah
                if target_row == -1:
                    target_row = len(df) - 1

                for idx, kategori in enumerate(categories, start=1):
                    if idx < len(df.columns):
                        val = df.iloc[target_row, idx]
                        # Ekstraksi angka aman tanpa batas maksimal > 100
                        try:
                            val_float = float(val)
                            if pd.isna(val_float):
                                val_float = 0.0
                        except (ValueError, TypeError):
                            val_float = 0.0
                        data_kategori[kategori].append(round(val_float, 2))
                    else:
                        data_kategori[kategori].append(0.0)
            except Exception:
                for kategori in categories: data_kategori[kategori].append(0.0)
        else:
            for kategori in categories: data_kategori[kategori].append(0.0)
            
    df_final = pd.DataFrame(data_kategori, index=months)
    return df_final, categories

# Fungsi pembantu untuk visualisasi meteogram (Line Chart)
def plot_meteogram(df, title, y_label, var_label):
    fig = px.line(df, x=df.index, y=df.columns, markers=True,
                  labels={'index': 'Bulan', 'value': y_label, 'variable': var_label},
                  template="plotly_white")
    fig.update_layout(hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)', height=500, title=title)
    return fig

# 3. Sistem Tab Navigasi
tabs = st.tabs([
    "🌡️ Temperatur", 
    "👁️ Visibility", 
    "☁️ Cloud Height", 
    "💨 Wind Speed", 
    "💧 Relative Humidity", 
    "📈 Temp Max & Min"
])

# --- TAB 1: TEMPERATUR ---
with tabs[0]:
    st.markdown("### 1. Persentase Temperatur Bulanan (2021-2025)")
    file_temp = 'rata_rata_persentase_temperature_2021_2025.xlsx'
    df_temp, _ = load_acs_generic_data(file_temp)
    if df_temp is not None and not df_temp.empty:
        st.plotly_chart(plot_meteogram(df_temp, "", "Persentase (%)", "Suhu (°C)"), use_container_width=True)
        st.dataframe(df_temp.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info("💡 Data tidak ditemukan.")

# --- TAB 2: VISIBILITY ---
with tabs[1]:
    st.markdown("### 2. Persentase Visibility Bulanan (2021-2025)")
    file_vis = 'rata_rata_persentase_visibility_2021_2025.xlsx'
    df_vis, _ = load_acs_generic_data(file_vis)
    if df_vis is not None and not df_vis.empty:
        st.plotly_chart(plot_meteogram(df_vis, "", "Persentase (%)", "Jarak Pandang (m)"), use_container_width=True)
        st.dataframe(df_vis.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info("💡 Data tidak ditemukan.")

# --- TAB 3: CLOUD HEIGHT (HS) ---
with tabs[2]:
    st.markdown("### 3. Persentase Cloud Height Bulanan (2021-2025)")
    file_hs = 'rata_rata_persentase_hs_2021_2025.xlsx'
    df_hs, _ = load_acs_generic_data(file_hs)
    if df_hs is not None and not df_hs.empty:
        st.plotly_chart(plot_meteogram(df_hs, "", "Persentase (%)", "Tinggi Awan (ft)"), use_container_width=True)
        st.dataframe(df_hs.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info("💡 Data tidak ditemukan.")

# --- TAB 4: WIND SPEED (WINDROSE) ---
with tabs[3]:
    st.markdown("### 4. Persentase Wind Speed Bulanan (2021-2025)")
    file_ws = 'rata_rata_persentase_ws_2021_2025.xlsx'
    df_ws, _ = load_acs_generic_data(file_ws)
    if df_ws is not None and not df_ws.empty:
        df_ws_long = df_ws.reset_index().rename(columns={'index': 'Bulan'}).melt(id_vars='Bulan', var_name='Kategori', value_name='Nilai')
        
        # Membuat plot Windrose (Polar Bar Chart)
        fig_ws = px.bar_polar(df_ws_long, r="Nilai", theta="Bulan", color="Kategori",
                              template="plotly_white",
                              color_discrete_sequence=px.colors.sequential.Plasma_r)
        fig_ws.update_layout(height=550)
        
        st.plotly_chart(fig_ws, use_container_width=True)
        st.dataframe(df_ws.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info("💡 Data tidak ditemukan.")

# --- TAB 5: RELATIVE HUMIDITY (RH) ---
with tabs[4]:
    st.markdown("### 5. Distribusi RH Bulanan (2021-2025)")
    file_rh = 'rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx'
    df_rh, _ = load_acs_generic_data(file_rh)
    if df_rh is not None and not df_rh.empty:
        st.plotly_chart(plot_meteogram(df_rh, "", "Nilai / Kejadian", "Rentang RH (%)"), use_container_width=True)
        st.dataframe(df_rh.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info("💡 Data tidak ditemukan.")

# --- TAB 6: TEMP MAKS & MIN ---
with tabs[5]:
    st.markdown("### 6. Distribusi Temp Maks & Min Bulanan (2021-2025)")
    file_tmaxmin = 'rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx'
    df_tmaxmin, _ = load_acs_generic_data(file_tmaxmin)
    if df_tmaxmin is not None and not df_tmaxmin.empty:
        st.plotly_chart(plot_meteogram(df_tmaxmin, "", "Nilai / Kejadian", "Kategori Suhu"), use_container_width=True)
        st.dataframe(df_tmaxmin.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info("💡 Data tidak ditemukan.")
