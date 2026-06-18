import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================================
# 1. KONFIGURASI HALAMAN WEB
# ==========================================
st.set_page_config(
    page_title="Dashboard ACS Terintegrasi", 
    layout="wide", 
    page_icon="🌤️"
)

st.title("🌤️ Dashboard Aerodrome Climatological Summary (ACS)")
st.subheader("Analisis Klimatologi Cuaca Operasional Periode 2021-2025")
st.markdown("---")

months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# ==========================================
# 2. FUNGSI EKSTRAKSI DATA AKURAT & PRESISI
# ==========================================
@st.cache_data(show_spinner=False)
def load_acs_generic_data(file_path):
    """
    Membaca file Excel ACS dengan pencarian jangkar (anchor) baris header 
    dan baris rata-rata secara presisi untuk menjamin tidak ada kolom teks 
    seperti '< 1800' yang hilang.
    """
    if not os.path.exists(file_path):
        return None, None
        
    try:
        xls = pd.ExcelFile(file_path)
        actual_sheets = xls.sheet_names
    except Exception:
        return None, None

    # --- TAHAP 1: MENGUNCI STRUKTUR HEADER SECARA PRESISI ---
    sample_sheet = next((s for s in actual_sheets if any(m.lower() in s.lower() for m in months)), actual_sheets[0])
    df_sample = pd.read_excel(file_path, sheet_name=sample_sheet, header=None)
    
    header_row_idx = -1
    
    # Metode Utama: Cari baris yang kolom pertamanya mengandung indikator waktu baku
    for r in range(min(20, len(df_sample))):
        val0 = str(df_sample.iloc[r, 0]).strip().upper()
        if any(k in val0 for k in ['(GMT)', 'GMT', 'UTC', 'JAM', 'WIB', 'HOUR']):
            header_row_idx = r
            break
            
    # Metode Cadangan 1: Cari kata kunci waktu di seluruh sel pada 15 baris pertama
    if header_row_idx == -1:
        for r in range(min(15, len(df_sample))):
            row_vals = df_sample.iloc[r].dropna().astype(str).str.upper().tolist()
            if any(any(k in cell for k in ['(GMT)', 'GMT', 'UTC', 'JAM']) for cell in row_vals):
                header_row_idx = r
                break
                
    # Metode Cadangan 2: Cari baris awal jam data (0 atau 00) dan ambil baris di atasnya
    if header_row_idx == -1:
        for r in range(len(df_sample)):
            val0 = str(df_sample.iloc[r, 0]).strip()
            if val0 in ['0', '00', '1', '01']:
                header_row_idx = r - 1
                break
                
    # Jika seluruh pencarian gagal, gunakan batas default standar acuan instansi
    if header_row_idx == -1:
        header_row_idx = 4

    # Petakan indeks kolom asli ke nama kategorinya agar urutan tidak tertukar
    category_map = {}
    for c in range(1, len(df_sample.columns)):
        val = df_sample.iloc[header_row_idx, c]
        if pd.notna(val) and str(val).strip() != '':
            category_map[c] = str(val).strip()
            
    categories = list(category_map.values())

    if not categories:
        return None, None

    # --- TAHAP 2: EKSTRAKSI NILAI SUMMARY BERDASARKAN KATEGORI ---
    data_kategori = {k: [] for k in categories}
    
    for month in months:
        matched_sheet = next((s for s in actual_sheets if month.lower() in s.lower()), None)
        
        if matched_sheet:
            try:
                df = pd.read_excel(file_path, sheet_name=matched_sheet, header=None)
                
                # Cari baris nilai rata-rata bulanan (Scan dari bawah ke atas)
                target_row_idx = -1
                for r in reversed(df.index):
                    val0 = str(df.iloc[r, 0]).strip().upper()
                    if any(k in val0 for k in ['MEAN', 'RATA', 'AVERAGE', 'AVG']):
                        target_row_idx = r
                        break
                        
                # Jika label 'MEAN' hilang, cari baris terbawah yang berisi data numerik valid
                if target_row_idx == -1:
                    for r in reversed(df.index):
                        has_numeric = False
                        for c in category_map.keys():
                            if c < len(df.columns):
                                val = df.iloc[r, c]
                                if pd.notna(val) and isinstance(val, (int, float)):
                                    has_numeric = True
                                    break
                        if has_numeric:
                            target_row_idx = r
                            break
                
                # Masukkan nilai ke dalam struktur data dashboard
                if target_row_idx != -1:
                    for c, kategori in category_map.items():
                        if c < len(df.columns):
                            val = df.iloc[target_row_idx, c]
                            try:
                                val = float(val)
                                if pd.isna(val): 
                                    val = 0.0
                            except (ValueError, TypeError):
                                val = 0.0
                            data_kategori[kategori].append(round(val, 2))
                        else:
                            data_kategori[kategori].append(0.0)
                else:
                    for k in categories: data_kategori[k].append(0.0)
                    
            except Exception:
                for k in categories: data_kategori[k].append(0.0)
        else:
            for k in categories: data_kategori[k].append(0.0)
            
    return pd.DataFrame(data_kategori, index=months), categories


# ==========================================
# 3. FUNGSI RENDER ANTARMUKA (UI)
# ==========================================
def render_parameter_ui(file_name, title, y_label, variable_label):
    file_path = os.path.join("data", file_name)
    
    st.markdown(f"### {title}")
    
    with st.spinner('Memproses data klimatologi operasional...'):
        df, categories = load_acs_generic_data(file_path)
    
    if df is not None and not df.empty:
        # Pembuatan Grafik Garis Interaktif menggunakan Plotly Express
        fig = px.line(
            df, 
            x=df.index, 
            y=df.columns, 
            markers=True,
            labels={'index': 'Bulan', 'value': y_label, 'variable': variable_label}
        )
        fig.update_layout(
            hovermode="x unified", 
            plot_bgcolor='rgba(0,0,0,0)', 
            height=500,
            legend=dict(title=variable_label, orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.2)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.2)')
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Pembuatan Tabel Historis di Bawah Grafik (Persis Desain app.py 57)
        st.markdown("#### Tabel Data Historis")
        st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error(f"⚠️ Gagal memproses data dari file: `{file_name}`")
        st.info("💡 Pastikan file Excel tersebut berada di dalam direktori `data/` pada repositori GitHub Anda.")


# ==========================================
# 4. SISTEM NAVIGASI TAB UTAMA
# ==========================================
tabs = st.tabs([
    "🌡️ Temperatur", 
    "👁️ Visibility", 
    "☁️ Cloud Height (HS)", 
    "💨 Wind Speed (WS)", 
    "💧 Relative Humidity (RH)", 
    "📈 Maks & Min Temp"
])

with tabs[0]:
    render_parameter_ui(
        file_name='rata_rata_persentase_temperature_2021_2025.xlsx',
        title='Distribusi Persentase Temperatur Bulanan',
        y_label='Persentase (%)',
        variable_label='Rentang Suhu (°C)'
    )

with tabs[1]:
    render_parameter_ui(
        file_name='rata_rata_persentase_visibility_2021_2025.xlsx',
        title='Distribusi Persentase Visibility Bulanan',
        y_label='Persentase (%)',
        variable_label='Rentang Jarak (m)'
    )

with tabs[2]:
    render_parameter_ui(
        file_name='rata_rata_persentase_hs_2021_2025.xlsx',
        title='Distribusi Persentase Tinggi Awan (Cloud Height)',
        y_label='Persentase (%)',
        variable_label='Rentang Tinggi (ft)'
    )

with tabs[3]:
    render_parameter_ui(
        file_name='rata_rata_persentase_ws_2021_2025.xlsx',
        title='Distribusi Persentase Kecepatan Angin',
        y_label='Persentase (%)',
        variable_label='Kecepatan Angin (knots)'
    )

with tabs[4]:
    render_parameter_ui(
        file_name='rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx',
        title='Rata-rata Kejadian Relative Humidity (RH)',
        y_label='Jumlah Kejadian',
        variable_label='Rentang Kelembapan (%)'
    )

with tabs[5]:
    render_parameter_ui(
        file_name='rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx',
        title='Rata-rata Kejadian Suhu Maksimum dan Minimum',
        y_label='Jumlah Kejadian',
        variable_label='Kategori Suhu (°C)'
    )
