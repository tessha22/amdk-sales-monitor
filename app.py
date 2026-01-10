import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
import os
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="AMDK Analytics & Forecasting", page_icon="📈", layout="wide")

# 2. KONEKSI SUPABASE (PERBAIKAN KREDENSIAL)
@st.cache_resource
def init_connection():
    try:
        # Gunakan URL lengkap (termasuk .supabase.co) dan API Key anon yang benar
        # Masukkan string langsung di sini untuk memperbaiki error "Kredensial tidak ditemukan"
        url = "https://vejhntwveszqdjptgiua.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamhudHd2ZXN6cWRqcHRnaXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNTA4NTUsImV4cCI6MjA4MTcyNjg1NX0.LiaMAVOLXmF2RU-qnNI2jzLypuKhcnb9LgMFC_uf-9E"
        
        if not url or not key:
            st.error("Kredensial Supabase tidak ditemukan!")
            st.stop()
        return create_client(url, key)
    except Exception as e:
        st.error(f"Gagal koneksi ke Supabase: {e}")
        return None

supabase = init_connection()

# 3. AMBIL DATA
@st.cache_data(ttl=600)
def fetch_data():
    if supabase is None:
        return pd.DataFrame()
    try:
        # Ambil data dari tabel amdk_sales
        response = supabase.table("amdk_sales").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if df.empty:
            return df
        
        # Preprocessing Data
        df['transaksi_date'] = pd.to_datetime(df['transaksi_date'])
        df['total_sales'] = pd.to_numeric(df['total_sales'], errors='coerce')
        
        # Konversi kolom numerik lainnya jika ada
        cols_to_fix = ['jumlah_tanggungan', 'plafon_kredit', 'status_lancar']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Hapus baris yang datanya rusak pada kolom kunci
        return df.dropna(subset=['total_sales', 'transaksi_date'])
    except Exception as e:
        st.error(f"Gagal mengambil data dari tabel: {e}")
        return pd.DataFrame()

df_raw = fetch_data()

# 4. SIDEBAR: RISIKO (DECISION TREE)
st.sidebar.header("🤖 Simulasi Risiko Nasabah")
if not df_raw.empty and 'status_lancar' in df_raw.columns:
    try:
        # Filter data hanya yang memiliki status_lancar (1 untuk Lancar, 0 untuk Macet)
        df_ml = df_raw.dropna(subset=['status_lancar', 'jumlah_tanggungan', 'plafon_kredit'])
        if not df_ml.empty:
            X_risk = df_ml[['total_sales', 'jumlah_tanggungan', 'plafon_kredit']]
            y_risk = df_ml['status_lancar']
            model_risk = DecisionTreeClassifier(random_state=42).fit(X_risk, y_risk)

            with st.sidebar.form("risk_form"):
                in_pendapatan = st.number_input("Pendapatan (Rp)", min_value=0, value=5000000)
                in_tanggungan = st.number_input("Jumlah Tanggungan", min_value=0, value=2)
                in_plafon = st.number_input("Plafon Kredit (Rp)", min_value=0, value=1000000)
                
                if st.form_submit_button("Cek Risiko"):
                    res = model_risk.predict([[in_pendapatan, in_tanggungan, in_plafon]])
                    prob = model_risk.predict_proba([[in_pendapatan, in_tanggungan, in_plafon]])
                    
                    st.sidebar.markdown("---")
                    if res[0] == 1:
                        st.sidebar.success("✅ Prediksi: LANCAR")
                    else:
                        st.sidebar.error("⚠️ Prediksi: MACET")
                    st.sidebar.write(f"Keyakinan: {prob[0][int(res[0])]:.2%}")
        else:
            st.sidebar.warning("Data historis risiko belum cukup.")
    except Exception as e:
        st.sidebar.error(f"Error Model Risiko: {e}")
else:
    st.sidebar.info("Sidebar akan aktif setelah data termuat.")

# 5. DASHBOARD UTAMA
st.title("🥤 AMDK Sales Forecasting Dashboard")
st.markdown("---")

if not df_raw.empty:
    # A. Persiapan Forecasting (Linear Regression)
    df_trend = df_raw.copy().sort_values('transaksi_date')
    df_monthly = df_trend.set_index('transaksi_date').resample('ME')['total_sales'].sum().reset_index()
    
    # Minimal butuh 2 titik data untuk forecasting
    if len(df_monthly) >= 2:
        df_monthly['date_ordinal'] = df_monthly['transaksi_date'].map(datetime.toordinal)
        X_time = df_monthly[['date_ordinal']].values
        y_sales = df_monthly['total_sales'].values
        
        model_lr = LinearRegression().fit(X_time, y_sales)
        df_monthly['trend_line'] = model_lr.predict(X_time)
        
        # Proyeksi Bulan Depan
        last_date = df_monthly['transaksi_date'].max()
        next_month_date = last_date + pd.DateOffset(months=1)
        projection = model_lr.predict([[next_month_date.toordinal()]])[0]

        # B. Tampilan Metric
        col1, col2, col3 = st.columns([1, 1, 2])
        col1.metric("Total Penjualan", f"Rp {df_raw['total_sales'].sum():,.0f}")
        col2.metric("Total Transaksi", f"{len(df_raw):,}")
        col3.metric("🎯 Proyeksi Bulan Depan", f"Rp {max(0, projection):,.0f}", 
                   delta=f"{(projection - y_sales[-1]):,.0f} vs bln terakhir")

        st.markdown("---")

        # C. Visualisasi Bar + Trendline
        st.subheader("📊 Analisis Tren & Garis Regresi")
        df_monthly['Bulan'] = df_monthly['transaksi_date'].dt.strftime('%b %Y')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_monthly['Bulan'], y=df_monthly['total_sales'], 
                             name="Penjualan Riil", marker_color='#3366CC'))
        fig.add_trace(go.Scatter(x=df_monthly['Bulan'], y=df_monthly['trend_line'], 
                                name="Garis Tren", line=dict(color='red', width=3, dash='dash')))

        fig.update_layout(xaxis_tickangle=-45, template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Data bulanan belum cukup untuk melakukan peramalan (minimal butuh 2 bulan data).")
else:
    st.warning("Menunggu data dari Supabase... Pastikan tabel 'amdk_sales' sudah terisi.")

st.caption(f"Update: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
