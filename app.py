import streamlit as st
from PIL import Image

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="TJK Çoklu Analiz", layout="wide", page_icon="🏇")
st.title("🏇 TJK Çoklu Görsel Analiz Sistemi")

st.info("""
**Talimatlar:** 1. TJK bültenini, son yarış performanslarını veya ganyan tablolarını (birden fazla olabilir) yükleyin.
2. Tüm görseller yüklendiğinde, aynı görselleri Gemini'ye gönderip analizi başlatın.
""")

# accept_multiple_files=True parametresi ile artık birden fazla dosya seçebilirsin
uploaded_files = st.file_uploader("Bülten Görsellerini Yükleyin (Maks 5 Adet)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    st.write(f"✅ {len(uploaded_files)} adet görsel yüklendi.")
    
    # Görselleri yan yana göster
    cols = st.columns(len(uploaded_files))
    for i, uploaded_file in enumerate(uploaded_files):
        image = Image.open(uploaded_file)
        cols[i].image(image, caption=f"Görsel {i+1}", use_container_width=True)
    
    st.divider()
    st.success("🚀 Veriler hazır! Şimdi bu görselleri toplu halde Gemini'ye göndererek 'Eksikleri tamamla, Banko ve Sürprizi söyle' deyin.")
