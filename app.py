import streamlit as st
import pandas as pd
import yfinance as yf

# Configuración de la página web
st.set_page_config(page_title="Monitor Merval", page_icon="📊", layout="wide")

st.title("📊 Monitor Inteligente S&P Merval")
st.subheader("Análisis fundamental automático de empresas argentinas en tiempo real")

st.markdown("Esta aplicación descarga los componentes del Merval, analiza sus balances y genera un ranking de **mejor a peor compra** según su ROE, Márgenes, PEG y P/B.")

# Botón para actualizar de forma manual si el usuario quiere
if st.button("🔄 Actualizar Datos del Día"):
    st.rerun()

# --- MOTOR DE DATOS ---
@st.cache_data(ttl=3600) # Guarda los datos por 1 hora para que la app sea súper rápida
def cargar_todo_el_merval():
    try:
        url_merval = "https://yahoo.com"
        tablas = pd.read_html(url_merval)
        df_componentes = tablas[0]
        empresas = df_componentes["Símbolo"].tolist()
    except:
        empresas = ["TGNO4.BA", "PAMP.BA", "AUSO.BA", "TGSU2.BA", "CEPU.BA", "YPFD.BA", "BBAR.BA", "SUPV.BA", "GGAL.BA"]
    
    datos_lista = []
    for ticker in empresas:
        try:
            accion = yf.Ticker(ticker)
            info = accion.info
            ficha = {
                "Empresa": ticker.replace(".BA", ""), 
                "Precio ARS": info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose"),
                "ROE (%)": (info.get("returnOnEquity") or 0) * 100,
                "Margen Neto (%)": (info.get("profitMargins") or 0) * 100,
                "Margen Operativo (%)": (info.get("operatingMargins") or 0) * 100,
                "PEG": info.get("pegRatio") or 0,
                "P/B (Precio/Libro)": info.get("priceToBook") or 0
            }
            if ficha["Precio ARS"]: datos_lista.append(ficha)
        except:
            pass
            
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

# Ejecutar el motor
with st.spinner("⏳ Conectando con BYMA y descargando balances..."):
    df_ranking = cargar_todo_el_merval()

# Columnas estéticas para el usuario
columnas_web = ["Empresa", "Precio ARS", "ROE (%)", "Margen Neto (%)", "Margen Operativo (%)", "PEG", "P/B (Precio/Libro)", "PUNTUACIÓN FINAL"]
df_mostrar = df_ranking[columnas_web].round(2)

# --- MOSTRAR TABLA EN LA WEB ---
st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

# --- BOTÓN DE DESCARGA EXCEL ---
@st.cache_data
def convertir_a_excel(df):
    return df.to_excel(index=False)

st.download_button(
    label="📥 Descargar Ranking en Excel",
    data=df_mostrar.to_csv(index=False).encode('utf-8'),
    file_name='ranking_merval.csv',
    mime='text/csv',
)
