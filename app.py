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
    page_icon="🌤️",
    initial_sidebar_state="expanded"
)

st.title("🌤️ Dashboard Aerodrome Climatological Summary (ACS)")
st.subheader("Analisis Klimatologi Cuaca Operasional Periode 2021-2025")
st.markdown("---")

months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# ==========================================
# 2. FUNGSI EKSTRAKSI DATA (CACHED)
# ==========================================
@st.cache_data(show_spinner=False)
def load_acs_generic_data(file_path):
    """
    Fungsi tahan banting untuk membaca data Excel.
    Menggunakan caching agar tidak perlu reload data berulang kali saat pindah tab.
    """
    if not os.path.exists(file_path):
        return None, None
        
    try:
        xls = pd.ExcelFile(file_path)
        actual_sheets = xls.sheet_names
    except Exception as e:
        return None, None

    # Cari sheet bulan pertama yang tersedia untuk mendeteksi kategori
    sample_sheet = next((s for s in actual_sheets if s.strip().lower() in [m.lower() for m in months]), actual_sheets[0])
    df_sample = pd.read_excel(file_path, sheet_name=sample_sheet, header=None)
    
    # Kunci pencarian hanya pada baris yang kolom pertamanya adalah '(GMT)'
    header_row_idx = df_sample[df_sample[0].astype(str).str.strip().str.upper() == '(GMT)'].index
    
    if len(header_row_idx) > 0:
        r = header_row_idx[0]
        # Mengambil semua nama rentang kategori (kolom 1 sampai akhir)
        categories = [str(df_sample.iloc[r, c]).strip() for c in range(1, len(df_sample.columns)) 
                      if pd.notna(df_sample.iloc[r, c]) and str(df_sample.iloc[r, c]).strip() != '']
    else:
        # Pilihan cadangan jika standar (GMT) tidak ditemukan
        categories = [f"Kategori {i}" for i in range(1, len(df_sample.columns))]

    # Buat wadah data untuk grafik
    data_kategori = {k: [] for k in categories}
    
    for month in months:
        matched_sheet = next((s for s in actual_sheets if s.strip().lower() == month.lower()), None)
        
        if matched_sheet:
            try:
                df = pd.read_excel(file_path, sheet_name=matched_sheet, header=None)
                # Cari baris MEAN periode gabungan 2021-2025 (paling bawah)
                mean_rows = df[df[0].astype(str).str.strip().str.upper() == 'MEAN'].index.tolist()
                
                if mean_rows:
                    target_row = mean_rows[-1]
                    for idx, kategori in enumerate(categories, start=1):
                        if idx < len(df.columns):
                            val = df.iloc[target_row, idx]
                            # Menghapus data anomali atau kosong
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
            
    return pd.DataFrame(data_kategori, index=months), categories


# ==========================================
# 3. FUNGSI PEMBUAT UI (MODULAR)
# ==========================================
def render_parameter_ui(file_name, title, y_label, variable_label):
    """
    Fungsi untuk merender grafik dan tabel secara dinamis.
    Ini mencegah penulisan kode berulang dan mempermudah debugging.
    """
    # Arahkan path langsung ke dalam folder 'data'
    file_path = os.path.join("data", file_name)
    
    st.markdown(f"### {title}")
    
    with st.spinner('Memuat data...'):
        df, categories = load_acs_generic_data(file_path)
    
    if df is not None and not df.empty:
        # Membuat Grafik Plotly
        fig = px.line(df, x=df.index, y=df.columns, markers=True,
                      labels={'index': 'Bulan', 'value': y_label, 'variable': variable_label})
        fig.update_layout(
            hovermode="x unified", 
            plot_bgcolor='rgba(0,0,0,0)', 
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Menampilkan Grafik
        st.plotly_chart(fig, use_container_width=True)
        
        # Menampilkan Tabel
        st.markdown("#### Tabel Data Historis")
        st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error(f"⚠️ Gagal memuat data untuk {title}.")
        st.info(f"💡 Pastikan file `{file_name}` sudah terunggah ke dalam folder `data/` di GitHub Anda dan formatnya sesuai standar ACS yang ditetapkan.")


# ==========================================
# 4. SISTEM TAB & NAVIGASI
# ==========================================
# Membuat 6 Tab sesuai dengan file yang ada di folder 'data' GitHub
tabs = st.tabs([
    "🌡️ Temperatur", 
    "👁️ Visibility", 
    "☁️ Cloud Height (HS)", 
    "💨 Wind Speed (WS)", 
    "💧 Relative Humidity (RH)", 
    "📈 Maks & Min Temp"
])

# Mapping setiap tab dengan fungsinya masing-masing
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
