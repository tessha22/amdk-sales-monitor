import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from supabase import create_client, Client
from datetime import datetime
from sklearn.linear_model import LinearRegression

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="AMDK Sales Analytics", page_icon="🥤", layout="wide")

# 2. KONEKSI SUPABASE
@st.cache_resource
def init_connection():
    try:
        url = "https://vejhntwveszqdjptgiua.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamhudHd2ZXN6cWRqcHRnaXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNTA4NTUsImV4cCI6MjA4MTcyNjg1NX0.LiaMAVOLXmF2RU-qnNI2jzLypuKhcnb9LgMFC_uf-9E"
        return create_client(url, key)
    except Exception as e:
        return None

supabase = init_connection()

# 3. AMBIL DATA
def fetch_data():
    try:
        response = supabase.table("amdk_sales").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df['total_sales_rp'] = pd.to_numeric(df['total_sales_rp'], errors='coerce')
            return df.dropna(subset=['transaction_date', 'total_sales_rp'])
    except:
        pass
    return pd.DataFrame()

df_raw = fetch_data()

# 4. TAMPILAN DASHBOARD
st.title("🥤 Dashboard Penjualan AMDK")

# PROTEKSI: JIKA DATA KOSONG, GUNAKAN DATA SIMULASI UNTUK TAMPILAN
if df_raw.empty:
    st.warning("⚠️ Database Supabase Kosong. Menampilkan Data Simulasi...")
    chart_data = pd.DataFrame({
        'transaction_date': pd.to_datetime(['2025-10-01', '2025-11-01', '2025-12-01', '2026-01-01']),
        'total_sales_rp': [1200000, 1500000, 1300000, 1800000]
    })
else:
    chart_data = df_raw.copy()

# 5. FORECASTING LOGIC
df_monthly = chart_data.set_index('transaction_date').resample('ME')['total_sales_rp'].sum().reset_index()

if len(df_monthly) >= 2:
    # Model Linear Regression
    df_monthly['date_ordinal'] = df_monthly['transaction_date'].map(datetime.toordinal)
    model = LinearRegression().fit(df_monthly[['date_ordinal']], df_monthly['total_sales_rp'])
    df_monthly['trend'] = model.predict(df_monthly[['date_ordinal']])
    
    # Prediksi Bulan Depan
    next_date = df_monthly['transaction_date'].max() + pd.DateOffset(months=1)
    prediction = model.predict([[next_date.toordinal()]])[0]

    # Visualisasi
    col1, col2 = st.columns([3, 1])
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_monthly['transaction_date'].dt.strftime('%b %Y'), y=df_monthly['total_sales_rp'], name="Riil"))
        fig.add_trace(go.Scatter(x=df_monthly['transaction_date'].dt.strftime('%b %Y'), y=df_monthly['trend'], name="Tren", line=dict(color='red', dash='dash')))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.metric("Proyeksi Bulan Depan", f"Rp {prediction:,.0f}")
        st.info("Berdasarkan tren pertumbuhan linear.")

st.caption(f"Sinkronisasi Terakhir: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
