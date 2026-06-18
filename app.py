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
# 2. FUNGSI EKSTRAKSI DATA (TAHAN BANTING)
# ==========================================
@st.cache_data(show_spinner=False)
def load_acs_generic_data(file_path):
    """
    Fungsi ini 100% dinamis. Akan men-scan secara cerdas baris mana yang 
    merupakan header kategori dan baris mana yang merupakan nilai rata-rata.
    """
    if not os.path.exists(file_path):
        return None, None
        
    try:
        xls = pd.ExcelFile(file_path)
        actual_sheets = xls.sheet_names
    except Exception:
        return None, None

    # --- TAHAP 1: MENCARI HEADER / KATEGORI RENTANG ---
    # Ambil sheet bulan pertama yang valid untuk di-scan strukturnya
    sample_sheet = next((s for s in actual_sheets if any(m.lower() in s.lower() for m in months)), actual_sheets[0])
    df_sample = pd.read_excel(file_path, sheet_name=sample_sheet, header=None)
    
    best_row_idx = 0
    max_cols = 0
    # Scan 15 baris pertama untuk mencari baris yang memiliki label rentang terbanyak
    for r in range(min(15, len(df_sample))):
        cols_filled = df_sample.iloc[r, 1:].dropna().astype(str).str.strip()
        cols_filled = cols_filled[cols_filled != '']
        if len(cols_filled) > max_cols:
            max_cols = len(cols_filled)
            best_row_idx = r
            
    if max_cols > 0:
        categories = [str(val).strip() for val in df_sample.iloc[best_row_idx, 1:] if pd.notna(val) and str(val).strip() != '']
    else:
        categories = [f"Rentang {i}" for i in range(1, len(df_sample.columns))]

    # Pastikan tidak ada nama kategori yang duplikat
    unique_categories = []
    for c in categories:
        if c not in unique_categories:
            unique_categories.append(c)
        else:
            unique_categories.append(c + " (copy)")
    categories = unique_categories

    # --- TAHAP 2: EKSTRAKSI NILAI DARI SETIAP BULAN ---
    data_kategori = {k: [] for k in categories}
    
    for month in months:
        matched_sheet = next((s for s in actual_sheets if month.lower() in s.lower()), None)
        
        if matched_sheet:
            try:
                df = pd.read_excel(file_path, sheet_name=matched_sheet, header=None)
                
                # Cari baris rata-rata (Scan dari bawah ke atas)
                target_row = -1
                for idx in reversed(df.index):
                    val0 = str(df.iloc[idx, 0]).strip().upper()
                    if any(keyword in val0 for keyword in ['MEAN', 'RATA-RATA', 'RATA RATA', 'RATA2', 'AVERAGE']):
                        target_row = idx
                        break
                        
                # Fallback Cerdas: Jika kata 'Mean/Rata-rata' tidak ditemukan, 
                # ambil baris paling bawah yang mengandung angka valid di kolom kedua.
                if target_row == -1:
                    for idx in reversed(df.index):
                        val1 = df.iloc[idx, 1]
                        if pd.notna(val1) and isinstance(val1, (int, float)):
                            target_row = idx
                            break
                
                # Masukkan data ke array
                if target_row != -1:
                    for col_idx, kategori in enumerate(categories, start=1):
                        if col_idx < len(df.columns):
                            val = df.iloc[target_row, col_idx]
                            try:
                                val = float(val)
                                if pd.isna(val): val = 0.0
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
# 3. FUNGSI RENDER TAMPILAN
# ==========================================
def render_parameter_ui(file_name, title, y_label, variable_label):
    file_path = os.path.join("data", file_name)
    
    st.markdown(f"### {title}")
    
    with st.spinner('Mengekstrak data dari Excel...'):
        df, categories = load_acs_generic_data(file_path)
    
    if df is not None and not df.empty:
        # Grafik
        fig = px.line(df, x=df.index, y=df.columns, markers=True,
                      labels={'index': 'Bulan', 'value': y_label, 'variable': variable_label})
        fig.update_layout(
            hovermode="x unified", 
            plot_bgcolor='rgba(0,0,0,0)', 
            height=500,
            legend=dict(title=variable_label)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabel
        st.markdown("#### Tabel Data Historis")
        st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error(f"⚠️ Gagal memuat data dari file: `{file_name}`")
        st.info("💡 Pastikan file tersebut ada di folder `data/` pada repositori GitHub Anda.")


# ==========================================
# 4. NAVIGASI TAB
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
