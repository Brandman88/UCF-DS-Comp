import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import FastMarkerCluster

# Load the block groups shapefile
blocks = gpd.read_file("tl_rd22_12_bg.shp")
blocks['geometry'] = blocks['geometry'].simplify(tolerance=0.001)
data = pd.read_csv("data.csv")

# Convert each column to string and ensure correct zero-padding
data['State Code'] = data['State Code'].astype(str).str.zfill(2)
data['County Code'] = data['County Code'].astype(str).str.zfill(3)
data['Census Tract'] = data['Census Tract'].str.replace('Census Tract ', '')
data['Block Group'] = data['Block Group'].str.replace('Block Group ', '').astype(str)

# Create the new 'GEOID_new' in the data DataFrame
data['GEOID_new'] = data['State Code'] + data['County Code'] +  data['Census Tract'].str.replace('Census Tract ', '').str.replace('.', '').astype(str).str.zfill(6) + data['Block Group']

# Merge the geospatial data with your data based on the new GEOID
merged = blocks.merge(data, left_on='GEOID', right_on='GEOID_new', how='left')

# Filter out invalid income values
merged = merged[merged['Median Household Income'] > 0]

def style_function(feature):
    return {
        'fillColor': '#ffaf00',
        'color': 'blue',
        'weight': 2,
        'fillOpacity': 0.5,
        'dashArray': '5, 5'
    }

# Create the map centered on the data
m = folium.Map(location=[merged['geometry'].centroid.y.mean(), 
                         merged['geometry'].centroid.x.mean()], 
               zoom_start=10, tiles="cartodb positron")
# Automatically generate fields and aliases based on CSV headers
tooltip_fields = data.columns
tooltip_aliases = [field.replace('_', ' ').title() + ':' for field in tooltip_fields]

# Add block groups to the map with interactivity
folium.GeoJson(merged, 
               tooltip=folium.GeoJsonTooltip(fields=tooltip_fields.tolist(), aliases=tooltip_aliases, localize=True),
               style_function=style_function,
               smooth_factor=2.0).add_to(m)

# Add layer control to toggle roads and landmarks
folium.LayerControl().add_to(m)

# Save the map to an HTML file
m.save("interactive_map.html")