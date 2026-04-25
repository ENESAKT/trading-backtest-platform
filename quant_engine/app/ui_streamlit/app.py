import streamlit as st

def main():
    st.set_page_config(
        page_title="Quant Engine Terminal",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Quant Engine - Algoritmik Araştırma Terminali")
    
    st.sidebar.title("Navigasyon")
    page = st.sidebar.radio("Sayfalar", ["Dashboard", "Matrix Tarayıcı", "Strateji Kurucu"])

    if page == "Dashboard":
        st.header("Dashboard & Veri İstasyonu")
        st.write("Sistem durumu ve veri sağlığı burada görünecek.")
    elif page == "Matrix Tarayıcı":
        st.header("Matrix Tarama Paneli")
        st.write("Sembollerin anlık durumu burada listelenecek.")
    elif page == "Strateji Kurucu":
        st.header("Strateji Kurucu ve Laboratuvar")
        st.write("Backtest parametreleri ve sonuç grafikleri burada yer alacak.")

if __name__ == "__main__":
    main()
