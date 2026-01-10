import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# 1. KONFIGURASI HALAMAN & TEMA VISUAL
st.set_page_config(page_title="AMDK Sales Analytics Pro", page_icon="📊", layout="wide")

# CSS untuk styling kartu metrik (Navy & White)
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
        url = "https://vejhntwveszqdjptgiua.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamhudHd2ZXN6cWRqcHRnaXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNTA4NTUsImV4cCI6MjA4MTcyNjg1NX0.LiaMAVOLXmF2RU-qnNI2jzLypuKhcnb9LgMFC_uf-9E"
        return create_client(url, key)
    except Exception:
        return None

supabase = init_connection()

# 3. FUNGSI AMBIL DATA RIIL (Mapping Kolom Screenshot 405)
@st.cache_data(ttl=60)
def fetch_real_data():
    if supabase is None: return pd.DataFrame()
    try:
        # Mengambil data dari tabel amdk_sales
        response = supabase.table("amdk_sales").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            # Pastikan tipe data numerik benar (Konversi dari database)
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
            df['total_sales_rp'] = pd.to_numeric(df['total_sales_rp'], errors='coerce')
            
            # Jika tabel tidak memiliki kolom tanggal, buat kolom buatan untuk keperluan visualisasi
            if 'transaction_date' not in df.columns:
                df['transaction_date'] = datetime.now()
            
            return df.dropna(subset=['region', 'total_sales_rp', 'product_name'])
    except Exception as e:
        st.error(f"Gagal memproses data: {e}")
    return pd.DataFrame()

df_riil = fetch_real_data()

# 4. DASHBOARD UTAMA
st.title("🥤 Dashboard Analitik Penjualan AMDK")
st.caption(f"Status: Live (Supabase) | Wilayah Penelitian: Lokasi Riil di Database")
st.markdown("---")

if not df_riil.empty:
    # --- BAGIAN KPI METRICS ---
    total_omzet = df_riil['total_sales_rp'].sum()
    total_unit = df_riil['quantity'].sum()
    # Link ke Riset: Estimasi Profit untuk Kesejahteraan Keluarga [cite: 125, 345]
    estimasi_profit = total_omzet * 0.20

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Omzet Riil", f"Rp {total_omzet:,.0f}")
    with m2:
        st.metric("Total Unit Terjual", f"{total_unit:,} Pcs")
    with m3:
        st.metric("Estimasi Profit (20%)", f"Rp {estimasi_profit:,.0f}")

    st.markdown("---")

    # --- BAGIAN GRAFIK ---
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📍 Distribusi Penjualan per Wilayah")
        # Grafik Lingkaran (Donut Chart) menggunakan kolom 'region' riil
        fig_pie = px.pie(
            df_riil, 
            values='total_sales_rp', 
            names='region', 
            hole=0.5,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_pie.update_layout(margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("📦 Performa Produk (Berdasarkan Omzet)")
        # Grafik Batang Horizontal menggunakan kolom 'product_name' riil
        df_prod = df_riil.groupby('product_name')['total_sales_rp'].sum().reset_index().sort_values('total_sales_rp')
        fig_bar = px.bar(
            df_prod, 
            x='total_sales_rp', 
            y='product_name', 
            orientation='h',
            color_discrete_sequence=['#1B4F72'] # Biru Navy
        )
        fig_bar.update_layout(xaxis_title="Total Nilai (Rp)", yaxis_title="", margin=dict(t=20, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- BAGIAN TABEL DATA ---
    with st.expander("🔍 Lihat Detail Data Transaksi (Amanah & Transparan)"):
        # Menampilkan data sesuai prinsip akuntabilitas dalam Akuntansi Syariah [cite: 204]
        st.dataframe(
            df_riil[['product_name', 'category', 'region', 'quantity', 'total_sales_rp']], 
            use_container_width=True
        )

else:
    # Tampilan jika data masih kosong
    st.error("⚠️ Grafik tidak dapat ditampilkan karena data tidak terbaca.")
    st.info("💡 Pastikan tabel 'amdk_sales' di Supabase sudah berisi data Jawa Timur, Bali, DKI Jakarta, dll.")
    
    if st.button("Segarkan Koneksi"):
        st.cache_data.clear()
        st.rerun()

st.caption("Monitoring Keuangan Real-time untuk Mendukung Kemandirian Ekonomi Home Industry.")
