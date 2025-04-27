import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from datetime import datetime
from io import BytesIO

# Başlangıç Animasyonu
st.markdown("<h1 style='text-align: center;'>🎉 Welcome to BEBE RUHI 🌎</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Global Earthquake Correlation & Prediction System</h3>", unsafe_allow_html=True)

# Sidebar Ayarları
st.sidebar.title("Filtre Ayarları")

min_magnitude = st.sidebar.slider("Minimum Magnitude", 4.0, 10.0, 4.0)
start_date = st.sidebar.date_input("Başlangıç Tarihi", datetime(2023, 1, 1))
end_date = st.sidebar.date_input("Bitiş Tarihi", datetime.now())
region1 = st.sidebar.text_input("Bölge 1 Anahtar Kelimeler (virgülle ayrın):", "Myanmar")
region2 = st.sidebar.text_input("Bölge 2 Anahtar Kelimeler (virgülle ayrın):", "Istanbul, Marmara")

# Veri çekme fonksiyonu
@st.cache_data
def fetch_earthquake_data():
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.csv"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        return pd.DataFrame()

# Verileri filtreleme
def filter_by_region(df, keywords):
    mask = df['place'].str.contains('|'.join(keywords), case=False, na=False)
    return df[mask]

# Korelasyon hesaplama
def calculate_correlation(df, region1_keywords, region2_keywords):
    df_r1 = filter_by_region(df, region1_keywords)
    df_r2 = filter_by_region(df, region2_keywords)
    if df_r1.empty or df_r2.empty:
        return None
    data = {
        'region1_counts': [len(df_r1)],
        'region2_counts': [len(df_r2)]
    }
    corr_df = pd.DataFrame(data)
    correlation = corr_df.corr().iloc[0, 1]
    return correlation

# Ana Uygulama İşleyişi
st.header("🌍 Deprem Verileri ve Korelasyon Analizi")

df = fetch_earthquake_data()

if not df.empty:
    # Zaman tiplerini düzenle
    df['time'] = pd.to_datetime(df['time'], errors='coerce')
    df = df.dropna(subset=['time'])  # NaT kayıtları temizle
    start_date = pd.to_datetime(str(start_date))
    end_date = pd.to_datetime(str(end_date))

    # Filtreleme
    df_filtered = df[(df['time'] >= start_date) &
                     (df['time'] <= end_date) &
                     (df['mag'] >= min_magnitude)]

    st.subheader("Son Deprem Verileri")
    st.dataframe(df_filtered[['time', 'place', 'mag']])

    # Magnitude Histogram
    st.subheader("Magnitude Dağılımı")
    fig, ax = plt.subplots()
    df_filtered['mag'].hist(bins=30, ax=ax)
    plt.xlabel('Magnitude')
    plt.ylabel('Frequency')
    st.pyplot(fig)

    # Dünya Haritası
    st.subheader("Depremlerin Dünya Haritası Üzerinde Gösterimi 🌎")
    m = folium.Map(location=[20, 0], zoom_start=2)
    for idx, row in df_filtered.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=3,
            color='red',
            fill=True,
        ).add_to(m)
    st_folium(m, width=700)

    # Korelasyon Analizi
    st.subheader("📊 Korelasyon Analizi")
    region1_keywords = [x.strip() for x in region1.split(',')]
    region2_keywords = [x.strip() for x in region2.split(',')]
    correlation = calculate_correlation(df_filtered, region1_keywords, region2_keywords)

    if correlation is not None:
        st.success(f"Bölge 1 ile Bölge 2 arasında korelasyon: {correlation:.2f}")
        if correlation > 0.5:
            st.info("Pozitif güçlü bir korelasyon mevcut!")
        elif correlation < -0.5:
            st.info("Negatif güçlü bir korelasyon mevcut!")
        else:
            st.info("Düşük veya zayıf korelasyon tespit edildi.")
    else:
        st.error("Korelasyon hesaplanamadı. Yeterli veri bulunamadı.")

    # CSV İndirme Butonu
    st.subheader("📥 Verileri İndir")
    towrite = BytesIO()
    df_filtered.to_csv(towrite, index=False)
    towrite.seek(0)
    st.download_button(
        label="Verileri CSV Olarak İndir",
        data=towrite,
        file_name='bebe_ruhi_earthquake_data.csv',
        mime='text/csv',
    )
else:
    st.error("Veri çekilemedi. Lütfen daha sonra tekrar deneyin.")
