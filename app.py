import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. KONFIGURASI HALAMAN UTAMA DASHBOARD
st.set_page_config(
    page_title="Dashboard ACS Terintegrasi BMKG", 
    layout="wide", 
    page_icon="🌤️"
)

st.title("📊 Dashboard Aerodrome Climatological Summary (ACS)")
st.subheader("Analisis Klimatologi Cuaca Operasional Pangkalan Udara Periode 2021-2025")
st.markdown("---")

# Urutan bulan standar untuk sumbu X grafik
months_ordered = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# 2. ENGINE PEMBACA DATA ADAPTIF & TAHAN BANTING (Auto-Detect Header & Summary Row)
@st.cache_data
def load_acs_robust_data(file_name):
    # Memastikan sistem mencari berkas di dalam folder 'data' maupun root
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

    # Antisipasi variasi penamaan sheet bulan pada dokumen Excel
    month_variants = {
        'Januari': ['jan', '01'], 'Februari': ['feb', '02'], 'Maret': ['mar', '03'],
        'April': ['apr', '04'], 'Mei': ['mei', 'may', '05'], 'Juni': ['jun', '06'],
        'Juli': ['jul', '07'], 'Agustus': ['agu', 'aug', '08'], 'September': ['sep', '09'],
        'Oktober': ['okt', 'oct', '10'], 'November': ['nov', '11'], 'Desember': ['des', 'dec', '12']
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
            
        # Pembersihan awal baris kosong
        df = df.dropna(how='all').reset_index(drop=True)
        if df.empty:
            continue
            
        # TAHAP A: Deteksi Dinamis Baris Judul Kolom (Kategori/Batas Parameter)
        header_idx = -1
        for idx in range(min(15, len(df))):
            val_0 = str(df.iloc[idx, 0]).strip().lower()
            if any(kw in val_0 for kw in ['(gmt)', 'gmt', 'jam', 'waktu', 'kategori', 'arah']):
                header_idx = idx
                break
        if header_idx == -1:
            header_idx = df.iloc[:10].notna().sum(axis=1).idxmax()
            
        # TAHAP B: Deteksi Dinamis Baris Ringkasan Akhir (Summary Row)
        target_idx = -1
        keywords_summary = ['mean', 'rata', 'jumlah', 'total', 'average', 'sum']
        
        for idx in range(header_idx + 1, len(df)):
            val_0 = str(df.iloc[idx, 0]).strip().lower()
            if any(kw in val_0 for kw in keywords_summary):
                target_idx = idx
                break
                
        # Kebijakan Cadangan (Fallback): Ambil baris berisi angka terdalam sebelum teks footer nama pembuat
        if target_idx == -1:
            for idx in range(len(df) - 1, header_idx, -1):
                row_slice = df.iloc[idx, 1:]
                numeric_values = pd.to_numeric(row_slice, errors='coerce').dropna()
                if len(numeric_values) >= (len(df.columns) - 1) * 0.4 and len(numeric_values) > 0:
                    target_idx = idx
                    break
                    
        if target_idx == -1 or header_idx >= target_idx:
            continue
            
        # TAHAP C: Ekstraksi Nilai Kolom Klimatologi
        month_dict = {}
        for col_idx in range(1, len(df.columns)):
            cat_val = df.iloc[header_idx, col_idx]
            if pd.isna(cat_val) or str(cat_val).strip().lower() in ['nan', 'unnamed', '']:
                continue
                
            cat_name = str(cat_val).strip()
            data_val = df.iloc[target_idx, col_idx]
            
            try:
                val_float = float(data_val)
                if pd.isna(val_float) or val_float > 100000:
                    val_float = 0.0
            except (ValueError, TypeError):
                val_float = 0.0
                
            month_dict[cat_name] = val_float
            if cat_name not in master_categories:
                master_categories.append(cat_name)
                
        all_months_data[m_name] = month_dict

    if not all_months_data:
        return None

    # TAHAP D: Rekonstruksi Matriks Data 12 Bulan Sempurna Tanpa Nilai Kosong
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

# 3. FUNGSI RENDER VISUALISASI (MENIRU SEMPURNA DESAIN TEMPERATUR)
def render_parameter_tab(title, file_name, y_label, variable_label):
    st.markdown(f"### 📊 {title}")
    df = load_acs_robust_data(file_name)
    
    if df is not None and not df.empty:
        # Pembuatan grafik garis interaktif Plotly
        fig = px.line(df, x=df.index, y=df.columns, markers=True,
                      labels={'index': 'Bulan', 'value': y_label, 'variable': variable_label},
                      template="plotly_white")
        fig.update_layout(
            hovermode="x unified", 
            plot_bgcolor='rgba(0,0,0,0)', 
            height=480,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(235,235,235,0.8)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(235,235,235,0.8)')
        
        st.plotly_chart(fig, use_container_width=True)
        # Menampilkan tabel data terformat presisi dua angka di belakang koma
        st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error(f"⚠️ Berkas data `{file_name}` tidak ditemukan di dalam folder 'data' atau format struktur tabel internal tidak sesuai.")

# 4. ANTARMUKA SISTEM TAB NAVIGASI YANG RAPI & SERAGAM
tabs = st.tabs([
    "🌡️ Temperatur", 
    "👁️ Visibility", 
    "☁️ Cloud Height (HS)", 
    "💨 Wind Speed", 
    "💧 Relative Humidity (RH)", 
    "📈 Temp Max & Min"
])

with tabs[0]:
    render_parameter_tab("Distribusi Persentase Temperatur Bulanan (2021-2025)", 
                         "rata_rata_persentase_temperature_2021_2025.xlsx", 
                         "Persentase (%)", "Rentang Suhu (°C)")

with tabs[1]:
    render_parameter_tab("Distribusi Persentase Visibility Bulanan (2021-2025)", 
                         "rata_rata_persentase_visibility_2021_2025.xlsx", 
                         "Persentase (%)", "Jarak Pandang (m)")

with tabs[2]:
    render_parameter_tab("Distribusi Persentase Cloud Height Bulanan (2021-2025)", 
                         "rata_rata_persentase_hs_2021_2025.xlsx", 
                         "Persentase (%)", "Tinggi Awan (ft)")

with tabs[3]:
    render_parameter_tab("Distribusi Persentase Wind Speed Bulanan (2021-2025)", 
                         "rata_rata_persentase_ws_2021_2025.xlsx", 
                         "Persentase (%)", "Kecepatan Angin (Kt)")

with tabs[4]:
    render_parameter_tab("Rata-rata Jumlah Kejadian Masuk Rentang RH Bulanan (2021-2025)", 
                         "rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx", 
                         "Jumlah Kejadian", "Rentang Kelembapan (%)")

with tabs[5]:
    render_parameter_tab("Rata-rata Jumlah Kejadian Masuk Rentang Temp Maks/Min Bulanan (2021-2025)", 
                         "rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx", 
                         "Jumlah Kejadian", "Kategori Suhu Ekstrem (°C)")
