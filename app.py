import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime
from sklearn.linear_model import LinearRegression

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="AMDK Sales Analytics", page_icon="📊", layout="wide")

# 2. KONEKSI SUPABASE
@st.cache_resource
def init_connection():
    try:
        url = "https://vejhntwveszqdjptgiua.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamhudHd2ZXN6cWRqcHRnaXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNTA4NTUsImV4cCI6MjA4MTcyNjg1NX0.LiaMAVOLXmF2RU-qnNI2jzLypuKhcnb9LgMFC_uf-9E"
        return create_client(url, key)
    except Exception:
        return None

supabase = init_connection()

# 3. AMBIL DATA RIIL
def fetch_data():
    try:
        response = supabase.table("amdk_sales").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df['total_sales_rp'] = pd.to_numeric(df['total_sales_rp'], errors='coerce')
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            # Filter hanya data yang memiliki nilai (menghilangkan data kosong)
            return df.dropna(subset=['transaction_date', 'total_sales_rp', 'region'])
    except Exception:
        pass
    return pd.DataFrame()

df_riil = fetch_data()

# 4. LOGIKA TAMPILAN (Menghilangkan Simulasi Ciomas/Bogor)
if not df_riil.empty:
    chart_data = df_riil
    mode_status = "Live"
else:
    # Jika database kosong, tampilkan peringatan alih-alih data simulasi Ciomas/Bogor
    st.error("⚠️ Data di Supabase tidak ditemukan. Silakan isi tabel 'amdk_sales' agar nama daerah Ciomas/Bogor hilang.")
    st.stop() 

# 5. VISUALISASI DATA RIIL
st.title("🥤 Dashboard Penjualan AMDK (Data Riil)")

# Grafik Distribusi Wilayah (Otomatis menyesuaikan data di Supabase)
st.subheader("Distribusi Penjualan per Wilayah")
fig_pie = px.pie(chart_data, values='total_sales_rp', names='region', hole=0.5,
                 color_discrete_sequence=px.colors.qualitative.Prism)
st.plotly_chart(fig_pie, use_container_width=True)

# Tabel Data untuk Cross-check
with st.expander("Lihat Data Wilayah di Supabase"):
    st.write(chart_data[['transaction_date', 'region', 'total_sales_rp']])
