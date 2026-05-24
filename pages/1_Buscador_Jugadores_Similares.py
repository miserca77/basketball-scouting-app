
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import euclidean_distances


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Find similar players",
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

    df = pd.read_excel("df_players_sublevel.xlsx")

    return df


df_players = load_data()


# =========================================================
# TITLE
# =========================================================

st.title("🏀 Find similar players")


# =========================================================
# FILTROS BASE
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

posiciones = st.multiselect(
    "Position",
    sorted(df_filtered["Position"].dropna().unique())
)

if posiciones:

    df_filtered = df_filtered[
        df_filtered["Position"].isin(posiciones)
    ]


# =========================================================
# AÑO
# =========================================================

if "año_ref" in df_filtered.columns:

    usar_anio = st.checkbox("Filtrar por año")

    if usar_anio:

        anio = st.selectbox(
            "Selecciona año",
            sorted(df_filtered["año_ref"].dropna().unique())
        )

        df_filtered = df_filtered[
            df_filtered["año_ref"] == anio
        ]


# =========================================================
# GP / MPG
# =========================================================

st.subheader("📈 Filtro de rendimiento")

min_gp = st.number_input(
    "Mínimo partidos jugados (GP)",
    min_value=0,
    value=0
)

min_mpg = st.number_input(
    "Mínimo minutos por partido (MPG)",
    min_value=0.0,
    value=0.0
)

if min_gp > 0:

    df_filtered = df_filtered[
        df_filtered["GP"] >= min_gp
    ]

if min_mpg > 0:

    df_filtered = df_filtered[
        df_filtered["MPG"] >= min_mpg
    ]


st.write("Shape final:", df_filtered.shape)


# =========================================================
# CONTROL ERRORES
# =========================================================

if df_filtered.shape[0] == 0:

    st.warning("No hay jugadores con esos filtros")

    st.stop()


# =========================================================
# SELECCIÓN JUGADOR
# =========================================================

player_id = st.selectbox(
    "Selecciona jugador (Player_League_ID)",
    sorted(df_filtered["Player_League_ID"].unique())
)


# =========================================================
# FEATURES
# =========================================================

num_cols = df_filtered.select_dtypes(include=np.number).columns.tolist()

features = st.multiselect(
    "Selecciona métricas para calcular similitud",
    num_cols,
    default=num_cols
)

num_similares = st.slider(
    "Número de jugadores similares",
    1,
    30,
    10
)


# =========================================================
# BOTÓN PRINCIPAL
# =========================================================

if st.button("🔎 Buscar similares"):

    try:

        if len(features) == 0:

            st.error("Selecciona al menos una métrica")

            st.stop()

        df_model = df_filtered.copy()

        X = df_model[features].values

        y = df_model["Player_League_ID"].values


        # =====================================================
        # STANDARD SCALER
        # =====================================================

        scaler = StandardScaler()

        X_std = scaler.fit_transform(X)


        # =====================================================
        # VARIANCE FILTER
        # =====================================================

        vt = VarianceThreshold(0.01)

        X_vf = vt.fit_transform(X_std)

        columnas_finales = [

            features[i]
            for i in vt.get_support(indices=True)

        ]

        if len(columnas_finales) == 0:

            st.error("No quedan variables tras VarianceThreshold")

            st.stop()


        # =====================================================
        # DISTANCIA EUCLÍDEA
        # =====================================================

        if len(columnas_finales) <= 5:

            dist_matrix = euclidean_distances(X_vf)

            idx = np.where(y == player_id)[0][0]

            distancias = dist_matrix[idx]

            indices_ordenados = np.argsort(
                distancias
            )[1:num_similares+1]

            jugadores_similares = y[
                indices_ordenados
            ]

            factores = distancias[
                indices_ordenados
            ]

            df_result = pd.DataFrame({

                "Jugador similar": jugadores_similares,

                "Distancia euclídea": factores

            })


        # =====================================================
        # PCA + CORRELACIÓN
        # =====================================================

        else:

            pca = PCA(
                n_components=min(
                    X_vf.shape[1]-1,
                    X_vf.shape[1]
                )
            )

            X_pca = pca.fit_transform(X_vf)

            explained = np.cumsum(
                pca.explained_variance_ratio_
            )

            n_comp = np.searchsorted(
                explained,
                0.95
            ) + 1

            st.write(
                f"📊 Componentes PCA usados: {n_comp}"
            )

            df_pca = pd.DataFrame(

                X_pca[:, :n_comp],

                index=y

            )

            corr = df_pca.T.corr()

            similares = (

                corr[player_id]
                .drop(player_id)
                .sort_values(ascending=False)
                .head(num_similares)

            )

            df_result = pd.DataFrame({

                "Jugador similar": similares.index,

                "Factor correlación": similares.values

            })


        # =====================================================
        # DATA FINAL
        # =====================================================

        base = df_model[
            df_model["Player_League_ID"] == player_id
        ]

        similars_df = df_model[
            df_model["Player_League_ID"]
            .isin(df_result["Jugador similar"])
        ]

        final_df = pd.concat(
            [base, similars_df],
            ignore_index=True
        )


        # =====================================================
        # TABLA MÉTRICAS
        # =====================================================

        columnas_mostrar = [

            "Player",

            "Player_League_ID"

        ]

        if "Position" in final_df.columns:

            columnas_mostrar.append("Position")

        if "League" in final_df.columns:

            columnas_mostrar.append("League")

        columnas_mostrar += [

            col
            for col in columnas_finales
            if col in final_df.columns

        ]

        resultado_metricas = final_df[
            columnas_mostrar
        ]


        # =====================================================
        # GUARDAR EN SESSION STATE
        # =====================================================

        st.session_state["df_result"] = df_result

        st.session_state["resultado_metricas"] = resultado_metricas

        st.session_state["final_df"] = final_df

        st.session_state["columnas_finales"] = columnas_finales


    except Exception as e:

        st.error(f"Error: {e}")


# =========================================================
# MOSTRAR RESULTADOS
# =========================================================

if "df_result" in st.session_state:

    df_result = st.session_state["df_result"]

    resultado_metricas = st.session_state[
        "resultado_metricas"
    ]

    final_df = st.session_state["final_df"]

    columnas_finales = st.session_state[
        "columnas_finales"
    ]


    st.subheader("🔎 Jugadores similares")

    st.dataframe(
        df_result.reset_index(drop=True),
        use_container_width=True
    )


    st.subheader(
        "📋 Datos con métricas seleccionadas"
    )

    st.dataframe(
        resultado_metricas.reset_index(drop=True),
        use_container_width=True
    )


    st.subheader("📊 Datos completos")

    st.dataframe(
        final_df.reset_index(drop=True),
        use_container_width=True
    )


    # =====================================================
    # DESCARGA COMPLETA
    # =====================================================

    csv_full = final_df.to_csv(
        index=False,
        sep=";",
        decimal=","
    ).encode("utf-8")

    st.download_button(

        label="⬇️ Descargar datos completos",

        data=csv_full,

        file_name="jugadores_similares_completo.csv",

        mime="text/csv"

    )


    # =====================================================
    # FORMATO LARGO
    # =====================================================

    columnas_largas = [

        "Player_League_ID"

    ] + columnas_finales

    df_largo = final_df[
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

        file_name="jugadores_similares_long.csv",

        mime="text/csv"

    )


    # =====================================================
    # NORMALIZADO RADAR
    # =====================================================

    scaler_norm = MinMaxScaler()

    df_norm = final_df[
        ["Player_League_ID"] + columnas_finales
    ].copy()

    df_norm[columnas_finales] = scaler_norm.fit_transform(
        df_norm[columnas_finales]
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

        file_name="jugadores_similares_radar.csv",

        mime="text/csv"

    )

