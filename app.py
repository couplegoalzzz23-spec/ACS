import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Dashboard ACS BMKG", layout="wide", page_icon="🌤️")

# --- Judul Utama ---
st.title("🌤️ Dashboard Aerodrome Climatological Summary (ACS)")
st.markdown("Aplikasi Interaktif Analisis Data Klimatologi Operasional Penerbangan Tahun 2021-2025.")
st.divider() # PERBAIKAN: Menggunakan st.divider() sebagai pengganti st.hr()

# --- Sidebar Navigasi Parameter ---
st.sidebar.header("Navigasi Analisis")
parameter = st.sidebar.selectbox(
    "Pilih Parameter Cuaca:",
    [
        "Temperatur Bulanan",
        "Relative Humidity (RH)",
        "Temperatur Maksimum & Minimum",
        "Visibility (Jarak Pandang)",
        "Height of Cloud Base (HS)",
        "Wind Speed (Windrose)"
    ]
)

# Kontrol Baris Excel melalui Sidebar (Default: baris 251 di Excel -> indeks 249 di Pandas)
indeks_baris = st.sidebar.number_input(
    "Indeks Baris Data (Pandas)", 
    min_value=0, 
    max_value=500, 
    value=249,
    help="Sesuaikan jika posisi baris rata-rata summary berbeda di tiap file Excel."
)

# --- Mapping File & Pengaturan Parameter ---
config = {
    "Temperatur Bulanan": {
        "file": "data/rata_rata_persentase_temperature_2021_2025.xlsx",
        "title": "Persentase Distribusi Temperatur Bulanan Tahun 2021-2025",
        "ylabel": "Persentase Kejadian (%)",
        "type": "line"
    },
    "Relative Humidity (RH)": {
        "file": "data/rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx",
        "title": "Persentase Relative Humidity (RH) Bulanan Tahun 2021-2025",
        "ylabel": "Persentase Kejadian (%)",
        "type": "line"
    },
    "Temperatur Maksimum & Minimum": {
        "file": "data/rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx",
        "title": "Persentase Kejadian Temperatur Maksimum & Minimum Tahun 2021-2025",
        "ylabel": "Persentase Kejadian (%)",
        "type": "line"
    },
    "Visibility (Jarak Pandang)": {
        "file": "data/rata_rata_persentase_visibility_2021_2025.xlsx",
        "title": "Persentase Jarak Pandang (Visibility) Bulanan Tahun 2021-2025",
        "ylabel": "Persentase Kejadian (%)",
        "type": "line"
    },
    "Height of Cloud Base (HS)": {
        "file": "data/rata_rata_persentase_hs_2021_2025.xlsx",
        "title": "Persentase Height of Cloud Base (HS) Bulanan Tahun 2021-2025",
        "ylabel": "Persentase Kejadian (%)",
        "type": "line"
    },
    "Wind Speed (Windrose)": {
        "file": "data/rata_rata_persentase_ws_2021_2025.xlsx",
        "title": "Analisis Distribusi Arah dan Kecepatan Angin (Windrose) 2021-2025",
        "type": "windrose"
    }
}

current_cfg = config[parameter]
bulan_list = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
              'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# Palette warna standar untuk grafik garis dinamis
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

# --- Proses Membaca Data ---
try:
    xls = pd.read_excel(current_cfg["file"], sheet_name=None)
    
    # KONDISI 1: Untuk Parameter Berupa Grafik Garis (Temp, RH, Visibility, HS)
    if current_cfg["type"] == "line":
        # Ambil nama kategori kolom secara dinamis langsung dari sheet pertama (Kolom B sampai akhir)
        first_sheet = list(xls.keys())[0]
        kategori_kolom = [col for col in xls[first_sheet].columns if col != xls[first_sheet].columns[0]]
        
        data_plot = {kat: [] for kat in kategori_kolom}
        tabel_matrix = []

        # Looping ekstraksi data 12 bulan
        for b in bulan_list:
            if b in xls:
                df_bulan = xls[b]
                row_data = [b]
                for kat in kategori_kolom:
                    # Ambil nilai, konversi ke float, bulatkan 2 desimal
                    val = round(float(df_bulan[kat].iloc[indeks_baris]), 2)
                    data_plot[kat].append(val)
                    row_data.append(val)
                tabel_matrix.append(row_data)
        
        # Buat Dataframe untuk Tabel Detail
        df_tabel = pd.DataFrame(tabel_matrix, columns=['Bulan'] + kategori_kolom).set_index('Bulan')

        # --- Plotting Grafik Garis ---
        st.subheader(current_cfg["title"])
        fig, ax = plt.subplots(figsize=(12, 5.5))
        
        for idx, kat in enumerate(kategori_kolom):
            ax.plot(
                bulan_list, data_plot[kat], 
                marker='o', linewidth=2, 
                color=colors[idx % len(colors)], label=kat
            )
            
        ax.set_xlabel('Bulan', fontsize=11, fontweight='bold')
        ax.set_ylabel(current_cfg["ylabel"], fontsize=11, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend(title='Kategori/Kelas', bbox_to_anchor=(1.01, 1), loc='upper left')
        plt.tight_layout()
        st.pyplot(fig)

        # --- Menampilkan Tabel Detail ---
        st.markdown(f"#### 📊 Tabel Detail {current_cfg['title']}")
        st.dataframe(df_tabel, use_container_width=True)

    # KONDISI 2: Untuk Parameter Wind Speed (Menggunakan Grafik Polar / Windrose)
    elif current_cfg["type"] == "windrose":
        st.subheader(current_cfg["title"])
        
        # Pilihan Bulan khusus Windrose agar interaktif
        pilihan_bulan = st.selectbox("Pilih Bulan untuk Grafik Windrose:", bulan_list)
        
        if pilihan_bulan in xls:
            df_ws = xls[pilihan_bulan]
            
            # Bersihkan data kolom pertama sebagai indeks arah
            df_ws = df_ws.dropna(subset=[df_ws.columns[0]])
            arah_angin = df_ws.iloc[:, 0].astype(str).tolist()
            kelas_kecepatan = [col for col in df_ws.columns if col != df_ws.columns[0]]
            
            # --- Tampilkan Tabel Data Wind Terlebih Dahulu ---
            st.markdown(f"#### 📊 Tabel Data Distribusi Angin - Bulan {pilihan_bulan}")
            df_tabel_ws = df_ws.set_index(df_ws.columns[0])
            st.dataframe(df_tabel_ws.style.format(precision=2), use_container_width=True)
            
            # --- Plotting Windrose Menggunakan Proyeksi Polar Matplotlib ---
            N_arah = len(arah_angin)
            angles = np.linspace(0, 2 * np.pi, N_arah, endpoint=False).tolist()
            
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
            ax.set_theta_thetainterp('no-clipping')
            ax.set_theta_direction(-1) # Searah jarum jam
            ax.set_theta_offset(np.pi / 2.0) # Utara di atas
            
            # Set label arah mata angin pada koordinat polar
            plt.xticks(angles, arah_angin, fontsize=10, fontweight='bold')
            
            # Membuat susunan stacked bar untuk mewakili kelas kecepatan angin
            bottom_bars = np.zeros(N_arah)
            
            for idx, kelas in enumerate(kelas_kecepatan):
                # Ambil data persentase kejadian untuk kelas kecepatan tertentu, bulatkan 2 desimal
                values = df_ws[kelas].astype(float).round(2).tolist()
                
                ax.bar(
                    angles, values, 
                    width=(2*np.pi/N_arah)*0.8, 
                    bottom=bottom_bars, 
                    color=colors[idx % len(colors)], 
                    label=kelas, 
                    alpha=0.8
                )
                bottom_bars += np.array(values)
                
            ax.legend(title="Kecepatan Angin", loc="lower left", bbox_to_anchor=(1.1, 0.1))
            plt.tight_layout()
            st.pyplot(fig)
            
except FileNotFoundError:
    st.error(f"Berkas tidak ditemukan pada direktori penyimpanan: {current_cfg['file']}. Pastikan nama file di folder data sudah sesuai.")
except Exception as e:
    st.error(f"Gagal memproses data atau membuat visualisasi grafik: {e}")
