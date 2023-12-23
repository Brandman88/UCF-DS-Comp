import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import FastMarkerCluster

projected_crs = 'EPSG:4269'

field_name_mapping = {
    'ALAND': 'Area of Land',
    'AWATER': 'Area of Water',
    'INTPTLAT': 'Latitude',
    'INTPTLON': 'Longitude'
    # Add any other renamings here
}


# Load the block groups and roads shapefiles
blocks = gpd.read_file("tl_rd22_12_bg.shp")
roads = gpd.read_file("tl_rd22_12_prisecroads.shp")

print("Original CRS:", blocks.crs)  # It should print EPSG:4269

# Reproject the geometries to the projected CRS for accurate calculations
blocks_projected = blocks.to_crs(projected_crs)
roads_projected = roads.to_crs(projected_crs)


# Simplify geometries
blocks['geometry'] = blocks['geometry'].simplify(tolerance=0.001)

# Load your data from the CSV
data = pd.read_csv("data.csv")

# Convert each column to string and ensure correct zero-padding
data['State Code'] = data['State Code'].astype(str).str.zfill(2)
data['County Code'] = data['County Code'].astype(str).str.zfill(3)
data['Census Tract'] = data['Census Tract'].str.replace('Census Tract ', '').str.replace('.', '').astype(str).str.zfill(6)
data['Block Group'] = data['Block Group'].str.replace('Block Group ', '').astype(str)

# Create the new 'GEOID_new' in the data DataFrame
data['GEOID_new'] = data['State Code'] + data['County Code'] + data['Census Tract'] + data['Block Group']

# Merge the geospatial data with your data based on the new GEOID
merged_blocks_projected = blocks_projected.merge(data, left_on='GEOID', right_on='GEOID_new', how='left')

# Filter out invalid income values or other criteria for your block groups
filtered_blocks_projected = merged_blocks_projected[merged_blocks_projected['Median Household Income'] > 0]

# Create a buffer around your block groups (adjust the distance as needed) in the projected CRS
buffer_distance = 0.03  # Adjust based on your needs and units of the projected CRS
block_buffer = filtered_blocks_projected['geometry'].buffer(buffer_distance)

# Create a unified geometry of all buffers (a single multipolygon)
unified_buffer = block_buffer.unary_union

# Filter roads that intersect with the buffer area (in the projected CRS)
filtered_roads_projected = roads_projected[roads_projected.intersects(unified_buffer)]

# Reproject the filtered geometries back to the original geographic CRS for mapping
filtered_blocks_geo = filtered_blocks_projected.to_crs('EPSG:4269')
filtered_roads_geo = filtered_roads_projected.to_crs('EPSG:4269')


# Define style functions
def road_style_function(feature):
    return {'color': 'grey', 'weight': 1}

def block_style_function(feature):
    return {'fillColor': '#ffaf00', 'color': 'blue', 'weight': 2, 'fillOpacity': 0.5, 'dashArray': '5, 5'}


if not filtered_blocks_geo.empty:
    map_center = [filtered_blocks_geo['geometry'].centroid.y.mean(), filtered_blocks_geo['geometry'].centroid.x.mean()]

    # Create the map centered on the data
    m = folium.Map(location=map_center, zoom_start=10, tiles="cartodb positron")

    # Fields to always exclude
    always_exclude = ['STATEFP', 'COUNTYFP', 'TRACTCE', 'BLKGRPCE', 'GEOID', 'NAMELSAD', 'MTFCC', 'FUNCSTAT', 'geometry']

    # Fields to include in the tooltip, with desired renaming
    base_fields_and_aliases = {
        'Block Group': 'Block Group',
        'Census Tract': 'Census Tract',
        'County': 'County',
        'State Code': 'State Code',
        'County Code': 'County Code',
        'Block Group Code': 'Block Group Code',
        'GEOID_new': 'GEOID',
        'ALAND': 'Area of Land',
        'AWATER': 'Area of Water',
        'INTPTLAT': 'Latitude',
        'INTPTLON': 'Longitude'
    }
    # Fields to always exclude
    always_exclude = ['STATEFP', 'COUNTYFP', 'TRACTCE', 'BLKGRPCE', 'GEOID', 'NAMELSAD', 'MTFCC', 'FUNCSTAT', 'geometry']

    # Identify fields with all null values to exclude them
    null_fields = [col for col in filtered_blocks_geo.columns if filtered_blocks_geo[col].isnull().all()]

    # Prepare tooltip fields and aliases, excluding always excluded and all-null fields
    tooltip_fields = []
    tooltip_aliases = []
    for field, alias in base_fields_and_aliases.items():
        if field not in always_exclude and field not in null_fields:
            tooltip_fields.append(field)
            tooltip_aliases.append(alias + ':')

    # Add additional fields that are not in the base set, aren't excluded, and aren't all null
    additional_fields = [col for col in filtered_blocks_geo.columns if col not in base_fields_and_aliases and col not in always_exclude and col not in null_fields]
    for field in additional_fields:
        tooltip_fields.append(field)
        tooltip_aliases.append(field.replace('_', ' ').title() + ':')

    # Generate tooltip aliases using the mapping
    tooltip_aliases = []
    for field in tooltip_fields:
        if field in field_name_mapping:
            tooltip_aliases.append(field_name_mapping[field] + ':')
        else:
            tooltip_aliases.append(field.replace('_', ' ').title() + ':')

    # Add block groups to the map with interactivity
    folium.GeoJson(
        filtered_blocks_geo,
        style_function=lambda x: {'fillColor': '#ffaf00', 'color': 'blue', 'weight': 2, 'fillOpacity': 0.5, 'dashArray': '5, 5'},
        tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases, localize=True),
        name="Block Groups"  # Custom name for the block groups layer
    ).add_to(m)
    
    # Add filtered roads to the map
    folium.GeoJson(filtered_roads_geo,
               style_function=road_style_function,
               name="Filtered Roads").add_to(m)

    # Add layer control to toggle layers
    folium.LayerControl().add_to(m)



    # Save the map to an HTML file
    m.save("interactive_map.html")
else:
    print("No data available to display on the map.")
