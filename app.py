import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client

# 1. KONEKSI SUPABASE
url = "https://vejhntwveszqdjptgiua.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamhudHd2ZXN6cWRqcHRnaXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNTA4NTUsImV4cCI6MjA4MTcyNjg1NX0.LiaMAVOLXmF2RU-qnNI2jzLypuKhcnb9LgMFC_uf-9E"
supabase = create_client(url, key)

# 2. FUNGSI AMBIL DATA RIIL
def fetch_real_data():
    response = supabase.table("amdk_sales").select("*").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        # Konversi kolom numerik sesuai skema file Anda
        df['total_sales_rp'] = pd.to_numeric(df['total_sales_rp'], errors='coerce')
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        return df
    return pd.DataFrame()

df = fetch_real_data()

# 3. TAMPILAN DASHBOARD
st.title("📊 Dashboard Analitik Penjualan AMDK")

if not df.empty:
    # Mengambil daftar wilayah riil dari kolom 'region' (Jawa Timur, Bali, DKI Jakarta, dll)
    list_wilayah = df['region'].unique().tolist()
    
    # Sidebar Filter Otomatis sesuai data riil
    selected_wilayah = st.sidebar.multiselect("Pilih Wilayah Riil", list_wilayah, default=list_wilayah)
    df_filtered = df[df['region'].isin(selected_wilayah)]

    # Metrik Utama
    c1, c2 = st.columns(2)
    c1.metric("Total Omzet Riil", f"Rp {df_filtered['total_sales_rp'].sum():,.0f}")
    c2.metric("Total Unit Terjual", f"{df_filtered['quantity'].sum():,} Pcs")

    # Grafik Distribusi Wilayah Riil
    st.subheader("Distribusi Penjualan per Wilayah (Data Supabase)")
    fig_pie = px.pie(df_filtered, values='total_sales_rp', names='region', hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Safe)
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Detail Tabel
    st.write("Data Transaksi Riil:", df_filtered[['product_name', 'region', 'total_sales_rp']])
else:
    st.error("Data tidak terbaca. Pastikan tabel 'amdk_sales' di Supabase sudah terisi.")
