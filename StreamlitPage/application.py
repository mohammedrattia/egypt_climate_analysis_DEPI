import streamlit as st
import folium
import numpy as np
import pandas as pd
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import matplotlib.colors as mcolors
import plotly.express as px
import plotly.graph_objects as go
import calendar
from pathlib import Path
import plotly.colors
import random

# Load data
@st.cache_data
def load_data():
    data_small_df = pd.read_csv("data/fullWithLocations_FINAL_small.csv")
    data_large_df = pd.read_csv("data/fullWithLocations_FINAL_large.csv")
    df_Mapped = pd.read_excel("data/dataMapping.xlsx")
    data_large_df['Month_Name'] = data_large_df['Month'].apply(lambda x: calendar.month_abbr[x]) 
    data_small_df['Month_Name'] = data_small_df['Month'].apply(lambda x: calendar.month_abbr[x]) 
    return data_small_df, data_large_df, df_Mapped

data_small_df, data_large_df, df_Mapped = load_data()
df_Large = data_large_df.copy()
df_Small = data_small_df.copy()

# Group definitions
group_small = [
    "AIRMASS", "ALLSKY_SFC_SW_DWN", "ALLSKY_SFC_UVA", "ALLSKY_SFC_UVB",
    "ALLSKY_SFC_UV_INDEX", "CLOUD_AMT", "CLOUD_AMT_DAY", "CLOUD_AMT_NIGHT",
    "CLRSKY_DAYS", "MIDDAY_INSOL", "PSH", "PW"
]

group_large = [
    "EVLAND", "GWETPROF", "GWETROOT", "GWETTOP", "PRECSNO", "PRECTOTCORR",
    "QV2M", "RH2M", "RHOA", "T10M", "T10M_MAX", "T10M_MIN", "T2M",
    "T2M_MAX", "T2M_MIN", "TO3", "TS", "TSOIL1", "TSOIL2", "TSOIL3",
    "TSOIL4", "TSOIL5", "TSOIL6", "TS_MAX", "TS_MIN", "WD2M", "WD50M",
    "WS2M", "WS2M_MAX", "WS2M_MIN", "WS50M", "WS50M_MAX", "WS50M_MIN", "Z0M"
]

# Combine groups for the dropdown
attribute_options = df_Mapped["Code"]

# Streamlit UI
st.title("Egypt Climate Data Visualization")

# =============================================
# SECTION 1: FOLIUM MAP
# =============================================
st.header("Geospatial Visualization")

# Create widgets for map
col1, col2 = st.columns(2)
with col1:
    map_year = st.number_input("Map Year:", 
                             min_value=int(data_large_df['YEAR'].min()),
                             max_value=int(data_large_df['YEAR'].max()),
                             value=int(data_large_df['YEAR'].min()))
with col2:
    map_attribute = st.selectbox("Map Attribute:", 
                               options=attribute_options,
                               index=attribute_options.to_list().index("PRECTOTCORR") if "PRECTOTCORR" in attribute_options.to_list() else 0)

map_agg_mode = st.selectbox("Aggregation Mode:", ["Week", "Month", "Chapter", "DOY"])
map_period = st.number_input("Period:", min_value=1, max_value=366, value=26)

def display_aggregated_map(year, attribute, agg_mode, period):

    EGYPT_BOUNDS = {
        'min_lat': 22.0,  
        'max_lat': 31.8, 
        'min_lon': 24.5,  
        'max_lon': 37.0    
    }

    if attribute in group_small:
        df = data_small_df
    elif attribute in group_large:
        df = data_large_df
    else:
        st.error("Attribute not found!")
        return

    df_year = df[df['YEAR'] == year].copy()
    if df_year.empty:
        st.warning(f"No data available for Year {year}")
        return

    if agg_mode == "Week":
        df_agg = df_year[df_year['Week'] == period]
        title_period = f"Week: {period}"
    elif agg_mode == "Month":
        df_agg = df_year[df_year['Month'] == period]
        title_period = f"Month: {period}"
    elif agg_mode == "Chapter":
        df_agg = df_year[df_year['Chapter'] == period]
        title_period = f"Chapter: {period}"
    elif agg_mode == "DOY":
        df_agg = df_year[df_year['DOY'] == period]
        title_period = f"DOY: {period}"
    else:
        df_agg = df_year
        title_period = "All Days"

    if df_agg.empty:
        st.warning(f"No data available for {agg_mode} {period} in Year {year}")
        return

    
    bounded_df = df_agg[
        (df_agg['LAT'] >= EGYPT_BOUNDS['min_lat']) & 
        (df_agg['LAT'] <= EGYPT_BOUNDS['max_lat']) & 
        (df_agg['LON'] >= EGYPT_BOUNDS['min_lon']) & 
        (df_agg['LON'] <= EGYPT_BOUNDS['max_lon'])
    ]

    group_cols = ['LAT', 'LON']
    agg_df = bounded_df.groupby(group_cols)[attribute].mean().reset_index()

    min_value = agg_df[attribute].min()
    max_value = agg_df[attribute].max()
    
    agg_df['Intensity'] = agg_df[attribute].apply(
        lambda x: (x - min_value) / (max_value - min_value) if max_value > min_value else min_value
    )

    
    center_lat = (EGYPT_BOUNDS['min_lat'] + EGYPT_BOUNDS['max_lat']) / 2
    center_lon = (EGYPT_BOUNDS['min_lon'] + EGYPT_BOUNDS['max_lon']) / 2

    # Create map with Egypt's fixed bounds
    egypt_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        min_lat=EGYPT_BOUNDS['min_lat'],
        max_lat=EGYPT_BOUNDS['max_lat'],
        min_lon=EGYPT_BOUNDS['min_lon'],
        max_lon=EGYPT_BOUNDS['max_lon'],
        max_bounds=True,
        control_scale=True
    )
    
    # Add rectangle to show Egypt's boundaries
    folium.Rectangle(
        bounds=[(EGYPT_BOUNDS['min_lat'], EGYPT_BOUNDS['min_lon']), 
                (EGYPT_BOUNDS['max_lat'], EGYPT_BOUNDS['max_lon'])],
        color='blue',
        fill=False,
        weight=2,
        opacity=0,
        tooltip="Egypt Boundaries"
    ).add_to(egypt_map)

    title_html = f'<h3 align="center" style="font-size:20px"><b>Year: {year} - {title_period} - Attribute: {attribute}</b></h3>'
    egypt_map.get_root().html.add_child(folium.Element(title_html))
    
    # Add heatmap if there's data
    if not agg_df.empty:
        heatmap_data = agg_df[agg_df['Intensity'] > 0][['LAT', 'LON', 'Intensity']].values.tolist()
        HeatMap(heatmap_data, radius=10, blur=15, max_zoom=10).add_to(egypt_map)

        colors = ["black", "blue", "cyan", "yellow", "orange", "red"]
        quantiles = np.quantile(agg_df["Intensity"], [0.01, 0.55, 0.7, 0.85, 0.95, 1.0])

        def intensity_to_color(intensity):
            if intensity <= quantiles[0]:
                return mcolors.to_hex(colors[0])
            elif intensity <= quantiles[1]:
                return mcolors.to_hex(colors[1])
            elif intensity <= quantiles[2]:
                return mcolors.to_hex(colors[2])
            elif intensity <= quantiles[3]:
                return mcolors.to_hex(colors[3])
            elif intensity <= quantiles[4]:
                return mcolors.to_hex(colors[4])
            else:
                return mcolors.to_hex(colors[5])

        for _, row in agg_df.iterrows():
            if row["Intensity"] > 0:
                tooltip_text = f"{attribute}: {row[attribute]:.5f}"
                if 'City' in agg_df.columns:
                    tooltip_text = f"City: {row['City']}, " + tooltip_text
                folium.CircleMarker(
                    location=[row['LAT'], row['LON']],
                    radius=7,
                    color=intensity_to_color(row['Intensity']),
                    fill=True,
                    fill_color=intensity_to_color(row['Intensity']),
                    fill_opacity=0.6,
                    tooltip=tooltip_text
                ).add_to(egypt_map)
    else:
        st.warning("No data points within Egypt's boundaries")

    return egypt_map
# Display map
m = display_aggregated_map(map_year, map_attribute, map_agg_mode, map_period)
if m:
    st_data = st_folium(m, width=700, height=600)

# Save functionality
if st.button("Save Map as HTML"):
    if m:
        filename = f"Aggregated_{map_attribute}_{map_year}_{map_agg_mode}{map_period}.html"
        m.save(filename)
        with open(filename, "rb") as f:
            st.download_button(
                label="Download HTML",
                data=f,
                file_name=filename,
                mime="text/html"
            )
    else:
        st.warning("No map to save")

# =============================================
# SECTION 2: GRAPHS VISUALIZATION
# =============================================
st.header("Statistical Visualizations")

# Create widgets for graphs
graph_col1, graph_col2 = st.columns(2)
with graph_col1:
    graph_year = st.selectbox("Graph Year:", 
                            options=sorted(data_large_df['YEAR'].unique()),
                            index=0)
with graph_col2:
    graph_month = st.selectbox("Graph Month:", 
                             options=list(calendar.month_abbr)[1:],
                             index=0)

graph_attribute = st.selectbox("Graph Attribute:", 
                             options=attribute_options,
                             index=attribute_options.to_list().index("PRECTOTCORR") if "PRECTOTCORR" in attribute_options.to_list() else 0)

# Get attribute name for display
Att_Name = df_Mapped.loc[df_Mapped["Code"] == graph_attribute, "Name"].iloc[0]

# Determine which dataframe to use
if graph_attribute in group_large:
    df = df_Large.copy()
else:
    df = df_Small.copy()

# Filter data for selected year and month
month_num = list(calendar.month_abbr).index(graph_month)
df_filtered = df[(df['YEAR'] == graph_year) & (df['Month'] == month_num)]

if not df_filtered.empty:
    # Create directory for saving graphs
    base_dir = Path(f"resources/{graph_attribute}")
    base_dir.mkdir(parents=True, exist_ok=True)

    # ======================
    # HISTOGRAM
    # ======================
    st.subheader(f"Histogram of {Att_Name}")
    fig_hist = px.histogram(df_filtered, 
                           x=graph_attribute, 
                           nbins=300,
                           title=f"{Att_Name} Distribution for {graph_month} {graph_year}",
                           labels={graph_attribute: Att_Name, "count": "Frequency"},
                           color_discrete_sequence=["royalblue"])
    
    fig_hist.update_layout(template="plotly_white")
    st.plotly_chart(fig_hist, use_container_width=True)

    # ======================
    # MONTHLY STATS BAR PLOT
    # ======================
    st.subheader(f"Monthly Statistics for {Att_Name}")
    
    month_stats = df[df['YEAR'] == graph_year].groupby("Month")[graph_attribute].agg(["min", "max", "mean"]).reset_index()
    month_stats['Month_Name'] = month_stats['Month'].apply(lambda x: calendar.month_abbr[x])
    
    fig_stats = px.bar(month_stats, 
                      x="Month_Name", 
                      y=["min", "max", "mean"],
                      title=f"Min, Max, and Mean {Att_Name} for {graph_year}",
                      labels={"value": Att_Name, "Month_Name": "Month"},
                      barmode="group")
    
    st.plotly_chart(fig_stats, use_container_width=True)

    # ======================
    # CITY STATS BAR PLOT
    # ======================
    st.subheader(f"City Statistics for {Att_Name}")
    
    city_stats = df_filtered.groupby("City")[graph_attribute].agg(["min", "max", "mean"]).reset_index()
    
    fig_city = px.bar(city_stats, 
                     x="City", 
                     y=["min", "max", "mean"],
                     title=f"City-wise {Att_Name} Statistics for {graph_month} {graph_year}",
                     labels={"value": Att_Name, "City": "City"},
                     barmode="group")
    
    st.plotly_chart(fig_city, use_container_width=True)

    # ======================
    # TOP 10 POINTS TABLE
    # ======================
    st.subheader(f"Top 10 Highest {Att_Name} Values")
    top_10_points = df_filtered.nlargest(10, graph_attribute)[["City", graph_attribute, "Date"]]
    st.dataframe(top_10_points)

else:
    st.warning(f"No data available for {graph_month} {graph_year}")