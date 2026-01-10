import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime
from sklearn.linear_model import LinearRegression

# 1. KONFIGURASI HALAMAN & TEMA VISUAL
st.set_page_config(page_title="AMDK Sales Analytics Pro", page_icon="📊", layout="wide")

# Custom CSS untuk warna Biru Navy & Abu-abu serta styling Card
st.markdown("""
    <style>
    .main { background-color: #F4F6F7; }
    .stMetric { 
        background-color: #FFFFFF; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 5px solid #1B4F72; /* Biru Navy */
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
    }
    h1, h2, h3 { color: #1B4F72; font-family: 'Helvetica Neue', sans-serif; }
    .sidebar .sidebar-content { background-color: #EBEDEF; }
    </style>
    """, unsafe_allow_html=True)

# 2. KONEKSI KE SUPABASE
@st.cache_resource
def init_connection():
    try:
        # Kredensial sesuai dengan project Anda
        url = "https://vejhntwveszqdjptgiua.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamhudHd2ZXN6cWRqcHRnaXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNTA4NTUsImV4cCI6MjA4MTcyNjg1NX0.LiaMAVOLXmF2RU-qnNI2jzLypuKhcnb9LgMFC_uf-9E"
        return create_client(url, key)
    except Exception:
        return None

supabase = init_connection()

# 3. FUNGSI PENGAMBILAN DATA (DATA FETCHING)
@st.cache_data(ttl=600)
def fetch_data():
    if supabase is None:
        return pd.DataFrame()
    try:
        # Mengambil data dari tabel amdk_sales sesuai skema SQL Anda
        response = supabase.table("amdk_sales").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            # Preprocessing data agar siap diolah
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df['total_sales_rp'] = pd.to_numeric(df['total_sales_rp'], errors='coerce')
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            # Membersihkan baris yang memiliki nilai krusial kosong
            return df.dropna(subset=['transaction_date', 'total_sales_rp', 'region'])
    except Exception as e:
        st.error(f"Gagal menarik data: {e}")
    return pd.DataFrame()

# Eksekusi pengambilan data
df_raw = fetch_data()

# 4. LOGIKA DATA RIIL VS DATA DEFAULT
# Menggunakan data riil jika ada, atau data placeholder tanpa nama daerah Ciomas/Bogor
if not df_raw.empty:
    chart_data = df_raw.copy()
    mode_status = "Live (Data Supabase)"
else:
    # Data Placeholder (Daerah A, B, C) hanya ditampilkan jika database kosong
    st.warning("⚠️ Data riil di Supabase belum terdeteksi. Menampilkan data contoh (Wilayah A/B/C).")
    chart_data = pd.DataFrame({
        'transaction_date': pd.to_datetime(['2025-10-01', '2025-11-01', '2025-12-01', '2026-01-01']),
        'total_sales_rp': [1200000, 1500000, 1300000, 1800000],
        'quantity': [120, 150, 130, 180],
        'region': ['Jawa Timur', 'Sumatera Utara', 'Banten', 'Bali', 'DKI Jakarta', 'Jawa Barat', 'Jawa Tengah', 'Sumatera Selatan', 'Sulawesi Selatan', 'Kalimantan Timur'],
        'payment_method': ['Transfer', 'Tunai', 'Transfer', 'Transfer']
    })
    mode_status = "Simulation (DB Empty)"

# 5. SIDEBAR & FILTER
st.sidebar.title("⚙️ Panel Kontrol")
st.sidebar.markdown(f"**Status:** {mode_status}")

# Fitur Filter Wilayah berdasarkan data yang tersedia
list_region = chart_data['region'].unique().tolist()
selected_region = st.sidebar.multiselect("Pilih Wilayah", list_region, default=list_region)

# Filter Data berdasarkan input sidebar
filtered_df = chart_data[chart_data['region'].isin(selected_region)]

if st.sidebar.button('🔄 Segarkan Data'):
    st.cache_data.clear()
    st.rerun()

# 6. HEADER & KPI METRICS
st.title("🥤 Dashboard Analitik Penjualan AMDK")
st.caption(f"Sinkronisasi Data Terakhir: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.markdown("---")

# Agregasi data bulanan untuk metrik dan grafik
df_monthly = filtered_df.set_index('transaction_date').resample('ME').sum(numeric_only=True).reset_index()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Omzet", f"Rp {filtered_df['total_sales_rp'].sum():,.0f}")
with col2:
    st.metric("Unit Terjual", f"{filtered_df['quantity'].sum():,} Pcs")
with col3:
    # Perhitungan Estimasi Laba (Prinsip Hifz al-Mal)
    profit = filtered_df['total_sales_rp'].sum() * 0.20
    st.metric("Estimasi Profit (20%)", f"Rp {profit:,.0f}")
with col4:
    # Fitur Peramalan (Forecasting)
    if len(df_monthly) >= 2:
        df_monthly['date_ordinal'] = df_monthly['transaction_date'].map(datetime.toordinal)
        model = LinearRegression().fit(df_monthly[['date_ordinal']], df_monthly['total_sales_rp'])
        next_date = df_monthly['transaction_date'].max() + pd.DateOffset(months=1)
        prediction = model.predict([[next_date.toordinal()]])[0]
        st.metric("Proyeksi Bulan Depan", f"Rp {max(0, prediction):,.0f}")
    else:
        st.metric("Proyeksi", "Data Minim")

# 7. VISUALISASI UTAMA (TREN & DISTRIBUSI)
st.markdown("### 📈 Analisis Performa Penjualan")
c_left, c_right = st.columns([2, 1])

with c_left:
    st.subheader("Tren Bulanan & Garis Pertumbuhan")
    fig_bar = go.Figure()
    # Bar Chart (Navy Blue)
    fig_bar.add_trace(go.Bar(
        x=df_monthly['transaction_date'].dt.strftime('%b %Y'),
        y=df_monthly['total_sales_rp'],
        name="Penjualan Riil",
        marker_color='#1B4F72'
    ))
    # Garis Tren/Forecasting (Gray)
    if len(df_monthly) >= 2:
        df_monthly['trend'] = model.predict(df_monthly[['date_ordinal']])
        fig_bar.add_trace(go.Scatter(
            x=df_monthly['transaction_date'].dt.strftime('%b %Y'),
            y=df_monthly['trend'],
            name="Tren Regresi",
            line=dict(color='#BDC3C7', width=3, dash='dash')
        ))
    fig_bar.update_layout(height=400, template="plotly_white", margin=dict(t=10, b=10))
    st.plotly_chart(fig_bar, use_container_width=True)

with c_right:
    st.subheader("Distribusi per Wilayah")
    fig_pie = px.pie(filtered_df, values='total_sales_rp', names='region', hole=0.5,
                     color_discrete_sequence=['#1B4F72', '#2E86C1', '#5D6D7E', '#7F8C8D', '#D5DBDB'])
    fig_pie.update_layout(height=400, margin=dict(t=10, b=10))
    st.plotly_chart(fig_pie, use_container_width=True)

# 8. FITUR PENDUKUNG (VOLUME & LOG TRANSAKSI)
st.markdown("---")
b_left, b_right = st.columns(2)

with b_left:
    st.subheader("Metode Pembayaran (Cash vs Transfer)")
    fig_pay = px.bar(filtered_df.groupby('payment_method')['total_sales_rp'].sum().reset_index(),
                     x='total_sales_rp', y='payment_method', orientation='h',
                     color_discrete_sequence=['#2E86C1'])
    fig_pay.update_layout(xaxis_title="Total Nilai (Rp)", yaxis_title="", height=300)
    st.plotly_chart(fig_pay, use_container_width=True)

with b_right:
    st.subheader("📋 Ringkasan Transaksi Terakhir")
    # Menampilkan 10 data terbaru untuk transparansi (Akuntabilitas)
    st.dataframe(filtered_df[['transaction_date', 'region', 'quantity', 'total_sales_rp']]
                 .sort_values('transaction_date', ascending=False).head(10), 
                 use_container_width=True)

# Footer
st.caption("Dikembangkan untuk mendukung monitoring keuangan Home Industry berbasis Cloud.")
