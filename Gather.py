import requests
import csv

# Base URL for the latest available ACS 5-year estimates
base_url = "https://api.census.gov/data/2021/acs/acs5"

# Variables to fetch:
variables = "NAME,B01001_001E,B01002_001E,B19013_001E"

# Florida state code
florida_code = "12"

# Fetch all county codes for Florida
county_url = f"{base_url}?get=NAME&for=county:*&in=state:{florida_code}&key=39a6ddc087c074ec8657a6df51e84575df9809f1"
county_response = requests.get(county_url)
counties = [item[2] for item in county_response.json()[1:]]

# Define a local file path to save the data
file_path = 'florida_county_all_block_group_data_2021.csv'

with open(file_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # Updated header
    writer.writerow(["Block Group", "Census Tract", "County", "Total Population", "Median Age", "Median Household Income", "State Code", "County Code", "Block Group Code"])

    for county_code in counties:
        # Constructing the API request URL for block groups within the county
        api_url = f"{base_url}?get={variables}&for=block group:*&in=state:{florida_code}&in=county:{county_code}&key=39a6ddc087c074ec8657a6df51e84575df9809f1"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()[1:]
            
            # Process and write the data
            for row in data:
                # Splitting the NAME field
                parts = row[0].split(", ")
                block_group = parts[0]
                census_tract = parts[1]
                county = parts[2]
                
                # Writing the processed data
                writer.writerow([block_group, census_tract, county, row[1], row[2], row[3], row[4], row[5], row[6]])

        else:
            print(f"Failed to retrieve data for Florida county:{county_code}. Error: {response.text}")

print(f"Data saved successfully to {file_path}")
