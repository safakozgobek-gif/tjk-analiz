import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="TJK Mobil Analiz", layout="wide")
st.title("🏇 TJK Akıllı Analiz")

# --- ANALİZ MANTIKLARI ---
def analiz_et(at):
    try:
        h_puan = int(at['handikap']) if str(at['handikap']).isdigit() else 0
        kilo = float(str(at['kilo']).replace(',', '.'))
    except: h_puan, kilo = 0, 60.0
    skor = (h_puan * 2.5) - (kilo * 0.4)
    return round(skor, 2)

# --- VERİ ÇEKME ---
def veri_cek_hizli():
    url = "https://www.tjk.org/TR/YarisSever/Info/Daily/YarisProgrami"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            tablolar = soup.find_all('table', class_=['queryTable', 'programTable'])
            
            veriler = []
            if not tablolar:
                return None

            for tablo in tablolar:
                satirlar = tablo.find_all('tr')[1:]
                for satir in satirlar:
                    sutunlar = satir.find_all('td')
                    if len(sutunlar) >= 10:
                        veriler.append({
                            'isim': sutunlar[2].text.strip().split('(')[0].strip().upper(),
                            'jokey': sutunlar[7].text.strip().upper(),
                            'kilo': sutunlar[4].text.strip(),
                            'handikap': sutunlar[9].text.strip()
                        })
            return veriler
        return None
    except:
        return None

# --- ARAYÜZ ---
if st.button("🚀 ANALİZİ BAŞLAT"):
    with st.spinner('TJK Bülteni taranıyor...'):
        data = veri_cek_hizli()
        
        if data:
            rapor = []
            for at in data:
                puan = analiz_et(at)
                rapor.append({
                    'At İsmi': at['isim'],
                    'Jokey': at['jokey'],
                    'Kilo': at['kilo'],
                    'Puan': puan
                })
            
            df = pd.DataFrame(rapor).sort_values(by='Puan', ascending=False)
            
            if not df.empty:
                st.success(f"🏆 Potansiyel Banko: {df.iloc[0]['At İsmi']}")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("Veriler işlenemedi. Lütfen daha sonra tekrar deneyin.")
        else:
            st.error("⚠️ Şu an bültene ulaşılamıyor. (TJK sitesi güncelleniyor olabilir. Lütfen sabah 09:00'dan sonra tekrar deneyin.)")
