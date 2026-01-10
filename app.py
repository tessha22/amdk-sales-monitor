import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime
from sklearn.linear_model import LinearRegression

# 1. KONFIGURASI HALAMAN & THEME
st.set_page_config(page_title="AMDK Sales Analytics Pro", page_icon="🥤", layout="wide")

# Custom CSS untuk mempercantik tampilan card
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
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

# 4. LOGIKA DATA (RIIL VS SIMULASI)
if df_raw.empty:
    st.sidebar.warning("Menggunakan Data Simulasi")
    chart_data = pd.DataFrame({
        'transaction_date': pd.to_datetime(['2025-10-01', '2025-11-01', '2025-12-01', '2026-01-01']),
        'total_sales_rp': [1200000, 1500000, 1300000, 1800000],
        'quantity': [120, 150, 130, 185],
        'region': ['Bogor', 'Jakarta', 'Bogor', 'Ciomas']
    })
else:
    chart_data = df_raw.copy()

# 5. HEADER DASHBOARD
st.title("📊 AMDK Executive Sales Dashboard")
st.caption(f"Sinkronisasi Terakhir: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.markdown("---")

# 6. KPI METRICS (Layout Baris Pertama)
df_monthly = chart_data.set_index('transaction_date').resample('ME').sum(numeric_only=True).reset_index()

col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    st.metric("Total Penjualan", f"Rp {chart_data['total_sales_rp'].sum():,.0f}")
with col_b:
    st.metric("Total Produk Terjual", f"{chart_data['quantity'].sum():,} unit")
with col_c:
    avg_sales = chart_data['total_sales_rp'].mean()
    st.metric("Rata-rata Transaksi", f"Rp {avg_sales:,.0f}")
with col_d:
    # Peramalan (Linear Regression tetap dipertahankan)
    if len(df_monthly) >= 2:
        df_monthly['date_ordinal'] = df_monthly['transaction_date'].map(datetime.toordinal)
        model = LinearRegression().fit(df_monthly[['date_ordinal']], df_monthly['total_sales_rp'])
        next_date = df_monthly['transaction_date'].max() + pd.DateOffset(months=1)
        prediction = model.predict([[next_date.toordinal()]])[0]
        st.metric("Proyeksi Bulan Depan", f"Rp {prediction:,.0f}", delta="Prediksi Pertumbuhan")
    else:
        st.metric("Proyeksi", "Data Minim")

st.markdown("### 📈 Analisis Performa")

# 7. GRAFIK UTAMA (Layout Dua Kolom)
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Tren Penjualan & Garis Regresi")
    if len(df_monthly) >= 2:
        df_monthly['trend'] = model.predict(df_monthly[['date_ordinal']])
        fig_main = go.Figure()
        fig_main.add_trace(go.Bar(x=df_monthly['transaction_date'].dt.strftime('%b %Y'), 
                                 y=df_monthly['total_sales_rp'], name="Penjualan Riil", marker_color='#1f77b4'))
        fig_main.add_trace(go.Scatter(x=df_monthly['transaction_date'].dt.strftime('%b %Y'), 
                                     y=df_monthly['trend'], name="Garis Tren", line=dict(color='red', width=3, dash='dash')))
        fig_main.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20), hovermode="x unified")
        st.plotly_chart(fig_main, use_container_width=True)

with col_right:
    st.subheader("Distribusi Penjualan per Wilayah")
    fig_pie = px.pie(chart_data, values='total_sales_rp', names='region', hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_pie.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_pie, use_container_width=True)

# 8. GRAFIK TAMBAHAN (Layout Baris Bawah)
st.markdown("---")
col_bot1, col_bot2 = st.columns(2)

with col_bot1:
    st.subheader("Volume Produk Terjual per Bulan")
    fig_qty = px.line(df_monthly, x='transaction_date', y='quantity', markers=True,
                      labels={'quantity': 'Unit', 'transaction_date': 'Bulan'})
    fig_qty.update_traces(line_color='#2ca02c')
    st.plotly_chart(fig_qty, use_container_width=True)

with col_bot2:
    st.subheader("Detail Transaksi Terakhir")
    st.dataframe(chart_data.sort_values('transaction_date', ascending=False).head(10), use_container_width=True)

# Footer info
if df_raw.empty:
    st.info("💡 Tips: Masukkan data ke tabel 'amdk_sales' di Supabase untuk menggantikan data simulasi ini.")
