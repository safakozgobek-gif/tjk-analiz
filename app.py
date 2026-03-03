import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import os

# --- OTOMATİK TARAYICI KURULUMU ---
# Bu komut sunucuyu zorlayarak tarayıcıyı kurdurur
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="TJK Otomatik Analiz", layout="wide")
st.title("🏇 TJK Akıllı Analiz (Tam Otomatik)")
st.info("Sistem pist tipini ve hava durumunu bültenden otomatik okur.")

# --- ANALİZ MANTIKLARI ---
def analiz_et(at, pist_tipi):
    try:
        h_puan = int(at['handikap']) if str(at['handikap']).isdigit() else 0
        kilo = float(str(at['kilo']).replace(',', '.'))
    except: h_puan, kilo = 0, 60.0

    skor = (h_puan * 2.5) - (kilo * 0.4)
    
    # Otomatik Pist Uzmanlığı
    at_ismi = at['isim'].upper()
    is_kum_ati = any(x in at_ismi for x in ["BABA", "OĞLU", "HAN", "DEMİR"])
    
    if (is_kum_ati and "KUM" in pist_tipi.upper()) or (not is_kum_ati and "ÇİM" in pist_tipi.upper()):
        skor *= 1.20 # Pist uyumu bonusu
        not_v = "Pist Uygun"
    else:
        not_v = "Pist Belirsiz"
        
    return round(skor, 2), not_v

# --- CANLI VE OTOMATİK VERİ ÇEKME ---
def veri_cek_otomatik():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            # TJK Program sayfasına git
            page.goto("https://www.tjk.org/TR/YarisSever/Info/Daily/YarisProgrami", wait_until="networkidle", timeout=90000)
            time.sleep(5)
            
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Pist bilgisini sayfadan otomatik bulalım
            # Genelde "Pist: Kum", "Pist: Çim" şeklinde bir yazı olur
            pist_metni = soup.find(text=lambda t: "Pist:" in t) if soup.find(text=lambda t: "Pist:" in t) else "Kum (Tahmin)"
            
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
                                'handikap': sutunlar[9].text.strip(),
                                'pist_bilgisi': str(pist_metni).strip()
                            })
            browser.close()
            return veriler
        except Exception as e:
            st.error(f"Hata detayı: {e}")
            return None

# --- ARAYÜZ ---
if st.button("🚀 GÜNLÜK BÜLTENİ TARA VE ANALİZ ET"):
    with st.spinner('TJK Sistemine bağlanılıyor...'):
        data = veri_cek_otomatik()
        if data:
            pist_bilgisi = data[0]['pist_bilgisi']
            st.write(f"🔍 **Tespit Edilen Pist:** {pist_bilgisi}")
            
            rapor = []
            for at in data:
                puan, durum = analiz_et(at, pist_bilgisi)
                rapor.append({
                    'At İsmi': at['isim'],
                    'Jokey': at['jokey'],
                    'Puan': puan,
                    'Analiz': durum
                })
            
            df = pd.DataFrame(rapor).sort_values(by='Puan', ascending=False)
            st.success(f"🏆 Banko Adayı: {df.iloc[0]['At İsmi']}")
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Veri çekilemedi. Lütfen birkaç dakika sonra tekrar deneyin.")
