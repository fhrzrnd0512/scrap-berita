import streamlit as st
import pandas as pd
import urllib.parse
import feedparser
from datetime import datetime
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import re

# ==========================================
# 1. Konfigurasi Halaman & UI
# ==========================================
st.set_page_config(page_title="Portal Analisis Berita Ekonomi", layout="wide")

# Integrasi Google Analytics 4
st.markdown("""
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KVF1YFEVZQ"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'G-KVF1YFEVZQ');
    </script>
""", unsafe_allow_html=True)

st.title("Portal Analisis Sentimen & Berita Ekonomi")
st.markdown("<span style='font-size: 16px; opacity: 0.8;'>Tim Neraca Produksi BPS Provinsi Sumatera Utara</span>", unsafe_allow_html=True)

# Kamus Global
kamus_sentimen = {
    "naik": "Positif (Optimisme)", "meningkat": "Positif (Optimisme)", "tumbuh": "Positif (Optimisme)", 
    "surplus": "Positif (Optimisme)", "panen": "Positif (Optimisme)", "bantuan": "Positif (Optimisme)", 
    "untung": "Positif (Optimisme)", "laba": "Positif (Optimisme)", "subsidi": "Positif (Optimisme)", 
    "positif": "Positif (Optimisme)", "maju": "Positif (Optimisme)",
    "anjlok": "Negatif (Tekanan)", "turun": "Negatif (Tekanan)", "merosot": "Negatif (Tekanan)", 
    "inflasi": "Negatif (Tekanan)", "rugi": "Negatif (Tekanan)", "mahal": "Negatif (Tekanan)", 
    "langka": "Negatif (Tekanan)", "gagal": "Negatif (Tekanan)", "lesu": "Negatif (Tekanan)", 
    "krisis": "Negatif (Tekanan)", "defisit": "Negatif (Tekanan)", "phk": "Negatif (Tekanan)", "ancaman": "Negatif (Tekanan)"
}

wilayah_sumut = ["Medan", "Binjai", "Tebing Tinggi", "Pematangsiantar", "Tanjungbalai", "Sibolga", "Padangsidimpuan", "Gunungsitoli", 
                 "Langkat", "Deli Serdang", "Karo", "Simalungun", "Asahan", "Labuhanbatu", "Tapanuli Selatan", "Nias", 
                 "Mandailing Natal", "Pakpak Bharat", "Humbang Hasundutan", "Samosir", "Serdang Bedagai", "Batu Bara", "Padang Lawas", 
                 "Dairi", "Labuhanbatu Utara", "Labuhanbatu Selatan", "Nias Barat", "Nias Selatan", "Nias Utara", 
                 "Padang Lawas Utara", "Toba", "Tapanuli Utara", "Tapanuli Tengah"]

stopwords_id = ["di", "ke", "dari", "dan", "atau", "untuk", "yang", "dengan", "pada", "dalam", "ini", "itu", "akan", "bisa", "ada", "tidak", "tahun", "hari", "rp", "sumut", "sumatera", "utara"]

# ==========================================
# 2. Sidebar
# ==========================================
with st.sidebar:
    st.header("Parameter Penarikan Baru")
    
    pilihan_tema = {
        "Kustom (Gunakan Kata Kunci Sendiri)": "kustom",
        "Inflasi & Komoditas Pangan": '"harga bahan pokok" OR cabai OR beras OR inflasi Sumatera Utara',
        "Sektor Real Estat & Properti": '"real estat" OR properti OR perumahan Sumatera Utara',
        "Sektor Pertanian": 'panen OR pupuk OR cuaca petani Sumatera Utara',
        "Ekspor-Impor & CPO": 'ekspor OR impor OR CPO OR Pelabuhan Belawan Sumatera Utara',
        "Belanja Pemerintah & Infrastruktur": 'APBD OR "belanja pemerintah" OR "proyek infrastruktur" Sumatera Utara'
    }
    
    tema = st.selectbox("Pilih Fokus Analisis PDRB:", list(pilihan_tema.keys()))
    
    if pilihan_tema[tema] == "kustom":
        keyword = st.text_input("Kata Kunci Berita:", "ekonomi OR PDRB Sumatera Utara")
    else:
        keyword = pilihan_tema[tema]
        
    start_date = st.date_input("Tanggal Mulai", datetime(2026, 7, 1))
    end_date = st.date_input("Tanggal Selesai", datetime(2026, 9, 30))
    
    tarik_btn = st.button("Tarik & Analisis Data", use_container_width=True, type="primary")

# ==========================================
# 3. Logika Scraping & Processing
# ==========================================
@st.cache_data(show_spinner=False)
def scrape_google_news(query, start, end):
    query_gabungan = f"{query} after:{start} before:{end}"
    url_encoded = urllib.parse.quote(query_gabungan)
    rss_url = f"https://news.google.com/rss/search?q={url_encoded}&hl=id&gl=ID&ceid=ID:id"
    
    feed = feedparser.parse(rss_url)
    berita_list = []
    
    for entry in feed.entries:
        try:
            waktu_raw = entry.published
            dt_obj = datetime.strptime(waktu_raw[5:16], "%d %b %Y")
            bulan_tahun = dt_obj.strftime("%Y-%m")
        except:
            bulan_tahun = "Bulan Tidak Diketahui"
            
        berita_list.append({
            "Tanggal_Terbit": entry.published,
            "Bulan": bulan_tahun,
            "Judul": entry.title,
            "Media": entry.source.title if hasattr(entry, 'source') else "Google News",
            "Tautan": entry.link
        })
    return pd.DataFrame(berita_list)

def clean_text(df):
    if df.empty: return []
    # Membersihkan teks dan tokenisasi
    all_titles = " ".join(df['Judul'].astype(str)).lower()
    all_titles = re.sub(r'\s*-\s*google berita.*', '', all_titles)
    all_titles = re.sub(r'[^a-z\s]', ' ', all_titles)
    words = all_titles.split()
    # Filter stopwords
    clean_words = [word for word in words if word not up in stopwords_id and len(word) > 1]
    return clean_words

# ==========================================
# 4. Tampilan Tab
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Data Tabel", "Sentimen Bulanan", "Sebaran Wilayah", "Frekuensi Isu", "Peta Topik", "Komparasi Historis"])

if tarik_btn:
    with st.spinner('Menarik & menganalisis teks...'):
        st.session_state.df_hasil = scrape_google_news(keyword, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if not st.session_state.df_hasil.empty:
            st.success(f"Berhasil menganalisis {len(st.session_state.df_hasil)} berita!")
        else:
            st.warning("Tidak ada berita ditemukan untuk parameter tersebut.")

# Rendering jika data tersedia
if 'df_hasil' in st.session_state and not st.session_state.df_hasil.empty:
    df = st.session_state.df_hasil
    
    with tab1:
        st.dataframe(df, use_container_width=True)
        
        # Tombol Unduh
        col1, col2 = st.columns(2)
        csv = df.to_csv(index=False).encode('utf-8')
        col1.download_button("Unduh CSV", data=csv, file_name=f"Berita_{datetime.now().date()}.csv", mime='text/csv', use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        col2.download_button("Unduh Excel", data=buffer.getvalue(), file_name=f"Berita_{datetime.now().date()}.xlsx", mime="application/vnd.ms-excel", use_container_width=True)
        
    with tab2:
        words = clean_text(df)
        df_words = pd.DataFrame(words, columns=['kata'])
        # Gabungkan dengan kamus sentimen
        df_sentimen = df_words[df_words['kata'].isin(kamus_sentimen.keys())].copy()
        df_sentimen['sentimen'] = df_sentimen['kata'].map(kamus_sentimen)
        
        # Ekstrak bulan dari dataframe asli ke dataframe kata (disederhanakan)
        # Menghitung agregat kasar berdasarkan seluruh kemunculan di triwulan
        if not df_sentimen.empty:
            sent_count = df_sentimen['sentimen'].value_counts().reset_index()
            sent_count.columns = ['Jenis Sentimen', 'Frekuensi']
            fig = px.bar(sent_count, x='Jenis Sentimen', y='Frekuensi', color='Jenis Sentimen', 
                         color_discrete_map={"Positif (Optimisme)": "#27ae60", "Negatif (Tekanan)": "#e74c3c"},
                         title="Volume Sentimen Makroekonomi")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak ada kata sentimen yang terdeteksi.")
            
    with tab3:
        wilayah_count = []
        for w in wilayah_sumut:
            jml = df['Judul'].str.contains(w, case=False, na=False).sum()
            if jml > 0:
                wilayah_count.append({"Wilayah": w, "Total": jml})
        
        if wilayah_count:
            df_wilayah = pd.DataFrame(wilayah_count).sort_values(by='Total', ascending=True)
            fig2 = px.bar(df_wilayah, x='Total', y='Wilayah', orientation='h', title="Intensitas Pemberitaan Isu Ekonomi per Wilayah")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Tidak ada penyebutan wilayah spesifik.")

    with tab4:
        words = clean_text(df)
        if words:
            df_freq = pd.Series(words).value_counts().head(15).reset_index()
            df_freq.columns = ['Kata Kunci', 'Jumlah']
            fig3 = px.bar(df_freq.sort_values(by='Jumlah', ascending=True), x='Jumlah', y='Kata Kunci', orientation='h', title="Top 15 Frekuensi Topik")
            st.plotly_chart(fig3, use_container_width=True)

    with tab5:
        words = clean_text(df)
        if words:
            word_freq = pd.Series(words).value_counts().to_dict()
            wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='Dark2').generate_from_frequencies(word_freq)
            fig4, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig4)

with tab6:
    st.header("Komparasi Historis (Q-to-Q / Y-on-Y)")
    st.info("Unggah file CSV hasil tarikan sebelumnya untuk membandingkan pergeseran isu.")
    
    col_a, col_b, col_c = st.columns(3)
    file1 = col_a.file_uploader("1. TW Berjalan (CSV)", type=['csv'])
    file2 = col_b.file_uploader("2. TW Sebelumnya (CSV)", type=['csv'])
    file3 = col_c.file_uploader("3. TW Tahun Lalu (CSV)", type=['csv'])
    
    if st.button("Bandingkan Tren", type="primary"):
        dfs = []
        if file1: 
            d1 = pd.read_csv(file1); d1['Periode'] = "1. TW Berjalan"; dfs.append(d1)
        if file2: 
            d2 = pd.read_csv(file2); d2['Periode'] = "2. TW Sebelumnya (Q-to-Q)"; dfs.append(d2)
        if file3: 
            d3 = pd.read_csv(file3); d3['Periode'] = "3. TW Tahun Lalu (Y-on-Y)"; dfs.append(d3)
            
        if dfs:
            df_komp = pd.concat(dfs, ignore_index=True)
            
            # Analisis Sentimen Komparasi
            st.subheader("Pergeseran Sentimen Makroekonomi")
            semua_kata = []
            for _, row in df_komp.iterrows():
                judul = re.sub(r'[^a-z\s]', ' ', str(row['Judul']).lower())
                for kata in judul.split():
                    if kata in kamus_sentimen:
                        semua_kata.append({"Periode": row['Periode'], "Sentimen": kamus_sentimen[kata]})
            
            if semua_kata:
                df_sent_komp = pd.DataFrame(semua_kata).groupby(['Periode', 'Sentimen']).size().reset_index(name='Frekuensi')
                fig_komp1 = px.bar(df_sent_komp, x='Periode', y='Frekuensi', color='Sentimen', barmode='group',
                                   color_discrete_map={"Positif (Optimisme)": "#27ae60", "Negatif (Tekanan)": "#e74c3c"})
                st.plotly_chart(fig_komp1, use_container_width=True)
                
        else:
            st.error("Unggah minimal 1 file CSV untuk membandingkan.")

st.markdown("<hr><p style='text-align: center; color: gray; font-size: 13px;'>2026 dibuat dengan sepenuh hati dengan ☕ dan ❤️</p>", unsafe_allow_html=True)
