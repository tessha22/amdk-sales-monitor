import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import os
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="AMDK Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

# 2. KONEKSI SUPABASE (Secure via os.environ)
@st.cache_resource
def init_connection():
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            st.error("Environment variables SUPABASE_URL dan SUPABASE_KEY tidak ditemukan!")
            st.stop()
        return create_client(url, key)
    except Exception as e:
        st.error(f"Gagal menghubungkan ke Supabase: {e}")
        return None

supabase = init_connection()

# 3. FUNGSI AMBIL DATA
@st.cache_data(ttl=600)  # Cache data selama 10 menit
def fetch_data():
    try:
        # Mengambil data dari tabel amdk_sales
        response = supabase.table("amdk_sales").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if df.empty:
            return df

        # Preprocessing Data
        df['transaksi_date'] = pd.to_datetime(df['transaksi_date'])
        df['total_sales'] = pd.to_numeric(df['total_sales'])
        df['quantity'] = pd.to_numeric(df['quantity'])
        return df
    except Exception as e:
        st.error(f"Terjadi kesalahan saat mengambil data: {e}")
        return pd.DataFrame()

# Load Data
df_raw = fetch_data()

if df_raw.empty:
    st.warning("Data tidak ditemukan atau tabel kosong.")
    st.stop()

# 4. SIDEBAR - FILTER
st.sidebar.header("Filter Data")

# Filter Region
all_regions = df_raw['region'].unique().tolist()
selected_region = st.sidebar.multiselect("Pilih Region", options=all_regions, default=all_regions)

# Filter Rentang Total Sales
min_sales = float(df_raw['total_sales'].min())
max_sales = float(df_raw['total_sales'].max())
sales_range = st.sidebar.slider(
    "Rentang Total Sales",
    min_value=min_sales,
    max_value=max_sales,
    value=(min_sales, max_sales)
)

# Apply Filter
df_filtered = df_raw[
    (df_raw['region'].isin(selected_region)) & 
    (df_raw['total_sales'] >= sales_range[0]) & 
    (df_raw['total_sales'] <= sales_range[1])
]

# 5. HEADER & KPI SECTION
st.title("🥤 AMDK Sales Performance Dashboard")
st.markdown("---")

try:
    total_sales_val = df_filtered['total_sales'].sum()
    total_transactions = len(df_filtered)
    avg_transaction = df_filtered['total_sales'].mean() if total_transactions > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Penjualan", f"Rp {total_sales_val:,.0f}")
    with col2:
        st.metric("Total Transaksi", f"{total_transactions:,}")
    with col3:
        st.metric("Rata-rata Nilai", f"Rp {avg_transaction:,.0f}")
except Exception as e:
    st.error(f"Error dalam kalkulasi KPI: {e}")

st.markdown("---")

# 6. VISUALISASI
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Tren Penjualan Bulanan")
    try:
        # Resample data ke bulanan
        df_trend = df_filtered.copy()
        df_trend.set_index('transaksi_date', inplace=True)
        df_monthly = df_trend.resample('M')['total_sales'].sum().reset_index()
        df_monthly['transaksi_date'] = df_monthly['transaksi_date'].dt.strftime('%B %Y')

        fig_bar = px.bar(
            df_monthly, 
            x='transaksi_date', 
            y='total_sales',
            labels={'total_sales': 'Total Penjualan', 'transaksi_date': 'Bulan'},
            color_discrete_sequence=['#3366CC']
        )
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)
    except Exception as e:
        st.error(f"Gagal memuat grafik tren: {e}")

with col_right:
    st.subheader("Komposisi Penjualan per Region")
    try:
        fig_pie = px.pie(
            df_filtered, 
            values='total_sales', 
            names='region',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    except Exception as e:
        st.error(f"Gagal memuat grafik region: {e}")

# 7. DATA PREVIEW (Opsional)
with st.expander("Lihat Detail Data Terfilter"):
    st.dataframe(df_filtered.sort_values(by='transaksi_date', ascending=False), use_container_width=True)

# Footer
st.caption(f"Terakhir diperbarui: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
