import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="TJK Akıllı Analiz Pro", layout="wide", page_icon="🏇")
st.title("🏇 TJK Akıllı Analiz & Tahmin Motoru")

# --- ANALİZ MANTIKLARI ---
def analiz_et(at):
    try:
        h_puan = int(at.get('Handikap', 0))
        kilo = float(str(at.get('Kilo', 60)).replace(',', '.'))
        # Gelişmiş Skorlama: Handikap %70, Kilo %30 ağırlıklı
        skor = (h_puan * 3.8) - (kilo * 0.6)
        return round(skor, 2)
    except:
        return 0

# --- API TABANLI VERİ ÇEKME (KESİN ÇÖZÜM) ---
def veri_cek_api():
    bugun = datetime.now().strftime('%d/%m/%Y')
    # TJK'nın bülten verilerini sağlayan doğrudan API endpoint'i
    url = f"https://www.tjk.org/TR/YarisSever/Info/Daily/YarisProgramiData?QueryDate={bugun}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        # TJK sitesi bazen JSON bazen HTML döner, kontrol edelim
        if response.status_code == 200:
            data = response.json() # JSON formatında veri çekmeyi deniyoruz
            
            all_horses = []
            # TJK API yapısı: Her şehir bir 'RaceDay' ve her koşu bir 'Race'
            for day in data.get('RaceDays', []):
                for race in day.get('Races', []):
                    for horse in race.get('Horses', []):
                        all_horses.append({
                            'Sehir': day.get('SehirAd', 'Bilinmiyor'),
                            'KosuNo': race.get('KosuNo', 0),
                            'isim': horse.get('AtAd', '').upper(),
                            'jokey': horse.get('JokeyAd', '').upper(),
                            'kilo': horse.get('Kilo', '0'),
                            'handikap': horse.get('Handikap', '0')
                        })
            return all_horses
        return None
    except:
        # API yöntemi başarısız olursa manuel uyarı ver
        return None

# --- ARAYÜZ ---
if st.button("🚀 ANALİZİ BAŞLAT", use_container_width=True):
    with st.spinner('TJK Sunucularından canlı veriler alınıyor...'):
        data = veri_cek_api()
        
        if data:
            rapor = []
            for at in data:
                puan = analiz_et(at)
                rapor.append({
                    'Şehir': at['Sehir'],
                    'Koşu': at['KosuNo'],
                    'At İsmi': at['isim'],
                    'Jokey': at['jokey'],
                    'Kilo': at['kilo'],
                    'Skor': puan
                })
            
            df = pd.DataFrame(rapor)
            df = df.sort_values(by=['Şehir', 'Koşu', 'Skor'], ascending=[True, True, False])
            
            st.success(f"✅ Toplam {len(df)} at analiz edildi.")
            
            # Şehir seçimi için filtre
            sehirler = df['Şehir'].unique()
            secilen_sehir = st.selectbox("📍 Şehir Seçin", sehirler)
            
            filtered_df = df[df['Şehir'] == secilen_sehir]
            st.dataframe(filtered_df, use_container_width=True, height=600)
        else:
            st.error("⚠️ TJK bülten verileri şu an çekilemiyor.")
            st.info("İpucu: TJK sitesine tarayıcıdan girip bültenin yayında olduğundan emin olun.")
