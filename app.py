import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# Configuración de la página web
st.set_page_config(page_title="Monitor Merval", page_icon="📊", layout="wide")

st.title("📊 Monitor Inteligente S&P Merval")
st.subheader("Análisis fundamental automático de empresas argentinas en tiempo real")
st.markdown("Esta aplicación descarga los componentes del Merval, analiza sus balances y genera un ranking de **mejor a peor compra**.")

# Botón para actualizar manualmente
if st.button("🔄 Actualizar Datos del Día"):
    st.cache_data.clear()
    st.rerun()

# --- MOTOR DE DATOS EN VIVO ---
@st.cache_data(ttl=3600)
def cargar_todo_el_merval():
    # Lista de empresas del panel local en pesos
    empresas = [
        "TGNO4.BA", "PAMP.BA", "AUSO.BA", "TGSU2.BA", "CEPU.BA", "YPFD.BA", 
        "BBAR.BA", "SUPV.BA", "GGAL.BA", "ALUA.BA", "EDN.BA", "LOMA.BA", 
        "CRES.BA", "TXAR.BA", "TRAN.BA", "BYMA.BA", "VALO.BA", "COME.BA", "METR.BA"
    ]
    
    datos_lista = []
    for ticker in empresas:
        try:
            accion = yf.Ticker(ticker)
            info = accion.info
            ficha = {
                "Empresa": ticker.replace(".BA", ""), 
                "Precio ARS": info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0,
                "ROE (%)": (info.get("returnOnEquity") or 0) * 100,
                "Margen Neto (%)": (info.get("profitMargins") or 0) * 100,
                "Margen Operativo (%)": (info.get("operatingMargins") or 0) * 100,
                "PEG": info.get("pegRatio") or 0,
                "P/B (Precio/Libro)": info.get("priceToBook") or 0
            }
            if ficha["Precio ARS"] > 0: 
                datos_lista.append(ficha)
        except:
            pass
            
    if not datos_lista:
        return pd.DataFrame()
        
    df = pd.DataFrame(datos_lista)
    
    # Sistema de scoring básico para el ranking
    for col in ["ROE (%)", "Margen Neto (%)", "Margen Operativo (%)", "PEG", "P/B (Precio/Libro)"]:
        if col in df.columns and df[col].max() != df[col].min():
            if col in ["PEG", "P/B (Precio/Libro)"]:
                df[f"P_{col}"] = ((df[col].max() - df[col]) / (df[col].max() - df[col].min())) * 100
            else:
                df[f"P_{col}"] = ((df[col] - df[col].min()) / (df[col].max() - df[col].min())) * 100
        else:
            df[f"P_{col}"] = 50

    df["PUNTUACIÓN FINAL"] = (df["P_ROE (%)"] + df["P_Margen Neto (%)"] + df["P_Margen Operativo (%)"] + df["P_PEG"] + df["P_P/B (Precio/Libro)"]) / 5
    return df.sort_values(by="PUNTUACIÓN FINAL", ascending=False)

# Ejecutar el motor con indicador de carga
with st.spinner("⏳ Conectando con la Bolsa de Buenos Aires y descargando balances..."):
    df_ranking = cargar_todo_el_merval()

if not df_ranking.empty:
    columnas_web = ["Empresa", "Precio ARS", "ROE (%)", "Margen Neto (%)", "Margen Operativo (%)", "PEG", "P/B (Precio/Libro)", "PUNTUACIÓN FINAL"]
    df_mostrar = df_ranking[columnas_web].round(2)

    # --- MOSTRAR TABLA EN LA WEB ---
    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

    # --- BOTÓN DE DESCARGA ---
    st.download_button(
        label="📥 Descargar Ranking Completo (CSV)",
        data=df_mostrar.to_csv(index=False).encode('utf-8'),
        file_name='ranking_merval.csv',
        mime='text/csv',
    )
else:
    st.error("❌ No se pudieron recuperar datos de la Bolsa en este momento. Reintentá en unos segundos.")
