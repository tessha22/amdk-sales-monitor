import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
import os
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="AMDK Analytics & Forecasting", page_icon="📈", layout="wide")

# 2. KONEKSI SUPABASE
@st.cache_resource
def init_connection():
    try:
        # PERBAIKAN DI SINI: 
        # Jika Anda ingin memasukkan kunci langsung di kode (Hardcoded), jangan gunakan os.environ.get
        url = "https://vejhntwveszqdjptgiua.supabase.co" # Pastikan format URL benar (tambahkan .supabase.co)
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamhudHd2ZXN6cWRqcHRnaXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNTA4NTUsImV4cCI6MjA4MTcyNjg1NX0.LiaMAVOLXmF2RU-qnNI2jzLypuKhcnb9LgMFC_uf-9E"
        
        if not url or not key:
            st.error("Kredensial Supabase tidak ditemukan!")
            st.stop()
        return create_client(url, key)
    except Exception as e:
        st.error(f"Gagal koneksi: {e}")
        return None

supabase = init_connection()

# 3. AMBIL DATA
@st.cache_data(ttl=600)
def fetch_data():
    try:
        # Mengambil data dari tabel amdk_sales
        response = supabase.table("amdk_sales").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if df.empty: 
            return df
        
        # Preprocessing Tanggal & Uang
        df['transaksi_date'] = pd.to_datetime(df['transaksi_date'])
        df['total_sales'] = pd.to_numeric(df['total_sales'], errors='coerce')
        
        # Kolom untuk ML Risiko
        for col in ['jumlah_tanggungan', 'plafon_kredit', 'status_lancar']:
            if col in df.columns: 
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df.dropna(subset=['total_sales', 'transaksi_date'])
    except Exception as e:
        st.error(f"Gagal ambil data: {e}")
        return pd.DataFrame()

df_raw = fetch_data()

# 4. SIDEBAR: RISIKO (DECISION TREE)
st.sidebar.header("🤖 Simulasi Risiko Nasabah")
if not df_raw.empty and 'status_lancar' in df_raw.columns:
    try:
        df_ml = df_raw.dropna(subset=['status_lancar', 'jumlah_tanggungan', 'plafon_kredit'])
        X_risk = df_ml[['total_sales', 'jumlah_tanggungan', 'plafon_kredit']]
        y_risk = df_ml['status_lancar']
        model_risk = DecisionTreeClassifier(random_state=42).fit(X_risk, y_risk)

        with st.sidebar.form("risk_form"):
            in_pendapatan = st.number_input("Pendapatan", min_value=0, value=5000000)
            in_tanggungan = st.number_input("Tanggungan", min_value=0, value=2)
            in_plafon = st.number_input("Plafon", min_value=0, value=1000000)
            if st.form_submit_button("Cek Risiko"):
                res = model_risk.predict([[in_pendapatan, in_tanggungan, in_plafon]])
                if res[0] == 1: 
                    st.sidebar.success("✅ Prediksi: LANCAR")
                else: 
                    st.sidebar.error("⚠️ Prediksi: MACET")
    except: 
        st.sidebar.warning("Data risiko belum optimal.")

# ---------------------------------------------------------
# 5. DASHBOARD UTAMA & FORECASTING (LINEAR REGRESSION)
# ---------------------------------------------------------
st.title("🥤 AMDK Sales Forecasting Dashboard")
st.markdown("---")

if not df_raw.empty:
    # A. Persiapan Data Bulanan untuk Regresi
    df_trend = df_raw.copy().set_index('transaksi_date')
    df_monthly = df_trend.resample('ME')['total_sales'].sum().reset_index()
    
    # Konversi Tanggal ke Ordinal (Angka) untuk Scikit-Learn
    df_monthly['date_ordinal'] = df_monthly['transaksi_date'].map(datetime.toordinal)
    
    X_time = df_monthly[['date_ordinal']].values
    y_sales = df_monthly['total_sales'].values
    
    # B. Modelling Peramalan
    model_lr = LinearRegression()
    model_lr.fit(X_time, y_sales)
    
    # Prediksi untuk garis tren saat ini
    df_monthly['trend_line'] = model_lr.predict(X_time)
    
    # C. Prediksi Masa Depan (Bulan Depan)
    last_date = df_monthly['transaksi_date'].max()
    next_month_date = (last_date + pd.DateOffset(months=1))
    next_month_ordinal = np.array([[next_month_date.toordinal()]])
    projection_next_month = model_lr.predict(next_month_ordinal)[0]

    # D. Tampilan Metric
    col_kpi1, col_kpi2, col_forecast = st.columns([1, 1, 2])
    with col_kpi1:
        st.metric("Total Penjualan", f"Rp {df_raw['total_sales'].sum():,.0f}")
    with col_kpi2:
        st.metric("Jumlah Transaksi", f"{len(df_raw):,}")
    with col_forecast:
        st.metric(
            label="🎯 Proyeksi Penjualan Bulan Depan", 
            value=f"Rp {projection_next_month:,.0f}",
            delta=f"{(projection_next_month - y_sales[-1]):,.0f} dari bulan terakhir",
            delta_color="normal"
        )

    st.markdown("---")

    # E. Visualisasi Bar Chart + Trendline
    st.subheader("📊 Tren Penjualan & Garis Regresi")
    df_monthly['Bulan'] = df_monthly['transaksi_date'].dt.strftime('%B %Y')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_monthly['Bulan'], y=df_monthly['total_sales'],
        name="Penjualan Riil", marker_color='#3366CC'
    ))
    fig.add_trace(go.Scatter(
        x=df_monthly['Bulan'], y=df_monthly['trend_line'],
        name="Garis Tren (Linear Regression)",
        line=dict(color='red', width=3, dash='dash')
    ))

    fig.update_layout(
        xaxis_tickangle=-45,
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Lihat Data Peramalan"):
        st.write(df_monthly[['Bulan', 'total_sales', 'trend_line']])
else:
    st.warning("Data tidak tersedia untuk melakukan peramalan.")

st.caption(f"Update: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
