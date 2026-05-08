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
            except Exception as e:
                st.error(f"Error al leer el GeoPackage: {e}")

    st.divider()
    st.markdown("Universidad **Sergio Arboleda**")
    st.markdown("Maestría en gestión de la información y tecnologías geoespaciales.")

st.title("🗺️ Geovisor Colombia")
st.caption("Visualización de datos geoespaciales")

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
    )
    bounds = gdf.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

m.to_streamlit(height=700, responsive=True)

if gdf is not None:
    with st.expander("📊 Tabla de atributos", expanded=False):
        display_cols = [c for c in gdf.columns if c != "geometry"]
        st.dataframe(gdf[display_cols], use_container_width=True)
