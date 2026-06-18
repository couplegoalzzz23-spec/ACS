import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================================
# 1. KONFIGURASI HALAMAN UTAMA
# ==========================================
st.set_page_config(
    page_title="Dashboard ACS Terintegrasi BMKG",
    layout="wide",
    page_icon="🌤️"
)

st.title("🌤️ Dashboard Aerodrome Climatological Summary (ACS)")
st.subheader("Analisis Klimatologi Cuaca Operasional Terintegrasi (Periode 2021-2025)")
st.markdown("---")

months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# ==========================================
# 2. FUNGSI PENCARI FILE OTOMATIS
# ==========================================
def find_excel_file(keyword, default_filename):
    """
    Mencari file secara dinamis di dalam folder 'data' berdasarkan kata kunci.
    Mencegah error jika terjadi perbedaan kecil pada penamaan file di GitHub.
    """
    folder = "data"
    if os.path.exists(folder):
        for file in os.listdir(folder):
            if file.endswith(".xlsx") and keyword.lower() in file.lower():
                return os.path.join(folder, file)
    return os.path.join(folder, default_filename)

# ==========================================
# 3. ENGINE EKSTRAKSI DATA (SMART SCANNER)
# ==========================================
@st.cache_data(show_spinner=False)
def load_acs_generic_data(file_path):
    if not file_path or not os.path.exists(file_path):
        return None, None
        
    try:
        xls = pd.ExcelFile(file_path)
        actual_sheets = xls.sheet_names
    except Exception:
        return None, None

    # Cari sheet pertama yang berisi data bulan untuk memetakan struktur kolom
    sample_sheet = None
    for m in months:
        for s in actual_sheets:
            if m.lower() in s.lower() or s.lower() in m.lower():
                sample_sheet = s
                break
        if sample_sheet:
            break
    
    if not sample_sheet:
        sample_sheet = actual_sheets[0]
        
    try:
        df_sample = pd.read_excel(file_path, sheet_name=sample_sheet, header=None)
    except Exception:
        return None, None

    # --- TAHAP 1: DETEKSI BARIS HEADER KATEGORI SECARA AGRESIF ---
    header_row_idx = None
    for r in range(min(20, len(df_sample))):
        val0 = str(df_sample.iloc[r, 0]).strip().upper()
        # Jika kolom pertama berisi penanda waktu standar
        if any(k in val0 for k in ['GMT', 'UTC', 'JAM', 'HOUR', 'TIME']):
            header_row_idx = r
            break
            
    # Fallback Pintar: Jika tidak ada teks penanda, cari baris tepat di atas urutan jam '00' atau '0'
    if header_row_idx is None:
        for r in range(min(15, len(df_sample) - 1)):
            next_val0 = str(df_sample.iloc[r+1, 0]).strip()
            if next_val0 in ['0', '00', '1', '01']:
                header_row_idx = r
                break
                
    if header_row_idx is None:
        header_row_idx = 0

    # Ambil nama kategori/rentang kolom (mulai kolom indeks 1 hingga akhir)
    categories = []
    for c in range(1, len(df_sample.columns)):
        val = df_sample.iloc[header_row_idx, c]
        if pd.notna(val) and str(val).strip() != '':
            categories.append(str(val).strip())

    # Penanganan jika ada nama kolom ganda agar grafik Plotly tidak crash
    unique_categories = []
    for c in categories:
        if c not in unique_categories:
            unique_categories.append(c)
        else:
            unique_categories.append(f"{c} (2)")
    categories = unique_categories

    if not categories:
        return None, None

    # --- TAHAP 2: PROSES EKSTRAKSI DATA BULANAN ---
    data_dict = {k: [] for k in categories}
    
    for month in months:
        matched_sheet = None
        for s in actual_sheets:
            if month.lower() in s.lower() or s.lower() in month.lower():
                matched_sheet = s
                break
        
        if matched_sheet:
            try:
                df = pd.read_excel(file_path, sheet_name=matched_sheet, header=None)
                
                # Cari baris nilai rata-rata (Scan terbalik dari baris paling bawah)
                target_row = None
                for r in reversed(df.index):
                    val0 = str(df.iloc[r, 0]).strip().upper()
                    if any(k in val0 for k in ['MEAN', 'RATA', 'AVERAGE', 'JUMLAH', 'TOTAL', 'SUMMARY']):
                        target_row = r
                        break
                        
                # Fallback jika label kata tidak ditemukan, ambil baris data numerik paling akhir
                if target_row is None:
                    for r in reversed(df.index):
                        if r > header_row_idx and pd.notna(df.iloc[r, 1]):
                            try:
                                float(df.iloc[r, 1])
                                target_row = r
                                break
                            except ValueError:
                                continue
                
                # Masukkan nilai ke matriks data
                if target_row is not None:
                    for col_idx, kategori in enumerate(categories, start=1):
                        if col_idx < len(df.columns):
                            val = df.iloc[target_row, col_idx]
                            try:
                                val = float(val)
                                if pd.isna(val):
                                    val = 0.0
                            except (ValueError, TypeError):
                                val = 0.0
                            data_dict[kategori].append(round(val, 2))
                        else:
                            data_dict[kategori].append(0.0)
                else:
                    for k in categories:
                        data_dict[k].append(0.0)
            except Exception:
                for k in categories:
                    data_dict[k].append(0.0)
        else:
            for k in categories:
                data_dict[k].append(0.0)
                
    return pd.DataFrame(data_dict, index=months), categories

# ==========================================
# 4. FUNGSI PEMBUAT ANTARMUKA (UI)
# ==========================================
def render_parameter_ui(keyword, default_filename, title, y_label, variable_label):
    file_path = find_excel_file(keyword, default_filename)
    
    st.markdown(f"### {title}")
    
    if not os.path.exists(file_path):
        st.error(f"⚠️ File data tidak ditemukan di folder `data/`.")
        st.info(f"Pastikan file Excel yang mengandung kata kunci `{keyword}` sudah berada di dalam folder `data/` repositori GitHub Anda.")
        return

    with st.spinner(f"Sedang menyusun visualisasi {title}..."):
        df, categories = load_acs_generic_data(file_path)
        
    if df is not None and not df.empty:
        # Pembuatan Grafik Garis Interaktif
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
            xaxis=dict(title="Bulan"),
            yaxis=dict(title=y_label),
            legend=dict(title=variable_label, orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Pembuatan Tabel Distribusi Data
        st.markdown("#### Tabel Data Historis")
        st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error(f"⚠️ Format data di dalam file `{os.path.basename(file_path)}` tidak dapat dikenali.")
        st.info("Silakan periksa apakah file tersebut kosong atau struktur tabelnya berbeda dari standar format ACS.")

# ==========================================
# 5. STRUKTUR NAVIGASI TAB UTAMA
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
        keyword="temperature",
        default_filename="rata_rata_persentase_temperature_2021_2025.xlsx",
        title="Distribusi Persentase Temperatur Bulanan",
        y_label="Persentase (%)",
        variable_label="Rentang Suhu (°C)"
    )

with tabs[1]:
    render_parameter_ui(
        keyword="visibility",
        default_filename="rata_rata_persentase_visibility_2021_2025.xlsx",
        title="Distribusi Persentase Visibility Bulanan",
        y_label="Persentase (%)",
        variable_label="Rentang Jarak Pandang"
    )

with tabs[2]:
    render_parameter_ui(
        keyword="hs",
        default_filename="rata_rata_persentase_hs_2021_2025.xlsx",
        title="Distribusi Persentase Tinggi Awan (Cloud Height)",
        y_label="Persentase (%)",
        variable_label="Rentang Tinggi Dasar Awan (ft)"
    )

with tabs[3]:
    render_parameter_ui(
        keyword="ws",
        default_filename="rata_rata_persentase_ws_2021_2025.xlsx",
        title="Distribusi Persentase Kecepatan Angin (Wind Speed)",
        y_label="Persentase (%)",
        variable_label="Kecepatan Angin (knots)"
    )

with tabs[4]:
    render_parameter_ui(
        keyword="rh",
        default_filename="rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx",
        title="Rata-rata Kejadian Relative Humidity (RH)",
        y_label="Jumlah Kejadian",
        variable_label="Rentang Kelembapan (%)"
    )

with tabs[5]:
    render_parameter_ui(
        keyword="tmaxmin",
        default_filename="rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx",
        title="Rata-rata Kejadian Suhu Maksimum & Minimum",
        y_label="Jumlah Kejadian",
        variable_label="Kategori Batas Suhu (°C)"
    )
