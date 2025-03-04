import json
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns
from google.cloud import bigquery
from google.oauth2 import service_account

import os

def load_data():
    service_account_json = st.secrets["gcp_service_account"]
    
    # 2. Convert it to a Python dict
    service_account_dict = json.loads(service_account_json)
    
    # 3. Create credentials object
    credentials = service_account.Credentials.from_service_account_info(service_account_dict)
    
    # 4. Create BigQuery client with these credentials
    client = bigquery.Client(
        project="homework-1-452605",
        credentials=credentials
    )
    
    # 5. Query your data
    query = "SELECT * FROM `homework-1-452605.survery_1309.survey_table`"
    df = client.query(query).to_dataframe()
    df['ACTIVEFLAG'] = df['ACTIVEFLAG'].fillna(0).astype(int)
    return df

# @st.cache
# def load_data():
#     client = bigquery.Client(project='homework-1-452605')
#     query = "SELECT * FROM `homework-1-452605.survery_1309.survey_table`"
#     df = client.query(query).to_dataframe()
#     df['ACTIVEFLAG'] = df['ACTIVEFLAG'].fillna(0).astype(int)
#     return df

data = load_data()

st.title("Facilities Data Dashboard")

# Sidebar Filters
st.sidebar.header("Filter Options")
active_filter = st.sidebar.multiselect("Select Active Flag", 
                                       options=data['ACTIVEFLAG'].unique(), 
                                       default=data['ACTIVEFLAG'].unique())
min_elev = st.sidebar.slider("Minimum Elevation (ft)", 
                             float(data['ELEVATIONFT'].min()), 
                             float(data['ELEVATIONFT'].max()), 
                             float(data['ELEVATIONFT'].min()))
max_elev = st.sidebar.slider("Maximum Elevation (ft)", 
                             float(data['ELEVATIONFT'].min()), 
                             float(data['ELEVATIONFT'].max()), 
                             float(data['ELEVATIONFT'].max()))

# Apply filters to data
filtered_data = data[
    (data['ACTIVEFLAG'].isin(active_filter)) &
    (data['ELEVATIONFT'] >= min_elev) &
    (data['ELEVATIONFT'] <= max_elev)
]

# Visualization 1: Map View (using Folium)
st.header("Map View")
map_center = [37.3382, -121.8863]
m = folium.Map(location=map_center, zoom_start=12)

for _, row in filtered_data.iterrows():
    folium.Marker(
        location=[row['LATITUDE_DEC'], row['LONGITUDE_DEC']],
        popup=f"Facility ID: {row['FACILITYID']}, Elevation: {row['ELEVATIONFT']} ft",
        icon=folium.Icon(color='blue' if row['ACTIVEFLAG'] == 1 else 'red')
    ).add_to(m)
st_data = st_folium(m, width=700)

# Visualization 2: Elevation Distribution (Histogram)
st.header("Elevation Distribution")
fig1, ax1 = plt.subplots(figsize=(10, 6))
sns.histplot(filtered_data['ELEVATIONFT'], bins=20, kde=True, ax=ax1, color='green')
ax1.set_title('Distribution of Facility Elevation (in feet)')
ax1.set_xlabel('Elevation (ft)')
ax1.set_ylabel('Frequency')
st.pyplot(fig1)

# Visualization 3: Active vs Inactive Facilities (Bar Graph)
st.header("Active vs Inactive Facilities")
active_counts = filtered_data['ACTIVEFLAG'].value_counts().sort_index()
fig2, ax2 = plt.subplots(figsize=(8, 6))
sns.barplot(x=active_counts.index, y=active_counts.values, ax=ax2, palette='viridis')
ax2.set_title('Active vs Inactive Facilities')
ax2.set_xlabel('Active Flag (0 = Inactive, 1 = Active)')
ax2.set_ylabel('Number of Facilities')
st.pyplot(fig2)
