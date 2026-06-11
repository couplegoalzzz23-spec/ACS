import streamlit as st
import pandas as pd
import os

# Konfigurasi halaman agar tampilannya rapi
st.set_page_config(page_title="Dashboard ACS", layout="wide")

st.title("📊 Dashboard ACS")
st.markdown("Dashboard ini menampilkan data dari folder `data` secara otomatis.")

# Fungsi untuk memuat data
# @st.cache_data akan menyimpan data di memori agar dashboard tidak lemot saat dibuka
@st.cache_data
def load_all_data():
    all_data = {}
    data_folder = 'data'
    
    # Cek apakah folder ada
    if os.path.exists(data_folder):
        for filename in os.listdir(data_folder):
            if filename.endswith(".xlsx"):
                path = os.path.join(data_folder, filename)
                # Membaca file excel
                all_data[filename] = pd.read_excel(path)
    return all_data

# Memuat data
data_dict = load_all_data()

# Sidebar untuk navigasi file
if data_dict:
    st.sidebar.header("Pengaturan")
    selected_file = st.sidebar.selectbox("Pilih File ACS untuk ditampilkan:", list(data_dict.keys()))

    # Menampilkan data sesuai pilihan
    st.subheader(f"Menampilkan: {selected_file}")
    df = data_dict[selected_file]
    
    # Menampilkan tabel
    st.dataframe(df, use_container_width=True)
    
    # Menampilkan statistik singkat
    with st.expander("Lihat Statistik Data"):
        st.write(df.describe())
else:
    st.error("Folder 'data' tidak ditemukan atau kosong. Pastikan Anda sudah mengunggah folder 'data' ke GitHub.")
