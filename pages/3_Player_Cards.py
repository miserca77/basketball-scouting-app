import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import euclidean_distances

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Player Cards",
    layout="wide"
)

st.title("🏀 Player Cards - Scouting Dashboard")

# 🔐 LOGIN 
if not st.session_state.get("auth", False):
    st.warning("🔐 Debes iniciar sesión")
    st.stop()

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():
    df = pd.read_excel("df_players_sublevel.xlsx", engine="openpyxl")
    return df

df_players = load_data()

# =========================================================
# FIX PLAYER IDs
# =========================================================

df_players["Player_League_ID"] = (
    df_players["Player_League_ID"]
    .astype(str)
    .str.strip()
)

# =========================================================
# LIMPIAR COLUMNAS DE PERCENTILES
# =========================================================

pct_cols = [

    c for c in df_players.columns

    if (
        c.endswith("_pct_league")
        or c.endswith("_pct_sublevel")
    )
]

for col in pct_cols:

    # convertir a numérico
    df_players[col] = pd.to_numeric(
        df_players[col],
        errors="coerce"
    )

    # NaN -> 0
    df_players[col] = df_players[col].fillna(0)


# =========================================================
# CLEAN NUMERIC COLUMNS ONLY
# =========================================================

for col in df_players.columns:

    if df_players[col].dtype != "object":

        df_players[col] = pd.to_numeric(
            df_players[col],
            errors="coerce"
        )
        
# =========================================================
# SELECT PLAYER
# =========================================================

player_id = st.selectbox(
    "Selecciona jugador",
    sorted(df_players["Player_League_ID"].dropna().unique())
)

# =========================================================
# SAFE LOOKUP (EVITA ERROR .iloc[0])
# =========================================================

player_df = df_players.loc[
    df_players["Player_League_ID"].astype(str).str.strip()
    == str(player_id).strip()
]

if player_df.empty:
    st.error("Jugador no encontrado en el dataset actual")
    st.stop()

player = player_df.iloc[0]

# =========================================================
# PCT COLUMNS
# =========================================================

pct_sub_cols = [c for c in df_players.columns if c.endswith("_pct_sublevel")]
pct_league_cols = [c for c in df_players.columns if c.endswith("_pct_league")]

# =========================================================
# TOP 5 SAFE FUNCTION
# =========================================================

def top5(df, cols, player_id):
    values = []

    for c in cols:
        if c in df.columns:
            val = df.loc[df["Player_League_ID"] == player_id, c]
            if len(val) > 0:
                try:
                    v = float(val.values[0])
                    if not np.isnan(v):
                        values.append((c, v))
                except:
                    pass

    return sorted(values, key=lambda x: x[1], reverse=True)[:5]

# =========================================================
# LAYOUT
# =========================================================

col1, col2 = st.columns([1, 3])

with col1:

    st.subheader("📋 Info")

    import re
    from datetime import datetime
    
    def clean_value(v):
        if pd.isna(v):
            return None
        v = str(v).strip()
        if v.lower() in ["", "no_data", "none", "nan"]:
            return None
        return v
    
    
    def find_col(possible_names):
        for c in possible_names:
            if c in df_players.columns:
                return c
        return None
    
    
    def extract_number(v):
        if pd.isna(v):
            return None
        try:
            num = re.findall(r"[\d.]+", str(v))
            return float(num[0]) if num else None
        except:
            return None
    
    
    mapping = {
        "Player": ["Player"],
        "Position": ["Position"],
        "League": ["League"],
        "Team": ["Team_Name"],
        "Age": ["Age"],
        "Height (cm)": ["HT"],
        "Weight (kg)": ["WT"],
        "GP": ["GP"],
        "MPG": ["MPG"],
        "Nationality": ["Nationality"],
        "Birth Year": ["Birth Date"]
    }
    
    
    for label, cols in mapping.items():
    
        col = find_col(cols)
        if col is None:
            continue
    
        value = player.get(col, None)
        value = clean_value(value)
    
        if value is None:
            continue
    
        if label in ["Height (cm)", "Weight (kg)"]:
            value = value
    
        if label == "Age":
            birth_col = find_col(["BirthYear", "DOB", "DateOfBirth", "Birthdate"])
            if birth_col:
                try:
                    birth_val = player.get(birth_col)
                    birth_year = int(str(birth_val)[:4])
                    value = datetime.now().year - birth_year
                except:
                    pass
    
        st.write(f"**{label}:** {value}")
        
with col2:

    st.subheader("📊 KPIs - Top Percentiles")

    # ===================== SUBLEVEL =====================
    st.markdown("### 🟢 Sublevel")
    top_sub = top5(df_players, pct_sub_cols, player_id)

    if len(top_sub) > 0:
        cols = st.columns(min(5, len(top_sub)))
        for i, (name, val) in enumerate(top_sub):
            cols[i].metric(
                label=name.replace("_pct_sublevel", ""),
                value=f"{val:.0f}%"
            )

    # ===================== LEAGUE =====================
    st.markdown("### 🌍 League")
    top_league = top5(df_players, pct_league_cols, player_id)

    if len(top_league) > 0:
        cols = st.columns(min(5, len(top_league)))
        for i, (name, val) in enumerate(top_league):
            cols[i].metric(
                label=name.replace("_pct_league", ""),
                value=f"{val:.0f}%"
            )

# =========================================================
# RADAR COMPARISON
# =========================================================

st.subheader("🕸️ Radar Comparison")

num_cols = df_players.select_dtypes(include=np.number).columns.tolist()

radar_metrics = st.multiselect(
    "Selecciona métricas para el radar",
    num_cols,
    default=num_cols[:4] if len(num_cols) >= 4 else num_cols
)

radar_metrics = [m for m in radar_metrics if m in df_players.columns]

# =========================================================
# SELECT COMPARABLE PLAYERS
# =========================================================

compare_players = st.multiselect(
    "Selecciona hasta 5 jugadores para comparar",
    options=[
        p for p in sorted(df_players["Player_League_ID"].unique())
        if p != player_id
    ],
    max_selections=5
)

# =========================================================
# RADAR
# =========================================================

if len(radar_metrics) >= 3:

    fig = go.Figure()

    # =====================================================
    # MAIN PLAYER
    # =====================================================

    main_values = []

    for m in radar_metrics:
        try:
            main_values.append(float(player[m]))
        except:
            main_values.append(0)

    main_values += main_values[:1]

    fig.add_trace(go.Scatterpolar(
        r=main_values,
        theta=radar_metrics + [radar_metrics[0]],
        fill='toself',
        name=player["Player"]
    ))

    # =====================================================
    # COMPARED PLAYERS
    # =====================================================

    for pid in compare_players:

        p = df_players[
            df_players["Player_League_ID"] == pid
        ].iloc[0]

        vals = []

        for m in radar_metrics:
            try:
                vals.append(float(p[m]))
            except:
                vals.append(0)

        vals += vals[:1]

        fig.add_trace(go.Scatterpolar(
            r=vals,
            theta=radar_metrics + [radar_metrics[0]],
            fill='toself',
            name=p["Player"]
        ))

    # =====================================================
    # LAYOUT
    # =====================================================

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True
            )
        ),
        showlegend=True,
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)

    
# =========================================================
# PLAYER EVOLUTION (FINAL UX CONTROL TOTAL)
# =========================================================

st.subheader("📈 Player Evolution")

evolution_metric = st.selectbox(
    "Selecciona métrica evolución",
    num_cols
)

# =====================================================
# SELECT PLAYERS (BASE)
# =====================================================

base_players = sorted(df_players["Player"].dropna().unique())

selected_base_players = st.multiselect(
    "Selecciona jugadores",
    base_players,
    default=[player["Player"]]
)

# =====================================================
# SELECT ROWS PER PLAYER (IMPORTANT PART)
# =====================================================

selected_data = {}

for bp in selected_base_players:

    st.markdown(f"### 👤 {bp}")

    df_subset = df_players[
        df_players["Player_League_ID"]
        .astype(str)
        .str.startswith(bp)
    ].copy()

    if df_subset.empty:
        continue

    options = df_subset["Player_League_ID"].tolist()

    selected_ids = st.multiselect(
        f"Selecciona temporadas / ligas / competiciones ({bp})",
        options=options,
        default=options,
        key=f"ev_{bp}"
    )

    selected_data[bp] = selected_ids

# =====================================================
# PLOT
# =====================================================

fig_line = go.Figure()

for bp, ids in selected_data.items():

    if len(ids) == 0:
        continue

    df_hist = df_players[
        df_players["Player_League_ID"].isin(ids)
    ].copy()

    if df_hist.empty:
        continue

    # SAFE NUMERIC
    df_hist["año_ref"] = pd.to_numeric(df_hist["año_ref"], errors="coerce")
    df_hist[evolution_metric] = pd.to_numeric(df_hist[evolution_metric], errors="coerce")

    df_hist = df_hist.dropna(subset=["año_ref", evolution_metric])

    # IMPORTANT: ORDER BY YEAR ONLY
    df_hist = df_hist.sort_values("año_ref")

    player_name = df_hist["Player"].iloc[0] if "Player" in df_hist.columns else bp

    fig_line.add_trace(go.Scatter(
        x=df_hist["año_ref"],
        y=df_hist[evolution_metric],
        mode="lines+markers",
        name=player_name,
        text=df_hist["Player_League_ID"],
        hovertemplate="<b>%{text}</b><br>Año: %{x}<br>Valor: %{y}<extra></extra>"
    ))

fig_line.update_layout(
    xaxis=dict(
        title="Año",
        tickmode="linear",
        dtick=1
    ),
    yaxis_title=evolution_metric,
    height=700,
    hovermode="x unified"
)

st.plotly_chart(fig_line, use_container_width=True)
# =========================================================
# SCOUTING REPORT SAFE (FIXED)
# =========================================================

st.subheader("📄 Scouting Report")

strengths = []
weaknesses = []

for col in pct_league_cols:

    if col in df_players.columns:

        # 🔥 limpiar columna (evita strings tipo 'no_data')
        clean_col = pd.to_numeric(df_players[col], errors="coerce")

        # si toda la columna es NaN, saltar
        if clean_col.notna().sum() == 0:
            continue

        # calcular percentiles correctamente
        pct = clean_col.rank(pct=True)

        val = pct[df_players["Player_League_ID"] == player_id].values

        if len(val) == 0 or np.isnan(val[0]):
            continue

        v = float(val[0])

        # reglas scouting
        if v >= 0.75:
            strengths.append(col.replace("_pct_league", ""))
        elif v <= 0.35:
            weaknesses.append(col.replace("_pct_league", ""))

# =========================================================
# OUTPUT
# =========================================================

st.markdown("### 🟢 Strengths")

if strengths:
    for s in strengths:
        st.write(f"- Elite {s}")
else:
    st.write("No standout strengths detected")

st.markdown("### 🔴 Weaknesses")

if weaknesses:
    for w in weaknesses:
        st.write(f"- Low {w}")
else:
    st.write("No major weaknesses detected")

# =========================================================
# PERFIL JUGADORES
# =========================================================

# =========================================================
# ARCHETYPE SCORING ENGINE
# =========================================================

st.subheader("🧬 Archetypes")

# =========================================================
# HELPER
# =========================================================

def get_pct(col):

    if col in df_players.columns:

        val = pd.to_numeric(
            player[col],
            errors="coerce"
        )

        if pd.notna(val):
            return float(val)

    return 0


# =========================================================
# EXTRAER PERCENTILES
# =========================================================

usg = get_pct("USG%_pct_league")
ast = get_pct("AST%_pct_league")
stl = get_pct("STL%_pct_league")
blk = get_pct("BLK%_pct_league")
efg = get_pct("eFG%_pct_league")
ts  = get_pct("TS%_pct_league")
orb = get_pct("ORB%_pct_league")
drb = get_pct("DRB%_pct_league")
tov = get_pct("TOV%_pct_league")
ortg = get_pct("ORtg_pct_league")
per = get_pct("PER_pct_league")


# =========================================================
# ARCHETYPE SCORES
# =========================================================

archetype_scores = {

    # =====================================================
    # OFFENSIVE CREATORS
    # =====================================================

    "🎯 Shot Creator":
        (
            0.40 * usg +
            0.30 * ast +
            0.30 * ts
        ),

    "🧠 Floor General":
        (
            0.60 * ast +
            0.25 * ortg +
            0.15 * (100 - tov)
        ),

    "🏀 Combo Guard":
        (
            0.45 * ast +
            0.45 * usg +
            0.10 * ts
        ),

    "🎮 Secondary Playmaker":
        (
            0.50 * ast +
            0.30 * ts +
            0.20 * usg
        ),

    # =====================================================
    # SCORERS
    # =====================================================

    "⚡ Slasher":
        (
            0.45 * usg +
            0.35 * ts +
            0.20 * per
        ),

    "🎯 Movement Shooter":
        (
            0.55 * efg +
            0.25 * ts +
            0.20 * usg
        ),

    "💥 Interior Finisher":
        (
            0.50 * orb +
            0.30 * ts +
            0.20 * per
        ),

    # =====================================================
    # DEFENSIVE
    # =====================================================

    "🛡️ 3&D Wing":
        (
            0.40 * stl +
            0.40 * efg +
            0.20 * drb
        ),

    "🚫 Rim Protector":
        (
            0.65 * blk +
            0.35 * drb
        ),

    "🛡️ Defensive Anchor":
        (
            0.50 * blk +
            0.30 * drb +
            0.20 * stl
        ),

    # =====================================================
    # BIGS / HYBRIDS
    # =====================================================

    "🗼 Stretch Big":
        (
            0.45 * efg +
            0.30 * blk +
            0.25 * drb
        ),

    "🧬 Point Forward":
        (
            0.45 * ast +
            0.35 * drb +
            0.20 * usg
        )
}


# =========================================================
# CONVERTIR A DATAFRAME
# =========================================================

df_arch = pd.DataFrame({

    "Archetype": archetype_scores.keys(),
    "Score": archetype_scores.values()

})


# =========================================================
# ORDENAR
# =========================================================

df_arch = df_arch.sort_values(
    by="Score",
    ascending=False
).reset_index(drop=True)


# =========================================================
# TOP 3
# =========================================================

primary = df_arch.iloc[0]
secondary = df_arch.iloc[1]
tertiary = df_arch.iloc[2]


# =========================================================
# MOSTRAR TOP ARCHETYPES (SMALL VERSION)
# =========================================================

st.markdown("""
<style>
.small-metric {
    padding: 8px;
    border-radius: 10px;
    background-color: #E0F2FE;
    text-align: center;
    margin-bottom: 10px;
}

.small-title {
    font-size: 14px;
    color: #020617;
    margin-bottom: 5px;
}

.small-archetype {
    font-size: 18px;
    font-weight: bold;
    line-height: 1.2;
}

.small-score {
    font-size: 13px;
    color: #0F766E;
}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:

    st.markdown(f"""
    <div class="small-metric">
        <div class="small-title">Primary</div>
        <div class="small-archetype">
            {primary["Archetype"]}
        </div>
        <div class="small-score">
            Score: {primary["Score"]:.1f}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:

    st.markdown(f"""
    <div class="small-metric">
        <div class="small-title">Secondary</div>
        <div class="small-archetype">
            {secondary["Archetype"]}
        </div>
        <div class="small-score">
            Score: {secondary["Score"]:.1f}
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# TABLA COMPLETA
# =========================================================

with st.expander("📊 View Full Archetype Scores"):

    st.dataframe(
        df_arch,
        use_container_width=True
    )
