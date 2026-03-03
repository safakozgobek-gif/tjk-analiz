import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="TJK Akıllı Analiz", layout="wide")
st.title("🏇 TJK Akıllı Analiz (Otomatik)")

# --- TARAYICI AYARI (Bulut Sunucu İçin Özel) ---
@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Streamlit Cloud'da Chromium kullanması için zorluyoruz
    try:
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        return webdriver.Chrome(service=service, options=options)
    except:
        # Eğer yukarıdaki başarısız olursa sistemdeki varsayılan yolu dene
        options.binary_location = "/usr/bin/chromium-browser"
        return webdriver.Chrome(options=options)

# --- ANALİZ MANTIKLARI ---
def analiz_et(at):
    try:
        h_puan = int(at['handikap']) if str(at['handikap']).isdigit() else 0
        kilo = float(str(at['kilo']).replace(',', '.'))
    except: h_puan, kilo = 0, 60.0
    skor = (h_puan * 2.5) - (kilo * 0.4)
    return round(skor, 2)

# --- VERİ ÇEKME ---
def veri_cek():
    driver = get_driver()
    try:
        driver.get("https://www.tjk.org/TR/YarisSever/Info/Daily/YarisProgrami")
        time.sleep(6) # Sayfa içeriğinin dolması için ek süre
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
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
        return veriler
    except Exception as e:
        st.error(f"Bağlantı Hatası: {e}")
        return None
    finally:
        driver.quit()

# --- ARAYÜZ ---
if st.button("🚀 GÜNLÜK BÜLTENİ TARA VE ANALİZ ET"):
    with st.spinner('TJK Sistemine bağlanılıyor... Lütfen bekleyin.'):
        data = veri_cek()
        if data:
            rapor = []
            for at in data:
                puan = analiz_et(at)
                rapor.append({
                    'At İsmi': at['isim'],
                    'Jokey': at['jokey'],
                    'Kilo': at['kilo'],
                    'Handikap': at['handikap'],
                    'Puan': puan
                })
            
            df = pd.DataFrame(rapor).sort_values(by='Puan', ascending=False)
            if not df.empty:
                st.success(f"🏆 Banko Adayı: {df.iloc[0]['At İsmi']}")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("Veri okundu ama tablo boş.")
        else:
            st.error("Bülten verisi çekilemedi. Bağlantı zaman aşımına uğramış olabilir.")
