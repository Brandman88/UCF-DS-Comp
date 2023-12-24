import geopandas as gpd
import pandas as pd
import folium
from folium import FeatureGroup
from folium.plugins import FastMarkerCluster

# Define style functions
def road_style_function(feature):
    return {'color': 'grey', 'weight': 1}

def pointlm_style_function(feature):
    return {'fillColor': 'purple', 'color': 'purple', 'weight': 1, 'fillOpacity': 0.6}


def block_style_function(feature):
    return {'fillColor': '#ffaf00', 'color': 'blue', 'weight': 2, 'fillOpacity': 0.5, 'dashArray': '5, 5'}

def place_style_function(feature):
    return {
        'fillColor': 'green',
        'color': 'darkgreen',
        'weight': 2,
        'fillOpacity': 0.6,
        'dashArray': '5, 5'
    }

def tract_style_function(feature):
    return {
        'fillColor': 'orange',
        'color': 'black',
        'weight': 2,
        'fillOpacity': 0.6,
        'dashArray': '5, 5'
    }

def cousub_style_function(feature):
    return {
        'fillColor': 'red',
        'color': 'purple',
        'weight': 2,
        'fillOpacity': 0.6,
        'dashArray': '5, 5'
    }










def filter_with_sindex(gdf, gdf_index, other_geom):
    possible_matches_index = list(gdf_index.intersection(other_geom.bounds))
    possible_matches = gdf.iloc[possible_matches_index]
    precise_matches = possible_matches[possible_matches.intersects(other_geom)]
    return precise_matches

# Define the projected CRS and the field name mapping
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
places = gpd.read_file("tl_rd22_12_place.shp")
pointlm = gpd.read_file("tl_rd22_12_pointlm.shp")
tracts = gpd.read_file("tl_rd22_12_tract.shp")
cousub = gpd.read_file("tl_rd22_12_cousub.shp")

print("Original CRS:", blocks.crs)  # It should print EPSG:4269

#print(blocks['TYPE'].unique())
#print(roads['TYPE'].unique())
#print(places['TYPE'].unique())
print(pointlm)
#print(tracts['TYPE'].unique())
#print(cousub['TYPE'].unique())


# Simplify geometries
#blocks['geometry'] = blocks['geometry'].simplify(tolerance=0.001)
#places['geometry'] = places['geometry'].simplify(tolerance=0.001)
#pointlm['geometry'] = pointlm['geometry'].simplify(tolerance=0.001)
#tracts['geometry'] = tracts['geometry'].simplify(tolerance=0.001)
#cousub['geometry'] = cousub['geometry'].simplify(tolerance=0.001)


# Get the column names for each GeoDataFrame
tracts_columns = tracts.columns.tolist()
places_columns = places.columns.tolist()
cousub_columns = cousub.columns.tolist()
pointlm_columns = pointlm.columns.tolist()

print("Tracts columns:", tracts_columns)
print("Places columns:", places_columns)
print("Cousub columns:", cousub_columns)
print("PointLM columns:", pointlm_columns)


# Filter out entries where the 'FULLNAME' column is null
pointlm = pointlm[pointlm['FULLNAME'].notnull()]


# Reproject the geometries to the projected CRS for accurate calculations
blocks_projected = blocks.to_crs(projected_crs)
roads_projected = roads.to_crs(projected_crs)
places_projected = places.to_crs(projected_crs)
pointlm_projected = pointlm.to_crs(projected_crs)
tracts_projected = tracts.to_crs(projected_crs)
cousub_projected = cousub.to_crs(projected_crs)


# Create spatial indexes for faster querying
blocks_index = blocks_projected.sindex
roads_index = roads_projected.sindex
places_index= places_projected.sindex
pointlm_index= pointlm_projected.sindex
tracts_index= tracts_projected.sindex
cousub_index= cousub_projected.sindex


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
filtered_roads_projected = filter_with_sindex(roads_projected, roads_index, unified_buffer)
filtered_places_projected = filter_with_sindex(places_projected, places_index, unified_buffer)
filtered_pointlm_projected = filter_with_sindex(pointlm_projected, pointlm_index, unified_buffer)
filtered_tracts_projected = filter_with_sindex(tracts_projected, tracts_index, unified_buffer)
filtered_cousub_projected = filter_with_sindex(cousub_projected, cousub_index, unified_buffer)


# Reproject the filtered geometries back to the original geographic CRS for mapping
filtered_blocks_geo = filtered_blocks_projected.to_crs('EPSG:4269')
filtered_roads_geo = filtered_roads_projected.to_crs('EPSG:4269')
filtered_places_geo = filtered_places_projected.to_crs('EPSG:4269')
filtered_pointlm_geo = filtered_pointlm_projected.to_crs('EPSG:4269')
filtered_tracts_geo = filtered_tracts_projected.to_crs('EPSG:4269')
filtered_cousub_geo = filtered_cousub_projected.to_crs('EPSG:4269')

# Print the total number of landmarks before filtering
print("Total landmarks before filtering:", len(pointlm))




#landmarks_points = filtered_pointlm_geo[['geometry']].copy()
#landmarks_points['geometry'] = landmarks_points['geometry'].apply(lambda geom: [geom.y, geom.x])
#landmarks_points_list = landmarks_points['geometry'].tolist()





landmarks_points_list = [
    [row['geometry'].y, row['geometry'].x] for idx, row in filtered_pointlm_geo.iterrows() if pd.notnull(row['FULLNAME']) and row['geometry'] is not None
]
#landmarks_points_list = filtered_pointlm_geo.apply( lambda row: [row.geometry.y, row.geometry.x, row['FULLNAME']], axis=1).tolist()

# Initialize an empty feature group for the landmarks
landmark_group = FeatureGroup(name="Landmarks")

# Print the total number of landmarks after filtering
print("Total landmarks after filtering:", len(landmarks_points_list))


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
        style_function=block_style_function,
        tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases, localize=True),
        name="Block Groups",  # Custom name for the block groups layer
        show=False
    ).add_to(m)
    
    if not filtered_places_geo.empty:
        folium.GeoJson(
            filtered_places_geo,
            style_function=place_style_function,
            name="Places",
            show=False,
            tooltip=folium.GeoJsonTooltip(
                fields=['NAMELSAD', 'ALAND', 'AWATER', 'INTPTLAT', 'INTPTLON'],
                aliases=['Place Name:', 'Area of Land:', 'Area of Water:', 'Latitude:', 'Longitude:']
            )
        ).add_to(m)

    landmarks_locations = []
    popups = []
    
    if not filtered_pointlm_geo.empty:
        for idx, row in filtered_pointlm_geo.iterrows():
            if pd.notnull(row['FULLNAME']) and row['geometry'] is not None:
                lat, lon = row['geometry'].y, row['geometry'].x
                popup_content = f"""
            <div>
                <strong>Name:</strong> {row['FULLNAME']}<br>
                <strong>Latitude:</strong> {lat}<br>
                <strong>Longitude:</strong> {lon}
            </div>
            """
                landmarks_locations.append([lat, lon, popup_content])

            # Custom callback function for marker creation
        callback = """
        function (row) {
        var marker = L.marker(new L.LatLng(row[0], row[1]));
        marker.bindPopup(row[2]);
        return marker;
        };
        """

    # Add FastMarkerCluster to the map
    m.add_child(FastMarkerCluster(data=landmarks_locations, callback=callback, name="Landmarks", show=False))

    """
        FastMarkerCluster(data=landmarks_points_list, name="Landmarks", show=False).add_to(m)
    """
        
    '''
   if not filtered_pointlm_geo.empty:
        FastMarkerCluster(
            data=landmarks_points_list,
            name="Landmarks",
            show=False,
            callback=callback
        ).add_to(m)
    '''


    if not filtered_tracts_geo.empty:
        folium.GeoJson(
            filtered_tracts_geo,
            style_function=tract_style_function,
            name="Census Tracts",
            show=False,
            tooltip=folium.GeoJsonTooltip(
                fields=['NAMELSAD', 'ALAND', 'AWATER', 'INTPTLAT', 'INTPTLON'],
                aliases=['Tract Name:', 'Area of Land:', 'Area of Water:', 'Latitude:', 'Longitude:']
            )
        ).add_to(m)

    if not filtered_cousub_geo.empty:
        folium.GeoJson(
            filtered_cousub_geo,
            style_function=cousub_style_function,
            name="County Subdivisions",
            show=False,
            tooltip=folium.GeoJsonTooltip(
                fields=['NAMELSAD', 'ALAND', 'AWATER', 'INTPTLAT', 'INTPTLON'],
                aliases=['Subdivision Name:', 'Area of Land:', 'Area of Water:', 'Latitude:', 'Longitude:']
            )
        ).add_to(m)
    
    # Add filtered roads to the map
    folium.GeoJson(filtered_roads_geo,style_function=road_style_function,name="Filtered Roads", show=False).add_to(m)

    # Add layer control to toggle layers
    folium.LayerControl().add_to(m)



    # Save the map to an HTML file
    m.save("interactive_map.html")
else:
    print("No data available to display on the map.")
