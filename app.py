import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import json
from sklearn.linear_model import LinearRegression
import io

# ---------------- CONFIG ----------------

st.set_page_config(
    page_title="Antiquaria Dashboard",
    layout="wide"
)

# ---------------- STYLE ----------------

st.markdown("""
<style>
body {
    background-color: #0e0e0e;
    color: gold;
}
.stApp {
    background: linear-gradient(#0e0e0e, #1c1c1c);
}
h1, h2, h3 {
    color: gold;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION ----------------

if "data" not in st.session_state:
    st.session_state.data = None

# ---------------- FUNCTIONS ----------------

def clean_data(df):
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str)
            df[col] = df[col].str.replace("€","")
            df[col] = df[col].str.replace("%","")
            df[col] = df[col].str.replace(",","")
            df[col] = df[col].str.strip()

        try:
            df[col] = pd.to_numeric(df[col])
        except:
            pass

    return df


def calc_profit(df):
    if "Prezzo Vendita" in df.columns and "Costo" in df.columns:
        df["Profitto"] = df["Prezzo Vendita"] - df["Costo"]
        df["Margine %"] = (df["Profitto"] / df["Costo"]) * 100
    return df


# ---------------- SIDEBAR ----------------

st.sidebar.title("📊 Antiquaria Control")

menu = st.sidebar.radio(
    "Menu",
    ["Upload", "Dashboard", "Analisi", "Grafici", "Magazzino", "Previsioni", "Backup", "AI"]
)

# ---------------- UPLOAD ----------------

if menu == "Upload":

    st.title("📁 Importazione File")

    file = st.file_uploader(
        "Carica CSV / Excel / PDF",
        type=["csv","xlsx","pdf"]
    )

    if file:

        try:

            if file.name.endswith(".csv"):
                df = pd.read_csv(file, sep=None, engine="python")

            elif file.name.endswith(".xlsx"):
                df = pd.read_excel(file)

            elif file.name.endswith(".pdf"):
                import tabula
                tables = tabula.read_pdf(file, pages="all")
                df = pd.concat(tables)

            df = clean_data(df)
            df = calc_profit(df)

            st.session_state.data = df

            st.success(f"✅ Importati {len(df)} record")

            st.dataframe(df)

        except Exception as e:
            st.error(f"Errore: {e}")

# ---------------- DASHBOARD ----------------

if menu == "Dashboard":

    st.title("📈 Dashboard")

    df = st.session_state.data

    if df is None:
        st.warning("Carica un file prima")
    else:

        entrate = df.get("Prezzo Vendita", pd.Series()).sum()
        costi = df.get("Costo", pd.Series()).sum()
        profitto = entrate - costi
        margine = df.get("Margine %", pd.Series()).mean()

        c1,c2,c3,c4 = st.columns(4)

        c1.metric("Entrate", f"€{entrate:,.0f}")
        c2.metric("Costi", f"€{costi:,.0f}")
        c3.metric("Profitto", f"€{profitto:,.0f}")
        c4.metric("Margine Medio", f"{margine:.1f}%")

# ---------------- ANALISI ----------------

if menu == "Analisi":

    st.title("🔍 Analisi Avanzata")

    df = st.session_state.data

    if df is None:
        st.warning("Carica dati")
    else:

        col = st.selectbox("Raggruppa per:", df.columns)

        res = df.groupby(col)["Profitto"].sum().reset_index()

        st.dataframe(res)

# ---------------- GRAFICI ----------------

if menu == "Grafici":

    st.title("📊 Grafici")

    df = st.session_state.data

    if df is None:
        st.warning("Carica dati")
    else:

        x = st.selectbox("Asse X", df.columns)
        y = st.selectbox("Asse Y", df.columns)

        tipo = st.selectbox(
            "Tipo",
            ["Linea","Barre","Torta"]
        )

        if tipo == "Linea":
            fig = px.line(df, x=x, y=y)

        elif tipo == "Barre":
            fig = px.bar(df, x=x, y=y)

        else:
            fig = px.pie(df, names=x, values=y)

        st.plotly_chart(fig, use_container_width=True)

# ---------------- MAGAZZINO ----------------

if menu == "Magazzino":

    st.title("📦 Magazzino")

    df = st.session_state.data

    if df is None:
        st.warning("Carica dati")
    else:

        if "Stato" in df.columns:

            stock = df[df["Stato"]=="Stock"]
            sold = df[df["Stato"]=="Venduto"]

            st.metric("In Stock", len(stock))
            st.metric("Venduti", len(sold))

            st.dataframe(stock)

        else:
            st.info("Colonna 'Stato' non trovata")

# ---------------- PREVISIONI ----------------

if menu == "Previsioni":

    st.title("🔮 Previsioni")

    df = st.session_state.data

    if df is None:
        st.warning("Carica dati")
    else:

        if "Data" in df.columns and "Profitto" in df.columns:

            df["Data"] = pd.to_datetime(df["Data"])

            df["Mese"] = df["Data"].dt.to_period("M").astype(str)

            m = df.groupby("Mese")["Profitto"].sum().reset_index()

            X = np.arange(len(m)).reshape(-1,1)
            y = m["Profitto"]

            model = LinearRegression()
            model.fit(X,y)

            future = model.predict([[len(m)+1]])

            st.metric("Prossimo mese stimato", f"€{future[0]:,.0f}")

            fig = px.line(m, x="Mese", y="Profitto")
            st.plotly_chart(fig)

        else:
            st.info("Servono Data + Profitto")

# ---------------- BACKUP ----------------

if menu == "Backup":

    st.title("💾 Backup")

    df = st.session_state.data

    if df is None:
        st.warning("Nessun dato")
    else:

        json_data = df.to_json()

        st.download_button(
            "Scarica Backup",
            json_data,
            "backup.json"
        )

# ---------------- AI ----------------

if menu == "AI":

    st.title("🤖 Consulente AI")

    df = st.session_state.data

    if df is None:
        st.warning("Carica dati")
    else:

        domanda = st.text_input("Chiedi qualcosa:")

        if domanda:

            top = df.groupby(df.columns[0])["Profitto"].sum().sort_values(ascending=False).head(3)

            st.write("📌 Migliori performance:")
            st.write(top)

            st.success("Consiglio: investi sui primi risultati")
