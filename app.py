import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Konfigurasi halaman utama web
st.set_page_config(
    page_title="Dashboard Klimatologi Bandara",
    layout="wide",
    page_icon="📊"
)

st.title("🛫 Dashboard Interaktif Data Klimatologi Operasional (2021-2025)")
st.markdown("Aplikasi web untuk visualisasi dinamis *Aerodrome Climatological Summary* (ACS) dan data parameter cuaca.")

# Urutan bulan standar meteorologi untuk sumbu X yang rapi
URUTAN_BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni", 
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

# ==================== SIDEBAR & MENU KONTROL ====================
st.sidebar.header("⚙️ Pengaturan & Unggah Data")

sumber_data = st.sidebar.radio(
    "Pilih Sumber Data:",
    ["Data Repositori (Folder 'data')", "Unggah Manual File ACS Baru"]
)

@st.cache_data
def proses_file_excel(file_source):
    """Membaca file Excel secara aman dan menggabungkan sheet bulanan."""
    try:
        xl = pd.ExcelFile(file_source)
        all_sheets = xl.sheet_names
        df_list = []
        
        for sheet in all_sheets:
            df_sheet = pd.read_excel(file_source, sheet_name=sheet)
            df_sheet = df_sheet.dropna(how='all')
            if not df_sheet.empty:
                # Jika nama sheet adalah nama bulan, jadikan sebagai kolom 'Bulan'
                if len(all_sheets) > 1:
                    df_sheet['Bulan'] = sheet
                df_list.append(df_sheet)
                
        if df_list:
            df_gabungan = pd.concat(df_list, ignore_index=True)
            df_gabungan.columns = df_gabungan.columns.astype(str)
            return df_gabungan
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal memproses file Excel: {e}")
        return pd.DataFrame()

df_utama = pd.DataFrame()
nama_parameter = ""

# ==================== LOGIKA PENYEDIAAN DATA ====================
if sumber_data == "Data Repositori (Folder 'data')":
    FOLDER_DATA = "data"
    if os.path.exists(FOLDER_DATA):
        daftar_file = [f for f in os.listdir(FOLDER_DATA) if f.endswith(('.xlsx', '.xls'))]
        if daftar_file:
            pilihan_file = st.sidebar.selectbox("Pilih Parameter Meteorologi:", sorted(daftar_file))
            path_file = os.path.join(FOLDER_DATA, pilihan_file)
            df_utama = proses_file_excel(path_file)
            nama_parameter = pilihan_file.replace("rata_rata_", "").replace("_2021_2025.xlsx", "").upper()
        else:
            st.sidebar.warning("Tidak ada file .xlsx di dalam folder 'data'.")
    else:
        st.sidebar.error(f"Folder '{FOLDER_DATA}' tidak ditemukan.")
else:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 Unggah File ACS Baru")
    uploaded_file = st.sidebar.file_uploader("Pilih file Excel format (.xlsx):", type=["xlsx"])
    if uploaded_file is not None:
        df_utama = proses_file_excel(uploaded_file)
        nama_parameter = uploaded_file.name.split(".")[0].upper()
        st.sidebar.success("Data manual berhasil dimuat!")

# ==================== ANTARMUKA VISUALISASI DATA ====================
if not df_utama.empty:
    st.subheader(f"📈 Grafik Tren Bulanan: {nama_parameter}")
    
    semua_kolom = df_utama.columns.tolist()
    kolom_numerik = df_utama.select_dtypes(include=['number']).columns.tolist()
    if 'Tahun' in kolom_numerik:
        kolom_numerik.remove('Tahun')
        
    col1, col2 = st.columns(2)
    with col1:
        sumbu_y = st.selectbox("Pilih Nilai Parameter (Sumbu Y):", options=kolom_numerik if kolom_numerik else semua_kolom)
    with col2:
        # Memastikan pembeda garis berdasarkan Tahun jika ada
        pembeda_warna = st.selectbox("Pembeda Garis (Legenda):", options=['Tahun'] + [k for k in semua_kolom if k != 'Tahun'] if 'Tahun' in semua_kolom else semua_kolom)

    # Memastikan kolom 'Bulan' mengikuti urutan kronologis agar grafik runut dari Jan-Des
    if 'Bulan' in semua_kolom:
        df_utama['Bulan'] = pd.Categorical(df_utama['Bulan'], categories=URUTAN_BULAN, ordered=True)
        df_utama = df_utama.sort_values('Bulan')

    # Konversi kolom legenda menjadi string agar Plotly memperlakukannya sebagai kategori (bukan gradasi warna numerik)
    if pembeda_warna in df_utama.columns:
        df_utama[pembeda_warna] = df_utama[pembeda_warna].astype(str)

    # Pembuatan Grafik Garis Interaktif ala Publikasi Ilmiah / BMKG
    try:
        fig = px.line(
            df_utama, 
            x='Bulan' if 'Bulan' in semua_kolom else semua_kolom[0], 
            y=sumbu_y, 
            color=pembeda_warna,
            markers=True,  # Menampilkan titik/bullet di setiap bulan seperti gambar contoh Anda
            title=f"Distribusi Rata-Rata {sumbu_y} Berdasarkan Bulan (2021-2025)",
            template="plotly_white"  # Background putih bersih agar kontras warna terlihat jelas
        )
        
        # Kustomisasi Layout agar Mirip Gambar Contoh (Garis grid tipis, teks jelas)
        fig.update_layout(
            hovermode="x unified",  # Menampilkan semua nilai tahun sekaligus saat kursor digeser di satu bulan
            xaxis_title="Bulan",
            yaxis_title=sumbu_y,
            font=dict(family="Arial", size=12),
            legend_title_text=pembeda_warna,
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        # Mengaktifkan grid abu-abu tipis
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
        
        # Tampilkan grafik ke aplikasi web
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as graph_err:
        st.error(f"Gagal membuat grafik: {graph_err}")

    # Data Mentah
    with st.expander("🔍 Periksa Lembar Tabel Data Mentah (Spreadsheet)"):
        st.dataframe(df_utama, use_container_width=True)
