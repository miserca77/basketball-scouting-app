
import streamlit as st

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Basketball Similarity App",
    page_icon="🏀",
    layout="wide"
)

# =========================================================
# 🔐 LOGIN
# =========================================================

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:

    st.title("🔐 Acceso a la app")

    password = st.text_input("Introduce la contraseña", type="password")

    if st.button("Entrar"):

        if password == "Master_SBL":

            # 👉 AQUÍ ESTÁ LO IMPORTANTE
            st.session_state.auth = True

            st.rerun()

        else:
            st.error("Contraseña incorrecta")

    st.stop()

# =========================================================
# CSS STYLE
# =========================================================

st.markdown("""
<style>

.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #1E3A8A;
    text-align: center;
}

.subtitle {
    font-size: 18px;
    color: #334155;
    text-align: center;
    margin-bottom: 30px;
}

.card {
    background-color: #F1F5F9;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 15px;
    border: 1px solid #E2E8F0;
}

.card-title {
    font-size: 18px;
    font-weight: 700;
    color: #0F172A;
}

.card-text {
    font-size: 14px;
    color: #475569;
}

.footer {
    text-align: center;
    margin-top: 50px;
    font-size: 14px;
    color: #64748B;
    padding: 20px;
    border-top: 1px solid #E2E8F0;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

st.markdown('<div class="main-title">🏀 Player Scouting & Performance Analytics</div>', unsafe_allow_html=True)

st.markdown('<div class="subtitle">Scouting Platform | Player Similarity | Analytics Dashboard</div>', unsafe_allow_html=True)

# =========================================================
# FEATURES
# =========================================================

st.markdown("## 🚀 Funcionalidades principales")

st.markdown("""
<div class="card">
    <div class="card-title">🔎 Buscar jugadores similares</div>
    <div class="card-text">
        Compara un jugador con otros jugadores reales usando métricas avanzadas y distancia euclídea.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
    <div class="card-title">🎯 Buscar perfiles manuales</div>
    <div class="card-text">
        Introduce métricas manualmente y encuentra jugadores con perfiles similares en la liga.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
    <div class="card-title">🧬 Player Cards (Scouting Dashboard)</div>
    <div class="card-text">
        Visualiza KPIs, percentiles, radar charts, comparables y archetypes NBA en un solo dashboard.
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# FEATURES EXTRA
# =========================================================

st.markdown("## 📊 Qué incluye esta app")

st.markdown("""
- 📈 Filtros por League, Position, Age, Minutes
- 📊 Percentiles sublevel y league
- 🕸️ Radar charts tipo scouting NBA
- 👥 Comparables por similitud
- 🧠 Archetypes automáticos
- 📥 Exportación CSV
""")

# =========================================================
# FOOTER (PORTFOLIO STYLE)
# =========================================================

st.markdown("""
<div class="footer">
    Created by <b>Miguel Serna Cabezas</b><br>
    Data Analyst | Sports Analytics & Basketball Scouting
</div>
""", unsafe_allow_html=True)
