import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. Konfigurasi Awal ---
# Path merujuk ke folder data di GitHub
file_path = 'data/rata_rata_persentase_temperature_2021_2025.xlsx'

# Daftar bulan untuk Sumbu X dan nama Sheet
bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
         'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# Definisi Kategori: Nama Label, Indeks Kolom Pandas, dan Warna Garis
kategori_suhu = {
    '5 - 0':   {'col': 1, 'color': 'blue'},   # Kolom B
    '0 - 5':   {'col': 2, 'color': 'orange'}, # Kolom C
    '5 - 10':  {'col': 3, 'color': 'green'},  # Kolom D
    '10 - 15': {'col': 4, 'color': 'red'},    # Kolom E
    '15 - 20': {'col': 5, 'color': 'purple'}, # Kolom F
    '20 - 25': {'col': 6, 'color': 'brown'},  # Kolom G
    '25 - 30': {'col': 7, 'color': 'pink'},   # Kolom H
    '30 - 35': {'col': 8, 'color': 'gray'},   # Kolom I
    '> 35':    {'col': 9, 'color': 'yellow'}  # Kolom J
}

# Mengambil data di baris ke-251 Excel (indeks 249 di Pandas)
indeks_baris = 249 

# Wadah kosong untuk menyimpan data fluktuasi
data_plot = {kat: [] for kat in kategori_suhu.keys()}

# --- 2. Looping Membaca Excel ---
try:
    # Membaca seluruh sheet sekaligus
    xls = pd.read_excel(file_path, sheet_name=None)
    
    # Looping per bulan
    for b in bulan:
        df_bulan = xls[b]
        
        # Ekstrak data untuk setiap kategori suhu
        for kat, properti in kategori_suhu.items():
            nilai = round(float(df_bulan.iloc[indeks_baris, properti['col']]), 2)
            data_plot[kat].append(nilai)

    # --- 3. Membuat Visualisasi Plot ---
    st.set_page_config(page_title="Dashboard ACS", layout="wide")
    st.title("Dashboard Aerodrome Climatological Summary")
    st.subheader("Persentase Temperatur Bulanan Tahun 2021-2025")

    # Inisialisasi kanvas Matplotlib
    fig, ax = plt.subplots(figsize=(12, 6))

    # Looping menggambar garis
    for kat, properti in kategori_suhu.items():
        ax.plot(
            bulan, 
            data_plot[kat], 
            marker='o', 
            color=properti['color'], 
            label=kat,
            linewidth=2
        )

    # Modifikasi tampilan grafik
    ax.set_xlabel('Bulan', fontsize=12, fontweight='bold')
    ax.set_ylabel('Persentase Kejadian (%)', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # Legenda di luar grafik
    ax.legend(title='Kategori Temperatur', bbox_to_anchor=(1.02, 1), loc='upper left')
    
    plt.tight_layout()

    # Tampilkan plot di Streamlit
    st.pyplot(fig)

except FileNotFoundError:
    st.error("File Excel tidak ditemukan. Pastikan file berada di dalam folder 'data/' dengan nama yang tepat.")
except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
