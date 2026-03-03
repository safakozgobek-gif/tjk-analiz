import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import subprocess

# --- PLAYWRIGHT KURULUMU ---
# Sunucuda tarayıcıyı sessizce ve hatasız kurması için
@st.cache_resource
def install_playwright():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Kurulum Hatası: {e}")

install_playwright()

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="TJK Mobil Pro Max", layout="wide")
st.title("🏇 TJK Pro Max Mobil Analiz")

# --- ANALİZ FONKSİYONLARI ---
def jokey_puani_hesapla(jokey_adi):
    ustalar = ["HALİS KARATAŞ", "AHMET ÇELİK", "GÖKHAN KOCAKAYA", "ÖZCAN YILDIRIM", "VEDAT ABİŞ"]
    if str(jokey_adi).upper().strip() in ustalar:
        return 1.10, "Usta Jokey (+10%)"
    return 1.0, "Normal"

def analiz_final(at, pist, hava):
    try:
        h_puan = int(at['handikap']) if str(at['handikap']).isdigit() else 0
        kilo = float(str(at['kilo']).replace(',', '.'))
    except: h_puan, kilo = 0, 60.0
    skor = (h_puan * 2.5) - (kilo * 0.4)
    j_carpan, j_not = jokey_puani_hesapla(at.get('jokey', ''))
    return round(skor * j_carpan, 2), j_not

# --- CANLI VERİ ÇEKME (Hata Giderilmiş) ---
def veri_cek_canli():
    with sync_playwright() as p:
        # Sunucu kısıtlamalarını aşmak için özel argümanlar
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        try:
            # TJK sitesine daha güvenli bir giriş yapıyoruz
            page.goto("https://www.tjk.org/TR/YarisSever/Info/Daily/YarisProgrami", wait_until="load", timeout=90000)
            time.sleep(7) # Verilerin tam oturması için bekleme süresini artırdık
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            tablolar = soup.find_all('table', class_=['queryTable', 'programTable'])
            
            veriler = []
            if tablolar:
                for tablo in tablolar:
                    for satir in tablo.find_all('tr')[1:]:
                        sutunlar = satir.find_all('td')
                        if len(sutunlar) >= 10:
                            veriler.append({
                                'isim': sutunlar[2].text.strip().split('(')[0].strip().upper(),
                                'jokey': sutunlar[7].text.strip().upper(),
                                'kilo': sutunlar[4].text.strip(),
                                'handikap': sutunlar[9].text.strip()
                            })
            browser.close()
            return veriler
        except Exception as e:
            st.warning(f"Bağlantı Detayı: {e}")
            browser.close()
            return None

# --- ARAYÜZ ---
pist = st.selectbox("Pist Tipi", ["Kum", "Çim"])
hava = st.selectbox("Hava Durumu", ["Güneşli", "Yağmurlu"])

if st.button("🚀 ANALİZİ BAŞLAT"):
    with st.spinner('TJK Bülteni taranıyor... Lütfen sayfayı kapatmayın.'):
        data = veri_cek_canli()
        if data:
            rapor = []
            for at in data:
                puan, n_not = analiz_final(at, pist, hava)
                rapor.append({**at, 'Puan': puan, 'Not': n_not})
            
            df = pd.DataFrame(rapor).sort_values(by='Puan', ascending=False)
            
            # ÖZET VE TABLO
            st.success(f"🏆 Kazanma Potansiyeli En Yüksek: {df.iloc[0]['At İsmi']}")
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Şu an veri çekilemiyor. Bülten henüz yayınlanmamış olabilir veya sunucu meşgul. Lütfen 1 dakika sonra tekrar deneyin.")
