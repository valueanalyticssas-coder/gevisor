import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd
import tempfile

st.set_page_config(
    page_title="Geovisor Colombia",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

    section[data-testid="stSidebar"] { background: #0f1923; border-right: 2px solid #1e3a5f; }
    section[data-testid="stSidebar"] * { color: #c9d8e8 !important; }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #5ba4cf !important;
        font-family: 'IBM Plex Mono', monospace !important;
        letter-spacing: 0.05em;
    }
    .geovisor-header {
        background: linear-gradient(135deg, #0f1923 0%, #1e3a5f 60%, #0d3349 100%);
        border-radius: 10px; padding: 18px 28px; margin-bottom: 16px;
        border-left: 5px solid #f5a623;
    }
    .geovisor-header h1 {
        color: #ffffff !important; font-family: 'IBM Plex Mono', monospace;
        font-size: 1.5rem; margin: 0; letter-spacing: 0.04em;
    }
    .geovisor-header p { color: #8ab4d4; margin: 4px 0 0 0; font-size: 0.85rem; }
    .info-card {
        background: #0f1923; border: 1px solid #1e3a5f;
        border-radius: 8px; padding: 14px 16px; margin-bottom: 10px;
    }
    .info-card h4 {
        color: #f5a623; font-family: 'IBM Plex Mono', monospace;
        font-size: 0.78rem; letter-spacing: 0.08em;
        text-transform: uppercase; margin: 0 0 6px 0;
    }
    .info-card p { color: #8ab4d4; font-size: 0.82rem; margin: 0; line-height: 1.5; }
    .stFileUploader label { color: #5ba4cf !important; font-weight: 600; }
    [data-testid="stFileUploader"] {
        background: #0f1923; border: 1px dashed #1e3a5f;
        border-radius: 8px; padding: 8px;
    }
    hr { border-color: #1e3a5f; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🗺️ Geovisor Colombia")
    st.divider()

    st.markdown("### 🛰️ Mapa base")
    basemap_option = st.radio(
        "Selecciona el fondo de mapa:",
        options=["OpenStreetMap", "Satélite (ESRI)", "Satélite + Etiquetas"],
        index=0,
    )
    st.divider()

    st.markdown("### 📦 Cargar GeoPackage")
    gpkg_file = st.file_uploader(
        "Sube tu archivo .gpkg",
        type=["gpkg"],
        help="El mapa se centrará automáticamente en el GeoPackage cargado.",
    )

    gpkg_layer = None
    gdf = None
    show_col = "(ninguna)"

    if gpkg_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".gpkg") as tmp:
            tmp.write(gpkg_file.read())
            tmp_gpkg = tmp.name

        try:
            import pyogrio
            layers = [str(row[0]) for row in pyogrio.list_layers(tmp_gpkg)]
        except Exception:
            layers = []

        if layers:
            gpkg_layer = st.selectbox("Capa a visualizar:", layers)

        if gpkg_layer:
            try:
                gdf = gpd.read_file(tmp_gpkg, layer=gpkg_layer)
                if gdf.crs and gdf.crs.to_epsg() != 4326:
                    gdf = gdf.to_crs(epsg=4326)
                st.success(f"✅ {len(gdf)} features cargadas")
                cols = [c for c in gdf.columns if c != "geometry"]
                if cols:
                    show_col = st.selectbox("Columna para tooltips:", ["(ninguna)"] + cols)
            except Exception as e:
                st.error(f"Error al leer el GeoPackage: {e}")

    st.divider()
    st.markdown("""
    <div class="info-card">
        <h4></h4>
        <p>Universidad <strong>Sergio Arboleda</strong>.<br>
        Maestría en gestión de la información y tecnologías geoespaciales.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="geovisor-header">
    <div>
        <h1>🗺️ Geovisor Colombia</h1>
        <p>Visualización de datos geoespaciales </p>
    </div>
</div>
""", unsafe_allow_html=True)

default_lat, default_lon, default_zoom = 4.5709, -74.2973, 6

if gdf is not None:
    bounds = gdf.total_bounds
    default_lat = (bounds[1] + bounds[3]) / 2
    default_lon = (bounds[0] + bounds[2]) / 2
    default_zoom = 14

BASEMAP_MAP = {
    "OpenStreetMap": "OpenStreetMap",
    "Satélite (ESRI)": "SATELLITE",
    "Satélite + Etiquetas": "HYBRID",
}

m = leafmap.Map(
    center=[default_lat, default_lon],
    zoom=default_zoom,
    locate_control=True,
    latlon_control=True,
    draw_export=False,
    minimap_control=True,
    search_control=False,
)

selected_basemap = BASEMAP_MAP[basemap_option]
if selected_basemap != "OpenStreetMap":
    m.add_basemap(selected_basemap)

if gdf is not None:
    m.add_gdf(
        gdf,
        layer_name=gpkg_layer,
        style={"fillColor": "#f5a623", "color": "#1e3a5f", "weight": 2, "fillOpacity": 0.35},
        highlight_style={"fillColor": "#5ba4cf", "color": "#ffffff", "weight": 3, "fillOpacity": 0.6},
        info_mode="on_hover" if show_col != "(ninguna)" else None,
    )
    bounds = gdf.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

m.to_streamlit(height=700, responsive=True)

if gdf is not None:
    with st.expander("📊 Tabla de atributos", expanded=False):
        display_cols = [c for c in gdf.columns if c != "geometry"]
        st.dataframe(gdf[display_cols], use_container_width=True)
