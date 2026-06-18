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

# Daftar bulan standar untuk sinkronisasi sumbu X
months_ordered = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# 2. ENGINE PEMBACA DATA MULTI-FORMAT (Akurat & Tahan Banting)
@st.cache_data
def load_acs_data(file_name):
    # Cek ketersediaan berkas di dalam folder 'data' maupun root directory
    possible_paths = [os.path.join("data", file_name), file_name]
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
            
    if not file_path:
        return None
        
    try:
        xls = pd.ExcelFile(file_path)
    except Exception:
        return None

    all_months_data = {}
    master_categories = []

    # Variasi penamaan sheet bulan pada Excel (mengantisipasi singkatan atau nomor)
    month_variants = {
        'Januari': ['jan', '01', '1'],
        'Februari': ['feb', '02', '2'],
        'Maret': ['mar', '03', '3'],
        'April': ['apr', '04', '4'],
        'Mei': ['mei', 'may', '05', '5'],
        'Juni': ['jun', '06', '6'],
        'Juli': ['jul', '07', '7'],
        'Agustus': ['agu', 'aug', '08', '8'],
        'September': ['sep', '09', '9'],
        'Oktober': ['okt', 'oct', '10'],
        'November': ['nov', '11'],
        'Desember': ['des', 'dec', '12']
    }

    for m_name, variants in month_variants.items():
        sheet_name = None
        for s in xls.sheet_names:
            s_clean = s.strip().lower()
            if any(s_clean.startswith(v) for v in variants):
                sheet_name = s
                break
                
        if not sheet_name:
            continue
            
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        except Exception:
            continue
            
        # Pembersihan awal baris yang kosong total
        df = df.dropna(how='all').reset_index(drop=True)
        if df.empty:
            continue
            
        # TAHAP A: Deteksi Baris Header Kategori (Batas Parameter)
        header_idx = 0
        found_header = False
        for idx in range(min(15, len(df))):
            val_0 = str(df.iloc[idx, 0]).strip().lower()
            if any(kw in val_0 for kw in ['(gmt)', 'gmt', 'jam', 'waktu', 'kategori', 'arah']):
                header_idx = idx
                found_header = True
                break
        if not found_header:
            header_idx = df.iloc[:10].notna().sum(axis=1).idxmax()
            
        # TAHAP B: Deteksi Baris Ringkasan Akhir (Summary Row)
        target_idx = -1
        keywords_summary = ['mean', 'rata', 'jumlah', 'total', 'average', 'sum']
        
        for idx in range(header_idx + 1, len(df)):
            val_0 = str(df.iloc[idx, 0]).strip().lower()
            if any(kw in val_0 for kw in keywords_summary):
                target_idx = idx
                break
                
        # Kebijakan Fallback jika tidak ada kata kunci: Cari baris numerik paling bawah sebelum footer text
        if target_idx == -1:
            for idx in range(len(df) - 1, header_idx, -1):
                row_slice = df.iloc[idx, 1:]
                numeric_values = pd.to_numeric(row_slice, errors='coerce').dropna()
                if len(numeric_values) >= (len(df.columns) - 1) * 0.5 and len(numeric_values) > 0:
                    target_idx = idx
                    break
                    
        if target_idx == -1 or header_idx >= target_idx:
            continue
            
        # TAHAP C: Ekstraksi Data Kolom demi Kolom
        month_dict = {}
        for col_idx in range(1, len(df.columns)):
            cat_val = df.iloc[header_idx, col_idx]
            if pd.isna(cat_val) or str(cat_val).strip().lower() in ['nan', 'unnamed', '']:
                continue
                
            cat_name = str(cat_val).strip()
            data_val = df.iloc[target_idx, col_idx]
            
            try:
                val_float = float(data_val)
                if pd.isna(val_float):
                    val_float = 0.0
            except (ValueError, TypeError):
                val_float = 0.0
                
            month_dict[cat_name] = val_float
            if cat_name not in master_categories:
                master_categories.append(cat_name)
                
        all_months_data[m_name] = month_dict

    if not all_months_data:
        return None

    # TAHAP D: Rekonstruksi Matriks Data 12 Bulan Secara Sempurna
    final_rows = []
    for m in months_ordered:
        row = {'Bulan': m}
        for cat in master_categories:
            if m in all_months_data:
                row[cat] = all_months_data[m].get(cat, 0.0)
            else:
                row[cat] = 0.0
        final_rows.append(row)
        
    df_final = pd.DataFrame(final_rows).set_index('Bulan')
    return df_final

# 3. FUNGSI UNIFORM UNTUK VISUALISASI GRAFIK (MENIRU DESAIN TEMPERATUR)
def plot_custom_meteogram(df, y_label, var_label):
    fig = px.line(df, x=df.index, y=df.columns, markers=True,
                  labels={'index': 'Bulan', 'value': y_label, 'variable': var_label},
                  template="plotly_white")
    fig.update_layout(
        hovermode="x unified", 
        plot_bgcolor='rgba(0,0,0,0)', 
        height=480,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(230,230,230,0.8)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(230,230,230,0.8)')
    return fig

# 4. ANTARMUKA TAB NAVIGASI YANG RAPI & SERAGAM
tabs = st.tabs([
    "🌡️ Temperatur", 
    "👁️ Visibility", 
    "☁️ Cloud Height (HS)", 
    "💨 Wind Speed", 
    "💧 Relative Humidity (RH)", 
    "📈 Temp Max & Min"
])

# --- TAB 1: TEMPERATUR ---
with tabs[0]:
    st.markdown("### 📊 Distribusi Persentase Temperatur Bulanan (2021-2025)")
    df_temp = load_acs_data('rata_rata_persentase_temperature_2021_2025.xlsx')
    if df_temp is not None and not df_temp.empty:
        st.plotly_chart(plot_custom_meteogram(df_temp, "Persentase (%)", "Suhu (°C)"), use_container_width=True)
        st.dataframe(df_temp.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error("⚠️ Berkas `rata_rata_persentase_temperature_2021_2025.xlsx` tidak ditemukan di folder 'data'.")

# --- TAB 2: VISIBILITY ---
with tabs[1]:
    st.markdown("### 📊 Distribusi Persentase Visibility Bulanan (2021-2025)")
    df_vis = load_acs_data('rata_rata_persentase_visibility_2021_2025.xlsx')
    if df_vis is not None and not df_vis.empty:
        st.plotly_chart(plot_custom_meteogram(df_vis, "Persentase (%)", "Jarak Pandang (m)"), use_container_width=True)
        st.dataframe(df_vis.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error("⚠️ Berkas `rata_rata_persentase_visibility_2021_2025.xlsx` tidak ditemukan di folder 'data'.")

# --- TAB 3: CLOUD HEIGHT (HS) ---
with tabs[2]:
    st.markdown("### 📊 Distribusi Persentase Cloud Height Bulanan (2021-2025)")
    df_hs = load_acs_data('rata_rata_persentase_hs_2021_2025.xlsx')
    if df_hs is not None and not df_hs.empty:
        st.plotly_chart(plot_custom_meteogram(df_hs, "Persentase (%)", "Tinggi Awan (ft)"), use_container_width=True)
        st.dataframe(df_hs.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error("⚠️ Berkas `rata_rata_persentase_hs_2021_2025.xlsx` tidak ditemukan di folder 'data'.")

# --- TAB 4: WIND SPEED ---
with tabs[3]:
    st.markdown("### 📊 Distribusi Persentase Wind Speed Bulanan (2021-2025)")
    df_ws = load_acs_data('rata_rata_persentase_ws_2021_2025.xlsx')
    if df_ws is not None and not df_ws.empty:
        st.plotly_chart(plot_custom_meteogram(df_ws, "Persentase (%)", "Kecepatan Angin (Kt)"), use_container_width=True)
        st.dataframe(df_ws.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error("⚠️ Berkas `rata_rata_persentase_ws_2021_2025.xlsx` tidak ditemukan di folder 'data'.")

# --- TAB 5: RELATIVE HUMIDITY (RH) ---
with tabs[4]:
    st.markdown("### 📊 Rata-rata Jumlah Kejadian Masuk Rentang RH Bulanan (2021-2025)")
    df_rh = load_acs_data('rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx')
    if df_rh is not None and not df_rh.empty:
        st.plotly_chart(plot_custom_meteogram(df_rh, "Jumlah Kejadian", "Rentang Kelembapan (%)"), use_container_width=True)
        st.dataframe(df_rh.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error("⚠️ Berkas `rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx` tidak ditemukan di folder 'data'.")

# --- TAB 6: TEMP MAKS & MIN ---
with tabs[5]:
    st.markdown("### 📊 Rata-rata Jumlah Kejadian Masuk Rentang Temp Maks/Min Bulanan (2021-2025)")
    df_tmaxmin = load_acs_data('rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx')
    if df_tmaxmin is not None and not df_tmaxmin.empty:
        st.plotly_chart(plot_custom_meteogram(df_tmaxmin, "Jumlah Kejadian", "Kategori Suhu Ekstrem (°C)"), use_container_width=True)
        st.dataframe(df_tmaxmin.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error("⚠️ Berkas `rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx` tidak ditemukan di folder 'data'.")
