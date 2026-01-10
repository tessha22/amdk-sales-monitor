import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from supabase import create_client, Client
import os
from datetime import datetime
from sklearn.linear_model import LinearRegression

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="AMDK Sales Monitor", page_icon="🥤", layout="wide")

# 2. KONEKSI SUPABASE
@st.cache_resource
def init_connection():
    try:
        url = "https://vejhntwveszqdjptgiua.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamhudHd2ZXN6cWRqcHRnaXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNTA4NTUsImV4cCI6MjA4MTcyNjg1NX0.LiaMAVOLXmF2RU-qnNI2jzLypuKhcnb9LgMFC_uf-9E"
        return create_client(url, key)
    except Exception as e:
        st.error(f"Koneksi Gagal: {e}")
        return None

supabase = init_connection()

# 3. AMBIL DATA (Pembersihan Data Otomatis)
def fetch_data():
    if supabase is None: return pd.DataFrame()
    try:
        # Memanggil tabel amdk_sales
        response = supabase.table("amdk_sales").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if df.empty: 
            return pd.DataFrame()
        
        # Konversi tipe data agar bisa dihitung
        df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
        df['total_sales_rp'] = pd.to_numeric(df['total_sales_rp'], errors='coerce')
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        
        # Hapus data yang tidak memiliki tanggal atau nilai penjualan
        return df.dropna(subset=['transaction_date', 'total_sales_rp'])
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

# Tombol Refresh di Sidebar
if st.sidebar.button('🔄 Perbarui Data'):
    st.cache_data.clear()

df_raw = fetch_data()

# 4. TAMPILAN DASHBOARD
st.title("🥤 Dashboard Penjualan AMDK")

if df_raw.empty:
    st.warning("⚠️ Tabel 'amdk_sales' terdeteksi kosong atau format data salah.")
    st.info("💡 Pastikan Anda sudah mengisi data di Supabase dan kolom 'transaction_date' serta 'total_sales_rp' sudah terisi.")
    
    # Debug: Tampilkan data mentah jika ada tapi rusak
    if 'df_raw' in locals() and not df_raw.empty:
        st.write("Data mentah terdeteksi:", df_raw)
else:
    # A. KPI Metrics
    total_sales = df_raw['total_sales_rp'].sum()
    total_qty = df_raw['quantity'].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("Total Penjualan", f"Rp {total_sales:,.0f}")
    col2.metric("Total Produk Terjual", f"{total_qty:,} unit")

    # B. Forecasting (Regresi Linear)
    df_monthly = df_raw.set_index('transaction_date').resample('ME')['total_sales_rp'].sum().reset_index()
    
    if len(df_monthly) >= 2:
        df_monthly['date_ordinal'] = df_monthly['transaction_date'].map(datetime.toordinal)
        X = df_monthly[['date_ordinal']].values
        y = df_monthly['total_sales_rp'].values
        
        model = LinearRegression().fit(X, y)
        df_monthly['trend_line'] = model.predict(X)
        
        # Visualisasi
        st.subheader("📊 Analisis Tren Penjualan")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_monthly['transaction_date'].dt.strftime('%b %Y'), 
                             y=df_monthly['total_sales_rp'], name="Penjualan Riil"))
        fig.add_trace(go.Scatter(x=df_monthly['transaction_date'].dt.strftime('%b %Y'), 
                                 y=df_monthly['trend_line'], name="Garis Tren", line=dict(color='red', dash='dash')))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Informasi: Minimal dibutuhkan 2 bulan data berbeda untuk menampilkan garis peramalan.")

    # C. Tabel Data
    with st.expander("🔍 Lihat Detail Transaksi"):
        st.dataframe(df_raw.sort_values('transaction_date', ascending=False), use_container_width=True)

st.caption(f"Sinkronisasi Terakhir: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
