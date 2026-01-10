import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# 1. KONFIGURASI HALAMAN & TEMA (NAVY BLUE & SLATE GRAY)
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
    h1, h2, h3 { color: #1B4F72; font-family: 'Helvetica Neue', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 2. KONEKSI SUPABASE
@st.cache_resource
def init_connection():
    try:
        # Menggunakan URL dan Key dari project vejhntwveszqdjptgiua
        url = "https://vejhntwveszqdjptgiua.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamhudHd2ZXN6cWRqcHRnaXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNTA4NTUsImV4cCI6MjA4MTcyNjg1NX0.LiaMAVOLXmF2RU-qnNI2jzLypuKhcnb9LgMFC_uf-9E"
        return create_client(url, key)
    except Exception:
        return None

supabase = init_connection()

# 3. FUNGSI AMBIL DATA (SESUAI SKEMA SCREENSHOT 405)
@st.cache_data(ttl=60)
def fetch_real_data():
    if supabase is None: return pd.DataFrame()
    try:
        # Menarik data dari tabel amdk_sales
        response = supabase.table("amdk_sales").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            # KONVERSI TIPE DATA SESUAI SKEMA RIIL ANDA
            # Memastikan kolom numerik terbaca sebagai angka untuk perhitungan SUM
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
            df['total_sales_rp'] = pd.to_numeric(df['total_sales_rp'], errors='coerce')
            
            # Jika kolom tanggal belum tersedia, gunakan placeholder waktu sekarang
            # agar visualisasi tren tidak error
            df['transaction_date'] = datetime.now()
            
            return df.dropna(subset=['region', 'total_sales_rp'])
    except Exception as e:
        st.error(f"Gagal memproses data: {e}")
    return pd.DataFrame()

df_riil = fetch_real_data()

# 4. DASHBOARD UTAMA
st.title("📊 Dashboard Analitik Penjualan AMDK")
st.caption(f"Status: Live (Supabase Cloud) | Update: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.markdown("---")

if not df_riil.empty:
    # A. KPI METRICS (Layout Baris Atas)
    total_omzet = df_riil['total_sales_rp'].sum()
    total_unit = df_riil['quantity'].sum()
    # Menghitung Estimasi Laba (Prinsip Hifz al-Mal)
    estimasi_profit = total_omzet * 0.20

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Omzet Riil", f"Rp {total_omzet:,.0f}")
    with m2:
        st.metric("Total Unit Terjual", f"{total_unit:,} Pcs")
    with m3:
        st.metric("Estimasi Profit (20%)", f"Rp {estimasi_profit:,.0f}")

    st.markdown("---")

    # B. ANALISIS GRAFIK (Layout Dua Kolom)
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📍 Distribusi per Wilayah")
        # Menampilkan wilayah riil: jawa_timur, bali, dki_jakarta, banten, dsb.
        fig_pie = px.pie(df_riil, values='total_sales_rp', names='region', hole=0.5,
                         color_discrete_sequence=px.colors.qualitative.Prism)
        fig_pie.update_layout(margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("📦 Performa Produk (Berdasarkan Omzet)")
        # Menampilkan produk riil: prima, bisto, cheers, sega, dsb.
        df_prod = df_riil.groupby('product_name')['total_sales_rp'].sum().reset_index()
        fig_bar = px.bar(df_prod, x='total_sales_rp', y='product_name', orientation='h',
                         color_discrete_sequence=['#1B4F72'])
        fig_bar.update_layout(xaxis_title="Total Nilai (Rp)", yaxis_title="")
        st.plotly_chart(fig_bar, use_container_width=True)

    # C. TABEL DATA MENTAH
    with st.expander("🔍 Lihat Detail Data Supabase"):
        st.dataframe(df_riil[['product_name', 'category', 'region', 'quantity', 'total_sales_rp']], 
                     use_container_width=True)

else:
    # Tampilan jika data masih gagal terbaca (Pesan pada Screenshot 407)
    st.error("⚠️ Data tidak terbaca dari Supabase.")
    st.info("💡 Pastikan tabel 'amdk_sales' sudah berisi data dengan kolom: product_name, region, quantity, dan total_sales_rp.")
    if st.button("Segarkan Koneksi"):
        st.cache_data.clear()
        st.rerun()

st.caption("Dikembangkan untuk Monitoring Keuangan Real-time berbasis PostgreSQL.")
