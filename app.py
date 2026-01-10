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
        # Gunakan URL dan Key Anda
        url = "https://vejhntwveszqdjptgiua.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamhudHd2ZXN6cWRqcHRnaXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNTA4NTUsImV4cCI6MjA4MTcyNjg1NX0.LiaMAVOLXmF2RU-qnNI2jzLypuKhcnb9LgMFC_uf-9E"
        return create_client(url, key)
    except Exception as e:
        st.error(f"Koneksi Gagal: {e}")
        return None

supabase = init_connection()

# 3. FUNGSI AMBIL DATA (Sesuai Skema Tabel Anda)
@st.cache_data(ttl=600)
def fetch_data():
    if supabase is None: return pd.DataFrame()
    try:
        # Mengambil data dari tabel amdk_sales
        response = supabase.table("amdk_sales").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if df.empty: return df
        
        # Mapping & Preprocessing sesuai skema database Anda
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['total_sales_rp'] = pd.to_numeric(df['total_sales_rp'], errors='coerce')
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        
        return df.dropna(subset=['total_sales_rp', 'transaction_date'])
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

df_raw = fetch_data()

# 4. DASHBOARD UTAMA
st.title("🥤 Dashboard Penjualan AMDK")
st.markdown("---")

if not df_raw.empty:
    # A. Perhitungan Forecasting (Linear Regression)
    # Agregasi data ke bulanan
    df_monthly = df_raw.set_index('transaction_date').resample('ME')['total_sales_rp'].sum().reset_index()
    
    if len(df_monthly) >= 2:
        # Menyiapkan data untuk regresi (Tanggal ke angka ordinal)
        df_monthly['date_ordinal'] = df_monthly['transaction_date'].map(datetime.toordinal)
        X = df_monthly[['date_ordinal']].values
        y = df_monthly['total_sales_rp'].values
        
        model = LinearRegression().fit(X, y)
        df_monthly['trend_line'] = model.predict(X)
        
        # Prediksi Bulan Depan
        last_date = df_monthly['transaction_date'].max()
        next_month = last_date + pd.DateOffset(months=1)
        next_val = model.predict([[next_month.toordinal()]])[0]

        # B. Tampilan Metric
        total_sales = df_raw['total_sales_rp'].sum()
        total_qty = df_raw['quantity'].sum()
        
        c1, c2, c3 = st.columns([1, 1, 2])
        c1.metric("Total Penjualan", f"Rp {total_sales:,.0f}")
        c2.metric("Total Produk Terjual", f"{total_qty:,} unit")
        c3.metric("🎯 Proyeksi Bulan Depan", f"Rp {max(0, next_val):,.0f}", 
                  delta=f"{(next_val - y[-1]):,.0f} dari tren terakhir")

        st.markdown("---")

        # C. Visualisasi: Bar Chart + Trendline
        st.subheader("📊 Analisis Tren Penjualan Bulanan")
        df_monthly['Periode'] = df_monthly['transaction_date'].dt.strftime('%b %Y')
        
        fig = go.Figure()
        # Bar Chart data riil
        fig.add_trace(go.Bar(x=df_monthly['Periode'], y=df_monthly['total_sales_rp'], 
                             name="Penjualan Riil", marker_color='#1f77b4'))
        # Line Chart untuk Tren (Forecasting)
        fig.add_trace(go.Scatter(x=df_monthly['Periode'], y=df_monthly['trend_line'], 
                                 name="Garis Tren (Regresi)", line=dict(color='red', width=3, dash='dash')))

        fig.update_layout(xaxis_tickangle=-45, template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # D. Breakdown Region
        st.subheader("📍 Penjualan per Wilayah")
        df_region = df_raw.groupby('region')['total_sales_rp'].sum().reset_index()
        fig_reg = go.Figure(data=[go.Pie(labels=df_region['region'], values=df_region['total_sales_rp'], hole=.3)])
        st.plotly_chart(fig_reg, use_container_width=True)

    else:
        st.info("Data bulanan belum cukup untuk melakukan peramalan (minimal 2 bulan).")
        st.dataframe(df_raw)
else:
    st.warning("Tabel 'amdk_sales' kosong. Silakan isi data di Supabase untuk melihat visualisasi.")

st.caption(f"Sinkronisasi Terakhir: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
