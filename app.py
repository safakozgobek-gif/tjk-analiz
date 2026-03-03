import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import subprocess

# --- PLAYWRIGHT KURULUM KONTROLÜ ---
@st.cache_resource
def install_playwright():
    subprocess.run(["playwright", "install", "chromium"])

install_playwright()

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="TJK Mobil Pro Max", layout="wide")
st.title("🏇 TJK Pro Max Mobil Analiz")

# --- ANALİZ FONKSİYONLARI (Senin Mantığın) ---
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

# --- CANLI VERİ ÇEKME ---
def veri_cek_canli():
    with sync_playwright() as p:
        # Önemli: Yavaş internet ve sunucu için bekleme süreleri artırıldı
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        try:
            page.goto("https://www.tjk.org/TR/YarisSever/Info/Daily/YarisProgrami", wait_until="networkidle", timeout=90000)
            time.sleep(5)
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
            browser.close()
            return None

# --- ARAYÜZ ---
pist = st.selectbox("Pist Tipi", ["Kum", "Çim"])
hava = st.selectbox("Hava Durumu", ["Güneşli", "Yağmurlu"])

if st.button("🚀 ANALİZİ BAŞLAT"):
    with st.spinner('TJK Bülteni taranıyor...'):
        data = veri_cek_canli()
        if data:
            rapor = [ {**at, 'Puan': analiz_final(at, pist, hava)[0], 'Not': analiz_final(at, pist, hava)[1]} for at in data ]
            df = pd.DataFrame(rapor).sort_values(by='Puan', ascending=False)
            st.success(f"🏆 Banko Adayı: {df.iloc[0]['At İsmi']}")
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Bağlantı başarısız veya bülten henüz hazır değil.")
