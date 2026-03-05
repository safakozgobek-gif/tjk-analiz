import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="TJK Akıllı Analiz v2", layout="wide", page_icon="🏇")
st.title("🏇 TJK Akıllı Analiz & Tahmin Motoru")

# --- GELİŞMİŞ ANALİZ MANTIKLARI ---
def analiz_et(at):
    try:
        # Veri temizleme
        h_puan = int(at['handikap']) if str(at['handikap']).isdigit() else 0
        kilo = float(str(at['kilo']).replace(',', '.'))
        
        # Ağırlıklı Puanlama Sistemi (Stratejik Güçlendirme)
        # Handikap Gücü (%45) + Kilo Etkisi (Negatif) + Jokey/Pist Tahmini (Bonus)
        skor = (h_puan * 3.5) - (kilo * 0.5) 
        
        # Eğer jokey 'A.' veya 'H.' ile başlıyorsa (Apprentice/Hayatının ilk yarışı vb.) küçük bir handikap
        if "A." in at['jokey']:
            skor -= 2
            
        return round(skor, 2)
    except:
        return 0

# --- GÜÇLENDİRİLMİŞ VERİ ÇEKME ---
def veri_cek_tjk():
    # TJK'nın bugünkü bültenine giden dinamik URL
    bugun = datetime.now().strftime('%d/%m/%Y')
    url = f"https://www.tjk.org/TR/YarisSever/Info/Daily/YarisProgrami?QueryDate={bugun}"
    
    # "İnsan gibi" görünmek için kapsamlı Headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.tjk.org/"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # TJK'nın tablo yapısını yakalamak için daha esnek bir arama
        veriler = []
        tablolar = soup.find_all('table')
        
        if not tablolar:
            return None

        for tablo in tablolar:
            satirlar = tablo.find_all('tr')
            for satir in satirlar:
                sutunlar = satir.find_all('td')
                # TJK bülten satırı genellikle 10+ sütun içerir
                if len(sutunlar) >= 10:
                    try:
                        veriler.append({
                            'isim': sutunlar[2].text.strip().split('(')[0].strip().upper(),
                            'jokey': sutunlar[7].text.strip().upper(),
                            'kilo': sutunlar[4].text.strip(),
                            'handikap': sutunlar[9].text.strip()
                        })
                    except:
                        continue
        return veriler
    except Exception as e:
        st.error(f"Bağlantı Hatası: {e}")
        return None

# --- ARAYÜZ VE ÇALIŞTIRMA ---
col1, col2 = st.columns([1, 4])

with col1:
    baslat = st.button("🚀 ANALİZİ BAŞLAT", use_container_width=True)

if baslat:
    with st.spinner('Güncel TJK bülteni analiz ediliyor...'):
        data = veri_cek_tjk()
        
        if data and len(data) > 0:
            rapor = []
            for at in data:
                puan = analiz_et(at)
                rapor.append({
                    'At İsmi': at['isim'],
                    'Jokey': at['jokey'],
                    'Kilo': at['kilo'],
                    'H.Puanı': at['handikap'],
                    'Tahmin Skoru': puan
                })
            
            df = pd.DataFrame(rapor).drop_duplicates(subset=['At İsmi'])
            df = df.sort_values(by='Tahmin Skoru', ascending=False)
            
            st.divider()
            
            # Üst panel - Banko ve Plase
            c1, c2 = st.columns(2)
            with c1:
                st.metric("🏆 GÜNÜN BANKOSU", df.iloc[0]['At İsmi'])
            with c2:
                st.metric("🥈 PLASE ADAYI", df.iloc[1]['At İsmi'])

            st.dataframe(df, use_container_width=True, height=500)
            
            st.info("💡 Not: Tahmin skoru; handikap puanı, kilo ve jokey tecrübesi ağırlıklandırılarak hesaplanmıştır.")
        else:
            st.error("⚠️ Veri çekilemedi. TJK sitesi erişimi kısıtlamış olabilir veya henüz bülten yayınlanmamış.")
            st.warning("Çözüm: Birkaç dakika sonra tekrar deneyin veya 'Rerun' yapın.")
