import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import os

# --- ÖNEMLİ: PLAYWRIGHT KURULUMU ---
# Sunucuda tarayıcı eksikse otomatik kurar
os.system("playwright install chromium")

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="TJK Pro Max Mobil", layout="wide")
st.title("🏇 TJK Pro Max Mobil Analiz")
st.markdown("Telefondan tek tıkla canlı veri çekme ve derin istatistik analizi.")

# --- 1. JOKEY VE ANALİZ MANTIKLARI ---
def jokey_puani_hesapla(jokey_adi):
    # Usta jokey listesi - %10 ek form bonusu
    ustalar = ["HALİS KARATAŞ", "AHMET ÇELİK", "GÖKHAN KOCAKAYA", "ÖZCAN YILDIRIM", "VEDAT ABİŞ"]
    jokey_temiz = str(jokey_adi).upper().strip()
    if jokey_temiz in ustalar:
        return 1.10, "Usta Jokey (+10%)"
    return 1.0, "Normal Form"

def at_karakteri_sorgula(at_ismi):
    # İsim bazlı pist tahmini simülasyonu
    kum_ipuclari = ["OĞLU", "HAN", "BABA", "DEMİR"]
    if any(ipucu in str(at_ismi).upper() for ipucu in kum_ipuclari):
        return "Kum"
    return "Çim"

def analiz_final(at, bugunku_pist, bugunku_hava):
    try:
        h_puan = int(at['handikap']) if str(at['handikap']).isdigit() else 0
        kilo = float(str(at['kilo']).replace(',', '.'))
    except:
        h_puan, kilo = 0, 60.0

    # 1. Temel Güç: Handikap ve Kilo Dengesi
    skor = (h_puan * 2.5) - (kilo * 0.4)

    # 2. %30 Pist Uzmanlığı Faktörü
    at_uzmanlik = at_karakteri_sorgula(at['isim'])
    if at_uzmanlik == bugunku_pist:
        skor *= 1.30
        p_not = f"{bugunku_pist} Uzmanı (+30%)"
    else:
        skor *= 0.70
        p_not = "Pist Uyumsuz (-30%)"

    # 3. %15 Hava Durumu
    if bugunku_hava == "Yağmurlu" and bugunku_pist == "Kum":
        skor *= 1.15
        h_not = "Ağır Pist Avantajı (+15%)"
    else:
        h_not = "Normal Hava"

    # 4. %10 Jokey Form Etkisi
    j_carpan, j_not = jokey_puani_hesapla(at.get('jokey', ''))
    skor *= j_carpan
    
    return round(skor, 2), p_not, h_not, j_not, at_uzmanlik

# --- 2. CANLI VERİ ÇEKME MOTORU ---
def veri_cek_canli():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = "https://www.tjk.org/TR/YarisSever/Info/Daily/YarisProgrami"
        
        try:
            page.goto(url, wait_until="load", timeout=90000)
            time.sleep(5) # Tabloların yüklenmesi için bekleme
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            tablolar = soup.find_all('table', class_=['queryTable', 'programTable'])
            
            if not tablolar: return None

            tum_veriler = []
            for tablo in tablolar:
                satirlar = tablo.find_all('tr')[1:]
                for satir in satirlar:
                    sutunlar = satir.find_all('td')
                    if len(sutunlar) >= 10:
                        tum_veriler.append({
                            'isim': sutunlar[2].text.strip().split('(')[0].strip().upper(),
                            'jokey': sutunlar[7].text.strip().upper(),
                            'kilo': sutunlar[4].text.strip(),
                            'handikap': sutunlar[9].text.strip()
                        })
            browser.close()
            return tum_veriler
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")
            browser.close()
            return None

# --- 3. MOBİL ARAYÜZ ---
col1, col2 = st.columns(2)
with col1:
    pist_durumu = st.selectbox("Pist Tipi", ["Kum", "Çim"])
with col2:
    hava_durumu = st.selectbox("Hava", ["Güneşli", "Yağmurlu"])

if st.button("🚀 VERİLERİ ÇEK VE ANALİZ ET"):
    with st.spinner('TJK sitesine bağlanılıyor ve tarayıcı ayarlanıyor...'):
        ham_veriler = veri_cek_canli()
    
    if ham_veriler:
        rapor = []
        for at in ham_veriler:
            puan, p_not, h_not, j_not, uzm = analiz_final(at, pist_durumu, hava_durumu)
            rapor.append({
                'At İsmi': at['isim'],
                'Puan': puan,
                'Jokey': at['jokey'],
                'Pist Analizi': p_not,
                'Jokey Notu': j_not,
                'Uzmanlık': uzm
            })
        
        df = pd.DataFrame(rapor).sort_values(by='Puan', ascending=False)
        
        # --- ÖZET SONUÇLAR ---
        st.divider()
        if not df.empty:
            banko = df.iloc[0]
            st.success(f"🏆 **GÜNÜN BANKO ADAYI:** \n\n **{banko['At İsmi']}** ({banko['Puan']} Puan)")
            
            # Sürpriz analizi: İlk 3 dışındaki usta jokeyler
            surprizler = df.iloc[3:][df.iloc[3:]['Jokey Notu'].str.contains("Usta")] if len(df) > 3 else pd.DataFrame()
            if not surprizler.empty:
                st.warning(f"💣 **DİKKAT! SÜRPRİZ ADAYI:** \n\n **{surprizler.iloc[0]['At İsmi']}**")
        
        # --- TABLO ---
        st.subheader("📋 Detaylı Analiz Tablosu")
        st.dataframe(df, use_container_width=True)
    else:
        st.error("Bülten verisi çekilemedi. Henüz program açıklanmamış olabilir.")
