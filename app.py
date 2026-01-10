import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# 1. KONFIGURASI HALAMAN & TEMA (NAVY & GRAY)
st.set_page_config(page_title="AMDK Sales Analytics Pro", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F4F6F7; }
    .stMetric { 
        background-color: #FFFFFF; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 5px solid #1B4F72; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
    }
    h1, h2, h3 { color: #1B4F72; }
    </style>
    """, unsafe_allow_html=True)

# 2. KONEKSI SUPABASE
@st.cache_resource
def init_connection():
    try:
        # Gunakan URL dan Key Anda
        url = "https://vejhntwveszqdjptgiua.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamhudHd2ZXN6cWRqcHRnaXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNTA4NTUsImV4cCI6MjA4MTcyNjg1NX0.LiaMAVOLXmF2RU-qnNI2jzLypuKhcnb9LgMFC_uf-9E"
        return create_client(url, key)
    except Exception:
        return None

supabase = init_connection()

# 3. FUNGSI AMBIL DATA (Sesuai Screenshot 405)
def fetch_real_data():
    if supabase is None: return pd.DataFrame()
    try:
        # Menarik data dari tabel amdk_sales
        response = supabase.table("amdk_sales").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            # PENYESUAIAN NAMA KOLOM SESUAI SCREENSHOT 405
            # Mengonversi tipe data agar bisa dikalkulasi
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
            df['total_sales_rp'] = pd.to_numeric(df['total_sales_rp'], errors='coerce')
            
            # Catatan: Jika kolom tanggal belum ada di screenshot 405, 
            # kita gunakan tanggal hari ini sebagai placeholder agar tidak error
            df['date_placeholder'] = datetime.now()
            
            return df
    except Exception as e:
        st.error(f"Error: {e}")
    return pd.DataFrame()

df_riil = fetch_real_data()

# 4. DASHBOARD UTAMA
st.title("📊 Dashboard Analitik Penjualan AMDK")

if not df_riil.empty:
    # KPI Metrics
    total_omzet = df_riil['total_sales_rp'].sum()
    total_unit = df_riil['quantity'].sum()
    avg_price = df_riil['unit_price'].mean()

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Omzet Riil", f"Rp {total_omzet:,.0f}")
    with m2:
        st.metric("Total Unit Terjual", f"{total_unit:,} Pcs")
    with m3:
        st.metric("Rata-rata Harga Satuan", f"Rp {avg_price:,.0f}")

    st.markdown("---")

    # Layout Grafik
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Distribusi Penjualan per Wilayah")
        # Menggunakan kolom 'region' dari data riil Anda (jawa_timur, bali, dki_jakarta, dll)
        fig_pie = px.pie(df_riil, values='total_sales_rp', names='region', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("Performa Produk (Top 10)")
        # Menggunakan kolom 'product_name' (prima, bisto, cheers, dll)
        df_prod = df_riil.groupby('product_name')['total_sales_rp'].sum().reset_index()
        fig_bar = px.bar(df_prod, x='total_sales_rp', y='product_name', orientation='h',
                         color_discrete_sequence=['#1B4F72'])
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tabel Data Mentah
    with st.expander("🔍 Lihat Detail Data Supabase"):
        st.dataframe(df_riil[['product_name', 'category', 'region', 'quantity', 'total_sales_rp']], use_container_width=True)

else:
    st.error("Data tidak terbaca. Pastikan tabel 'amdk_sales' di Supabase sudah terisi dengan benar.")
    st.info("Saran: Cek kembali nama kolom di Supabase. Kode ini mencari kolom: 'product_name', 'region', 'quantity', dan 'total_sales_rp'.")

st.caption(f"Sinkronisasi Terakhir: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
