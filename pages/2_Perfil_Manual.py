
import streamlit as st
import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics.pairwise import euclidean_distances


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Players with specific metrics",
    layout="wide"
)

# 🔐 LOGIN 
if not st.session_state.get("auth", False):
    st.warning("🔐 Debes iniciar sesión")
    st.stop()

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    url = "https://docs.google.com/spreadsheets/d/1BaMavjirF82EDqo0nQz1rpGC8O4fUsGh/export?format=xlsx"

    df = pd.read_excel(url, engine="openpyxl")
    
    return df


df_players = load_data()


# =========================================================
# TITLE
# =========================================================

st.title("🎯 Players with specific metrics")


# =========================================================
# FILTROS
# =========================================================

df_filtered = df_players.copy()


# =========================================================
# LEAGUE
# =========================================================

ligas = st.multiselect(
    "League",
    sorted(df_players["League"].dropna().unique())
)

if ligas:

    df_filtered = df_filtered[
        df_filtered["League"].isin(ligas)
    ]


# =========================================================
# SUBLEVEL
# =========================================================

if "Sublevel" in df_players.columns:

    sublevels = st.multiselect(
        "Sublevel",
        sorted(df_filtered["Sublevel"].dropna().unique())
    )

    if sublevels:

        df_filtered = df_filtered[
            df_filtered["Sublevel"].isin(sublevels)
        ]


# =========================================================
# POSITION
# =========================================================

if "Position" in df_filtered.columns:

    posiciones = st.multiselect(
        "Position",
        sorted(df_filtered["Position"].dropna().unique())
    )

    if posiciones:

        df_filtered = df_filtered[
            df_filtered["Position"].isin(posiciones)
        ]


# =========================================================
# CONTROL VACÍO
# =========================================================

if df_filtered.shape[0] == 0:

    st.warning("No hay jugadores con esos filtros")

    st.stop()


# =========================================================
# MÉTRICAS
# =========================================================

num_cols = df_filtered.select_dtypes(
    include=np.number
).columns.tolist()

metricas = st.multiselect(
    "Selecciona métricas",
    num_cols,
    default=num_cols[:5]
)


# =========================================================
# NÚMERO SIMILARES
# =========================================================

num_similares = st.slider(
    "Número de jugadores similares",
    1,
    30,
    10
)


# =========================================================
# INPUTS MANUALES
# =========================================================

st.subheader("✍️ Introduce valores manuales")

perfil_manual = {}

for m in metricas:

    media = float(df_filtered[m].mean())

    minimo = float(df_filtered[m].min())

    maximo = float(df_filtered[m].max())

    perfil_manual[m] = st.number_input(

        label=m,

        value=round(media, 2),

        min_value=minimo,

        max_value=maximo

    )


# =========================================================
# BOTÓN
# =========================================================

if st.button("🔎 Buscar jugadores similares"):

    try:

        if len(metricas) == 0:

            st.error("Selecciona al menos una métrica")

            st.stop()


        # =====================================================
        # MATRIZ
        # =====================================================

        X = df_filtered[metricas].values

        scaler = StandardScaler()

        X_std = scaler.fit_transform(X)


        # =====================================================
        # PERFIL MANUAL
        # =====================================================

        perfil_vector = np.array([

            perfil_manual[m]
            for m in metricas

        ]).reshape(1, -1)

        perfil_std = scaler.transform(
            perfil_vector
        )


        # =====================================================
        # DISTANCIAS
        # =====================================================

        distancias = euclidean_distances(

            perfil_std,
            X_std

        )[0]

        df_resultado = df_filtered.copy()

        df_resultado["Distancia"] = distancias

        resultado = df_resultado.sort_values(
            by="Distancia"
        ).head(num_similares)


        # =====================================================
        # TABLA MÉTRICAS
        # =====================================================

        columnas_mostrar = [

            "Player",
            "Player_League_ID"

        ]

        if "Position" in resultado.columns:

            columnas_mostrar.append("Position")

        if "League" in resultado.columns:

            columnas_mostrar.append("League")

        columnas_mostrar += metricas

        columnas_mostrar.append("Distancia")

        resultado_metricas = resultado[
            columnas_mostrar
        ]


        # =====================================================
        # SESSION STATE
        # =====================================================

        st.session_state["resultado_manual"] = resultado

        st.session_state[
            "resultado_metricas_manual"
        ] = resultado_metricas

        st.session_state[
            "metricas_manual"
        ] = metricas


    except Exception as e:

        st.error(f"Error: {e}")


# =========================================================
# MOSTRAR RESULTADOS
# =========================================================

if "resultado_manual" in st.session_state:

    resultado = st.session_state[
        "resultado_manual"
    ]

    resultado_metricas = st.session_state[
        "resultado_metricas_manual"
    ]

    metricas = st.session_state[
        "metricas_manual"
    ]


    # =====================================================
    # TABLA MÉTRICAS
    # =====================================================

    st.subheader(
        "📋 Jugadores más parecidos al perfil"
    )

    st.dataframe(

        resultado_metricas.reset_index(drop=True),

        use_container_width=True

    )


    # =====================================================
    # TABLA COMPLETA
    # =====================================================

    st.subheader("📊 Datos completos")

    st.dataframe(

        resultado.reset_index(drop=True),

        use_container_width=True

    )


    # =====================================================
    # DESCARGA COMPLETA
    # =====================================================

    csv_full = resultado.to_csv(

        index=False,
        sep=";",
        decimal=","

    ).encode("utf-8")

    st.download_button(

        label="⬇️ Descargar datos completos",

        data=csv_full,

        file_name="perfil_manual_completo.csv",

        mime="text/csv"

    )


    # =====================================================
    # FORMATO LARGO
    # =====================================================

    columnas_largas = [

        "Player_League_ID"

    ] + metricas

    df_largo = resultado[
        columnas_largas
    ].melt(

        id_vars=["Player_League_ID"],

        var_name="Metrica",

        value_name="Valor"

    )

    csv_largo = df_largo.to_csv(

        index=False,
        sep=";",
        decimal=","

    ).encode("utf-8")

    st.download_button(

        label="⬇️ Descargar formato largo",

        data=csv_largo,

        file_name="perfil_manual_long.csv",

        mime="text/csv"

    )


    # =====================================================
    # NORMALIZADO RADAR
    # =====================================================

    scaler_norm = MinMaxScaler()

    df_norm = resultado[
        ["Player_League_ID"] + metricas
    ].copy()

    df_norm[metricas] = scaler_norm.fit_transform(
        df_norm[metricas]
    )

    df_norm_largo = df_norm.melt(

        id_vars=["Player_League_ID"],

        var_name="Metrica",

        value_name="Valor"

    )

    csv_norm = df_norm_largo.to_csv(

        index=False,
        sep=";",
        decimal=","

    ).encode("utf-8")

    st.download_button(

        label="📊 Descargar datos normalizados radar",

        data=csv_norm,

        file_name="perfil_manual_radar.csv",

        mime="text/csv"

    )

