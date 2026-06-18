import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Konfigurasi Halaman Web Dashboard
st.set_page_config(
    page_title="Dashboard ACS Terintegrasi", 
    layout="wide", 
    page_icon="🌤️"
)

st.title("📊 Dashboard Aerodrome Climatological Summary (ACS)")
st.subheader("Analisis Klimatologi Cuaca Operasional Pangkalan Udara Periode 2021-2025")
st.markdown("---")

# Daftar bulan standar untuk pencarian sheet
months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

# 2. ENGINE PEMBACA DATA TAHAN BANTING (Auto-Detect Header & Summary)
@st.cache_data
def load_acs_data(file_name):
    file_path = os.path.join("data", file_name)
    
    if not os.path.exists(file_path):
        return None
        
    try:
        xls = pd.ExcelFile(file_path)
    except Exception:
        return None

    all_data = {}
    master_categories = [] # Menyimpan urutan kategori asli

    for month in months:
        # Cari sheet yang namanya mirip dengan bulan berjalan (misal: "Jan", "Januari")
        sheet_name = next((s for s in xls.sheet_names if s.strip().lower().startswith(month[:3].lower())), None)
        if not sheet_name:
            continue
            
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        except Exception:
            continue
            
        # Bersihkan baris dan kolom yang 100% kosong
        df = df.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)
        if df.empty:
            continue
            
        # -- TAHAP A: Cari Baris Kategori (Header) --
        # Logikanya: Baris dengan jumlah sel terisi paling banyak biasanya adalah baris kategori/rentang nilai.
        row_counts = df.notna().sum(axis=1)
        header_idx = row_counts.idxmax()
        
        # -- TAHAP B: Cari Baris Rekapitulasi (MEAN/JUMLAH/TOTAL) --
        target_idx = -1
        keywords = ['mean', 'rata', 'jumlah', 'total', 'average']
        
        # Scan dari baris paling bawah ke atas (untuk menghindari footer text)
        for i in range(len(df)-1, -1, -1):
            # Gabungkan teks di 4 kolom pertama untuk mencari kata kunci
            row_text = ' '.join([str(x).lower() for x in df.iloc[i, :4] if pd.notna(x)])
            if any(kw in row_text for kw in keywords):
                target_idx = i
                break
                
        # Jika kata kunci tidak ditemukan, ambil baris paling bawah yang berisi angka
        if target_idx == -1:
            for i in range(len(df)-1, header_idx, -1):
                numeric_count = pd.to_numeric(df.iloc[i, 1:], errors='coerce').notna().sum()
                if numeric_count > 1: # Jika ada minimal 2 angka, anggap ini baris data terakhir
                    target_idx = i
                    break
                    
        # Jika struktur tidak logis, lewati bulan ini
        if target_idx == -1 or header_idx >= target_idx:
            continue
            
        # -- TAHAP C: Ekstraksi Data Sesuai Kolom --
        month_data = {}
        for col in range(1, len(df.columns)):
            cat = str(df.iloc[header_idx, col]).strip()
            
            # Abaikan kolom tanpa nama atau sisa kolom kosong
            if pd.isna(df.iloc[header_idx, col]) or cat.lower() in ['nan', 'unnamed']:
                continue
                
            val = df.iloc[target_idx, col]
            
            try:
                val_float = float(val)
                if pd.isna(val_float):
                    val_float = 0.0
            except (ValueError, TypeError):
                val_float = 0.0
                
            month_data[cat] = val_float
            
            # Simpan kategori baru ke daftar master agar urutannya terjaga
            if cat not in master_categories:
                master_categories.append(cat)
                
        all_data[month] = month_data

    # Jika file sama sekali tidak bisa dibaca, kembalikan None
    if not all_data:
        return None

    # -- TAHAP D: Susun Data Menjadi DataFrame Sempurna --
    final_rows = []
    for m in months:
        row_dict = {'Bulan': m}
        if m in all_data:
            for cat in master_categories:
                row_dict[cat] = all_data[m].get(cat, 0.0)
        else:
            for cat in master_categories:
                row_dict[cat] = 0.0
        final_rows.append(row_dict)
        
    df_final = pd.DataFrame(final_rows).set_index('Bulan')
    return df_final

# 3. FUNGSI PEMBUAT GRAFIK METEOGRAM
def plot_meteogram(df, y_label, var_label):
    fig = px.line(df, x=df.index, y=df.columns, markers=True,
                  labels={'index': 'Bulan', 'value': y_label, 'variable': var_label},
                  template="plotly_white")
    fig.update_layout(hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)', height=500,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig

# 4. SISTEM TAB NAVIGASI (Sesuai output yang diminta)
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
    st.markdown("### 1. Persentase Temperatur Bulanan (2021-2025)")
    df_temp = load_acs_data('rata_rata_persentase_temperature_2021_2025.xlsx')
    if df_temp is not None and not df_temp.empty:
        st.plotly_chart(plot_meteogram(df_temp, "Persentase (%)", "Suhu (°C)"), use_container_width=True)
        st.dataframe(df_temp.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error("⚠️ Gagal memuat data dari `rata_rata_persentase_temperature_2021_2025.xlsx`. Pastikan file ada di folder 'data'.")

# --- TAB 2: VISIBILITY ---
with tabs[1]:
    st.markdown("### 2. Persentase Visibility Bulanan (2021-2025)")
    df_vis = load_acs_data('rata_rata_persentase_visibility_2021_2025.xlsx')
    if df_vis is not None and not df_vis.empty:
        st.plotly_chart(plot_meteogram(df_vis, "Persentase (%)", "Jarak Pandang (m)"), use_container_width=True)
        st.dataframe(df_vis.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error("⚠️ Gagal memuat data dari `rata_rata_persentase_visibility_2021_2025.xlsx`.")

# --- TAB 3: CLOUD HEIGHT (HS) ---
with tabs[2]:
    st.markdown("### 3. Persentase Cloud Height Bulanan (2021-2025)")
    df_hs = load_acs_data('rata_rata_persentase_hs_2021_2025.xlsx')
    if df_hs is not None and not df_hs.empty:
        st.plotly_chart(plot_meteogram(df_hs, "Persentase (%)", "Tinggi Awan (ft)"), use_container_width=True)
        st.dataframe(df_hs.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error("⚠️ Gagal memuat data dari `rata_rata_persentase_hs_2021_2025.xlsx`.")

# --- TAB 4: WIND SPEED (WINDROSE / POLAR) ---
with tabs[3]:
    st.markdown("### 4. Persentase Wind Speed Bulanan (2021-2025)")
    df_ws = load_acs_data('rata_rata_persentase_ws_2021_2025.xlsx')
    if df_ws is not None and not df_ws.empty:
        # Transformasi bentuk tabel untuk visualisasi Polar Chart
        df_ws_long = df_ws.reset_index().melt(id_vars='Bulan', var_name='Kategori', value_name='Persentase')
        
        # Membuat Polar Bar Chart (Windrose Bulanan)
        fig_ws = px.bar_polar(df_ws_long, r="Persentase", theta="Bulan", color="Kategori",
                              template="plotly_white",
                              color_discrete_sequence=px.colors.sequential.Tealgrn)
        fig_ws.update_layout(height=600, polar=dict(radialaxis=dict(visible=True, showticklabels=True)))
        
        st.plotly_chart(fig_ws, use_container_width=True)
        st.dataframe(df_ws.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error("⚠️ Gagal memuat data dari `rata_rata_persentase_ws_2021_2025.xlsx`.")

# --- TAB 5: RELATIVE HUMIDITY (RH) ---
with tabs[4]:
    st.markdown("### 5. Kejadian Relative Humidity (RH) Bulanan (2021-2025)")
    df_rh = load_acs_data('rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx')
    if df_rh is not None and not df_rh.empty:
        st.plotly_chart(plot_meteogram(df_rh, "Jumlah Kejadian", "Rentang RH (%)"), use_container_width=True)
        st.dataframe(df_rh.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error("⚠️ Gagal memuat data dari `rata_rata_jumlah_kejadian_masuk_rh_2021_2025.xlsx`.")

# --- TAB 6: TEMP MAKS & MIN ---
with tabs[5]:
    st.markdown("### 6. Kejadian Temperatur Maks & Min Bulanan (2021-2025)")
    df_tmaxmin = load_acs_data('rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx')
    if df_tmaxmin is not None and not df_tmaxmin.empty:
        st.plotly_chart(plot_meteogram(df_tmaxmin, "Jumlah Kejadian", "Kategori Suhu (°C)"), use_container_width=True)
        st.dataframe(df_tmaxmin.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error("⚠️ Gagal memuat data dari `rata_rata_jumlah_kejadian_masuk_tmaxmin_2021_2025.xlsx`.")
