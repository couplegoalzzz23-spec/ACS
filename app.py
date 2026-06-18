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
# 2. FUNGSI EKSTRAKSI DATA SUPER AKURAT
# ==========================================
@st.cache_data(show_spinner=False)
def load_acs_generic_data(file_path):
    """
    Membaca file Excel ACS menggunakan algoritma "Kepadatan Kolom".
    Sistem akan mencari baris yang memiliki rentang kategori terbanyak,
    sehingga tidak mungkin tertukar dengan judul tabel atau baris kosong.
    """
    if not os.path.exists(file_path):
        return None, None
        
    try:
        xls = pd.ExcelFile(file_path)
        actual_sheets = xls.sheet_names
    except Exception:
        return None, None

    # --- TAHAP 1: MENGUNCI BARIS KATEGORI (HEADER) ---
    sample_sheet = next((s for s in actual_sheets if any(m.lower() in s.lower() for m in months)), actual_sheets[0])
    df_sample = pd.read_excel(file_path, sheet_name=sample_sheet, header=None)
    
    max_filled_cols = 0
    header_row_idx = -1
    category_map = {}

    # Scan 15 baris pertama untuk mencari baris dengan kolom data terbanyak (mulai dari kolom ke-1/indeks 1)
    for r in range(min(15, len(df_sample))):
        temp_map = {}
        filled_count = 0
        for c in range(1, len(df_sample.columns)):
            val = str(df_sample.iloc[r, c]).strip()
            # Hitung kolom jika isinya bukan kosong dan bukan 'nan'
            if val and val.lower() != 'nan':
                filled_count += 1
                temp_map[c] = val
        
        # Jika baris ini memiliki lebih banyak kolom terisi daripada baris sebelumnya, jadikan ini sebagai header
        if filled_count > max_filled_cols:
            max_filled_cols = filled_count
            header_row_idx = r
            category_map = temp_map

    # Jika gagal mendeteksi (hampir mustahil untuk file ACS), hentikan proses
    if not category_map:
        return None, None

    # Rapikan nama kategori agar siap dijadikan kolom pada tabel/grafik
    categories = list(category_map.values())

    # --- TAHAP 2: EKSTRAKSI NILAI SUMMARY (MEAN/RATA-RATA) ---
    data_kategori = {k: [] for k in categories}
    
    for month in months:
        matched_sheet = next((s for s in actual_sheets if month.lower() in s.lower()), None)
        
        if matched_sheet:
            try:
                df = pd.read_excel(file_path, sheet_name=matched_sheet, header=None)
                
                target_row_idx = -1
                
                # Scan dari bawah ke atas (20 baris terakhir) mencari kata "MEAN", "RATA", dll di 3 kolom pertama
                for r in range(len(df)-1, max(-1, len(df)-20), -1):
                    row_text = " ".join(str(x).upper() for x in df.iloc[r, 0:3].values)
                    if any(k in row_text for k in ['MEAN', 'RATA', 'AVERAGE', 'AVG']):
                        target_row_idx = r
                        break
                
                # Fallback: Jika tidak ada kata MEAN, cari baris paling bawah yang berisi angka
                if target_row_idx == -1:
                    first_col_idx = list(category_map.keys())[0]
                    for r in range(len(df)-1, max(-1, len(df)-20), -1):
                        val = df.iloc[r, first_col_idx]
                        if pd.notna(val) and isinstance(val, (int, float)):
                            target_row_idx = r
                            break
                
                # Ekstrak nilai berdasarkan indeks kolom (category_map) yang sudah dikunci
                if target_row_idx != -1:
                    for c_idx, kategori in category_map.items():
                        if c_idx < len(df.columns):
                            val = df.iloc[target_row_idx, c_idx]
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
# 3. FUNGSI RENDER ANTARMUKA (UI)
# ==========================================
def render_parameter_ui(file_name, title, y_label, variable_label):
    file_path = os.path.join("data", file_name)
    
    st.markdown(f"### {title}")
    
    with st.spinner('Memproses data klimatologi operasional...'):
        df, categories = load_acs_generic_data(file_path)
    
    if df is not None and not df.empty:
        # Grafik Garis Interaktif menggunakan Plotly
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
        
        # Tabel Historis
        st.markdown("#### Tabel Data Historis")
        st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
    else:
        st.error(f"⚠️ Gagal memproses data dari file: `{file_name}`")
        st.info("💡 Pastikan file Excel tersebut berada di dalam direktori `data/` pada repositori GitHub Anda dan bukan merupakan file dummy.")


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
