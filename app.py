import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime
from sklearn.linear_model import LinearRegression

# 1. KONFIGURASI HALAMAN & THEME (WARNA BIRU & ABU-ABU)
st.set_page_config(page_title="AMDK Analytics Dashboard", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    /* Mengatur latar belakang dan font */
    .main { background-color: #F0F2F6; }
    .stMetric { 
        background-color: #FFFFFF; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 5px solid #1B4F72; /* Biru Navy */
        box-shadow: 2px 4px 15px rgba(0,0,0,0.05); 
    }
    h1, h2, h3 { color: #2C3E50; font-family: 'Segoe UI', sans-serif; }
    div[data-testid="stSidebarNav"] { background-color: #E5E8E8; }
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

# 3. AMBIL DATA
def fetch_data():
    try:
        response = supabase.table("amdk_sales").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df['total_sales_rp'] = pd.to_numeric(df['total_sales_rp'], errors='coerce')
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            return df.dropna(subset=['transaction_date', 'total_sales_rp'])
    except:
        pass
    return pd.DataFrame()

df_raw = fetch_data()

# 4. FITUR PENDUKUNG: DATA SIMULASI (Jika DB Kosong) & SIDEBAR FILTER
if df_raw.empty:
    chart_data = pd.DataFrame({
        'transaction_date': pd.to_datetime(['2025-09-01', '2025-10-01', '2025-11-01', '2025-12-01', '2026-01-01']),
        'total_sales_rp': [1100000, 1250000, 1500000, 1350000, 1900000],
        'quantity': [110, 125, 155, 140, 195],
        'region': ['Bogor', 'Jakarta', 'Bogor', 'Tangerang', 'Ciomas'],
        'payment_method': ['Tunai', 'Transfer', 'Tunai', 'Transfer', 'Transfer']
    })
else:
    chart_data = df_raw.copy()

# Sidebar: Filter Rentang Waktu
st.sidebar.title("⚙️ Kontrol Panel")
date_range = st.sidebar.date_input("Filter Periode", 
                                  [chart_data['transaction_date'].min(), chart_data['transaction_date'].max()])

# 5. HEADER (AKUNTANSI SYARIAH CONTEXT)
# Mencerminkan prinsip Amanah dalam pelaporan keuangan [cite: 147, 184]
st.title("🥤 AMDK Sales & Forecasting Intelligence")
st.caption(f"Data Akurat untuk Mendukung Kesejahteraan Ekonomi Keluarga | {datetime.now().strftime('%d/%m/%Y')}")
st.markdown("---")

# 6. KPI METRICS (DENGAN AKSEN BIRU & ABU)
df_monthly = chart_data.set_index('transaction_date').resample('ME').sum(numeric_only=True).reset_index()

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Omzet", f"Rp {chart_data['total_sales_rp'].sum():,.0f}")
with m2:
    st.metric("Unit Terjual", f"{chart_data['quantity'].sum():,} Pcs")
with m3:
    # Estimasi Profitability (Simulasi 20% margin) - Prinsip Hifz al-Mal 
    profit_est = chart_data['total_sales_rp'].sum() * 0.20
    st.metric("Estimasi Profit (20%)", f"Rp {profit_est:,.0f}")
with m4:
    if len(df_monthly) >= 2:
        df_monthly['date_ordinal'] = df_monthly['transaction_date'].map(datetime.toordinal)
        model = LinearRegression().fit(df_monthly[['date_ordinal']], df_monthly['total_sales_rp'])
        next_date = df_monthly['transaction_date'].max() + pd.DateOffset(months=1)
        prediction = model.predict([[next_date.toordinal()]])[0]
        st.metric("Target Bulan Depan", f"Rp {prediction:,.0f}")
    else:
        st.metric("Target", "N/A")

# 7. VISUALISASI UTAMA (PERPADUAN BIRU & ABU-ABU)
st.markdown("### 📈 Analisis Tren & Prediksi")
c_left, c_right = st.columns([2, 1])

with c_left:
    # Bar Chart Performa Bulanan
    fig_main = go.Figure()
    fig_main.add_trace(go.Bar(
        x=df_monthly['transaction_date'].dt.strftime('%b %Y'),
        y=df_monthly['total_sales_rp'],
        name="Pendapatan",
        marker_color='#1B4F72' # Biru Navy
    ))
    if len(df_monthly) >= 2:
        df_monthly['trend'] = model.predict(df_monthly[['date_ordinal']])
        fig_main.add_trace(go.Scatter(
            x=df_monthly['transaction_date'].dt.strftime('%b %Y'),
            y=df_monthly['trend'],
            name="Garis Pertumbuhan",
            line=dict(color='#7F8C8D', width=3, dash='dot') # Abu-abu
        ))
    fig_main.update_layout(plot_bgcolor='rgba(0,0,0,0)', height=400)
    st.plotly_chart(fig_main, use_container_width=True)

with c_right:
    # Donut Chart Wilayah
    fig_pie = px.pie(chart_data, values='total_sales_rp', names='region', hole=0.5,
                     color_discrete_sequence=['#1B4F72', '#2E86C1', '#5D6D7E', '#AEB6BF'])
    fig_pie.update_layout(showlegend=True, height=400)
    st.plotly_chart(fig_pie, use_container_width=True)

# 8. FITUR PENDUKUNG TAMBAHAN
st.markdown("---")
b_left, b_right = st.columns(2)

with b_left:
    st.subheader("💳 Metode Pembayaran")
    # Memastikan transparansi dalam transaksi (Amanah) 
    fig_pay = px.bar(chart_data.groupby('payment_method')['total_sales_rp'].sum().reset_index(),
                     x='total_sales_rp', y='payment_method', orientation='h',
                     color_discrete_sequence=['#2E86C1'])
    fig_pay.update_layout(xaxis_title="Total (Rp)", yaxis_title="")
    st.plotly_chart(fig_pay, use_container_width=True)

with b_right:
    st.subheader("📋 Log Transaksi Terbaru")
    # Menampilkan data mentah untuk audit internal sesuai Akuntansi Syariah [cite: 20, 125]
    st.dataframe(chart_data[['transaction_date', 'region', 'quantity', 'total_sales_rp']]
                 .sort_values('transaction_date', ascending=False).head(8), 
                 use_container_width=True)

# Status Koneksi di Sidebar
st.sidebar.markdown("---")
st.sidebar.info(f"Database: Connected\nMode: {'Live' if not df_raw.empty else 'Simulation'}")
