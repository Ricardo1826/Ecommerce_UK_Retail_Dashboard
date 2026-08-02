import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Ecommerce UK Retail Dashboard",
    layout="wide",
    page_icon="🛒"
)

st.markdown("""
<style>
    .stApp {
        background-color: #f7f9fc;
    }
    .kpi-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #2E4057;
    }
    .kpi-label {
        font-size: 14px;
        color: #6c757d;
        margin-top: 4px;
    }
    h1, h2, h3, h4, p, span, label, .stMarkdown, .stCaption {
    color: #2E4057 !important;
}
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
    }
    .header-fixe {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999999;
    background-color: #f7f9fc;
    padding: 12px 40px 8px 40px;
    border-bottom: 1px solid #e0e0e0;
}
    .header-fixe h1 {
        margin-bottom: 0;
        font-size: 28px;
    }
    .header-fixe p {
        margin-top: 4px;
        color: #6c757d;
    }
    /* Pousse le contenu vers le bas pour qu'il ne soit pas caché sous le header fixe */
    .block-container {
        padding-top: 110px !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-fixe">
    <h1>🛒 Ecommerce UK Retail Dashboard</h1>
    <p>Exploration interactive des ventes e-commerce (Online Retail, 2010-2011)</p>
</div>
""", unsafe_allow_html=True)
@st.cache_data
def charger_donnees():
    df = pd.read_csv("../data/processed/OnlineRetail_clean.csv")
    df['TotalPrice'] = df['Quantity'] * df['UnitPrice']
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    return df

with st.spinner("Chargement des données..."):
    df = charger_donnees()

with st.expander("🔎 Filtres", expanded=False):
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        pays_disponibles = sorted(df["Country"].unique())
        tout_selectionner = st.checkbox("Tout sélectionner (pays)", value=True)
        if tout_selectionner:
            pays_selectionnes = st.multiselect(
                "Pays", options=pays_disponibles, default=pays_disponibles
            )
        else:
            pays_selectionnes = st.multiselect("Pays", options=pays_disponibles)

    with col_f2:
        date_min = df["InvoiceDate"].min().date()
        date_max = df["InvoiceDate"].max().date()
        plage_dates = st.date_input(
            "Période", value=(date_min, date_max), min_value=date_min, max_value=date_max
        )

    with col_f3:
        recherche_produit = st.text_input("Rechercher un produit (optionnel)")

# --- Application des filtres ---
df_filtre = df[df["Country"].isin(pays_selectionnes)]

if len(plage_dates) == 2:
    date_debut, date_fin = plage_dates
    df_filtre = df_filtre[
        (df_filtre["InvoiceDate"].dt.date >= date_debut) &
        (df_filtre["InvoiceDate"].dt.date <= date_fin)
    ]

if recherche_produit:
    df_filtre = df_filtre[
        df_filtre["Description"].str.contains(recherche_produit, case=False, na=False)
    ]
# --- Gestion du cas vide : on arrête proprement ici si rien à afficher ---
if df_filtre.empty:
    st.warning("⚠️ Aucune transaction ne correspond aux filtres sélectionnés. Essaie d'élargir tes critères (pays, période ou recherche produit).")
    st.stop()

st.caption(f"**{len(df_filtre):,}** lignes de vente (articles) correspondent aux filtres sélectionnés - soit **{df_filtre['InvoiceNo'].nunique():,}** commandes distinctes")
ca_total = df_filtre["TotalPrice"].sum()
nb_transactions = df_filtre["InvoiceNo"].nunique()
panier_moyen = ca_total / nb_transactions if nb_transactions > 0 else 0
nb_clients = df_filtre["CustomerID"].nunique()

col1, col2, col3, col4 = st.columns(4)

kpis = [
    (col1, f"{ca_total:,.0f} £", "Chiffre d'affaires"),
    (col2, f"{nb_transactions:,}", "Transactions distinctes"),
    (col3, f"{panier_moyen:,.2f} £", "Panier moyen"),
    (col4, f"{nb_clients:,}", "Clients uniques"),
]

for col, valeur, label in kpis:
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{valeur}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.subheader("📈 Analyse détaillée")

onglet1, onglet2, onglet3, onglet4 = st.tabs(["📅 Évolution temporelle", "🏆 Top produits", "🌍 Répartition par pays", "👥 Clients"])

with onglet1:
    df_filtre["YearMonth"] = df_filtre["InvoiceDate"].dt.to_period("M").astype(str)
    evolution = df_filtre.groupby("YearMonth")["TotalPrice"].sum().reset_index()

    fig = px.line(
        evolution, x="YearMonth", y="TotalPrice",
        markers=True,
        title="Évolution du chiffre d'affaires par mois",
        labels={"YearMonth": "Mois", "TotalPrice": "Chiffre d'affaires (£)"}
    )
    fig.update_traces(line_color="#2E86AB", line_width=3)
    fig.update_layout(
    template="plotly_white",
    font=dict(color="#2E4057"),
    plot_bgcolor="white",
    paper_bgcolor="white"
)
    st.plotly_chart(fig, use_container_width=True, theme=None)

with onglet2:
    top_produits = (
        df_filtre.groupby("Description")["TotalPrice"].sum()
        .nlargest(10).sort_values().reset_index()
    )

    fig = px.bar(
        top_produits, x="TotalPrice", y="Description",
        orientation="h",
        title="Top 10 produits par chiffre d'affaires",
        labels={"TotalPrice": "Chiffre d'affaires (£)", "Description": ""},
        color="TotalPrice", color_continuous_scale="Greens"
    )
    fig.update_layout(
    template="plotly_white",
    font=dict(color="#2E4057"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    showlegend=False
)
    st.plotly_chart(fig, use_container_width=True, theme=None)

with onglet3:
    top_pays = (
        df_filtre.groupby("Country")["TotalPrice"].sum()
        .nlargest(10).sort_values().reset_index()
    )

    fig = px.bar(
        top_pays, x="TotalPrice", y="Country",
        orientation="h",
        title="Top 10 pays par chiffre d'affaires",
        labels={"TotalPrice": "Chiffre d'affaires (£)", "Country": ""},
        color="TotalPrice", color_continuous_scale="Oranges"
    )
    fig.update_layout(
    template="plotly_white",
    font=dict(color="#2E4057"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    showlegend=False
)
    st.plotly_chart(fig, use_container_width=True, theme=None)

with onglet4:
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        ca_par_pays = df_filtre.groupby("Country")["TotalPrice"].sum()
        ca_uk = ca_par_pays.get("United Kingdom", 0)
        ca_reste = ca_par_pays.sum() - ca_uk

        fig = px.pie(
            values=[ca_uk, ca_reste],
            names=["Royaume-Uni", "Reste du monde"],
            title="CA : UK vs reste du monde",
            color_discrete_sequence=["#2E86AB", "#C0C0C0"]
        )
        fig.update_layout(
            template="plotly_white",
            font=dict(color="#2E4057"),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        st.plotly_chart(fig, use_container_width=True, theme=None)

    with col_b:
        commandes_par_client = df_filtre.groupby("CustomerID")["InvoiceNo"].nunique()
        recurrents = (commandes_par_client > 1).sum()
        ponctuels = (commandes_par_client == 1).sum()

        fig = px.pie(
            values=[recurrents, ponctuels],
            names=["Récurrents (2+)", "Ponctuels (1)"],
            title="Fidélité client",
            color_discrete_sequence=["#5B8C5A", "#E8A87C"]
        )
        fig.update_layout(
            template="plotly_white",
            font=dict(color="#2E4057"),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        st.plotly_chart(fig, use_container_width=True, theme=None)

    with col_c:
        top_clients = df_filtre.groupby("CustomerID")["TotalPrice"].sum().nlargest(10).sort_values().reset_index()
        top_clients["CustomerID"] = top_clients["CustomerID"].astype(str)

        fig = px.bar(
            top_clients, x="TotalPrice", y="CustomerID",
            orientation="h",
            title="Top 10 clients (CA)",
            labels={"TotalPrice": "CA (£)", "CustomerID": "Client"},
            color="TotalPrice", color_continuous_scale="Purples"
        )
        fig.update_layout(
            template="plotly_white",
            font=dict(color="#2E4057"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, theme=None)

st.divider()

with st.expander("🔍 Voir les données détaillées"):
    st.dataframe(df_filtre, use_container_width=True, height=300)

csv_export = df_filtre.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Télécharger les données filtrées (CSV)",
    data=csv_export,
    file_name="ecommerce_filtre.csv",
    mime="text/csv"
)

st.divider()
st.caption("Dashboard réalisé par Richard GNALOU — Dataset Online Retail (UCI)")