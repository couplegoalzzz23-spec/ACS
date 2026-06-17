import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. Konfigurasi Awal ---
# Path disesuaikan dengan struktur folder baru di GitHub Anda
file_path = 'data/rata_rata_persentase_temperature_2021_2025.xlsx'

# Daftar bulan yang akan menjadi Sumbu X sekaligus nama Sheet di Excel
bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
         'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# Definisi Kategori: Nama Label, Indeks Kolom Pandas, dan Warna Garis
# Catatan Pandas: Kolom A = 0, B = 1, C = 2, dst.
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

# Penyesuaian Baris: Jika di Excel Anda membaca baris 251 dan baris 1 adalah Header,
# maka di Pandas indeksnya berkurang 2 (karena Python dimulai dari 0).
indeks_baris = 249 

# Menyiapkan wadah (dictionary) kosong untuk menyimpan data fluktuasi 12 bulan
data_plot = {kat: [] for kat in kategori_suhu.keys()}

# --- 2. Looping Membaca Excel ---
# Membaca seluruh sheet sekaligus agar prosesnya jauh lebih cepat
try:
    xls = pd.read_excel(file_path, sheet_name=None)
    
    # Looping untuk setiap bulan (sheet)
    for b in bulan:
        df_bulan = xls[b] # Mengambil dataframe sesuai nama bulan
        
        # Looping untuk mengekstrak nilai di setiap kategori/kolom pada baris ke-251
        for kat, properti in kategori_suhu.items():
            # Mengambil data, memastikan formatnya angka (float), lalu bulatkan 2 desimal
            nilai = round(float(df_bulan.iloc[indeks_baris, properti['col']]), 2)
            data_plot[kat].append(nilai)

    # --- 3. Membuat Visualisasi Plot ---
    st.title("Dashboard Aerodrome Climatological Summary")
    st.subheader("Persentase Temperatur Bulanan Tahun 2021-2025")

    # Inisialisasi kanvas Matplotlib
    fig, ax = plt.subplots(figsize=(12, 6))

    # Looping untuk menggambar garis plot masing-masing kategori
    for kat, properti in kategori_suhu.items():
        ax.plot(
            bulan, 
            data_plot[kat], 
            marker='o', 
            color=properti['color'], 
            label=kat,
            linewidth=2
        )

    # Mempercantik tampilan grafik
    ax.set_xlabel('Bulan', fontsize=12, fontweight='bold')
    ax.set_ylabel('Persentase Kejadian (%)', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # Meletakkan legenda di luar grafik agar garis tidak tertutupi
    ax.legend(title='Kategori Temperatur', bbox_to_anchor=(1.02, 1), loc='upper left')
    
    plt.tight_layout()

    # Menampilkan plot ke antarmuka web Streamlit
    st.pyplot(fig)

except Exception as e:
    st.error(f"Terjadi kesalahan saat membaca file atau membuat plot: {e}")
