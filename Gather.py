import requests
import csv

def get_variable_labels(variable_codes):
    """
    Fetch the corresponding labels for the provided variable codes from the Census API.
    
    Parameters:
    - variable_codes (list): List of variable codes to fetch labels for.
    
    Returns:
    - dict: A dictionary mapping variable codes to their respective labels.
    """
    #url contains census data. Formated in dictionary style. Give it a search
    url = "https://api.census.gov/data/2021/acs/acs5/variables.json"
    response = requests.get(url) # get(url) function sends the request to that URL and returns an HTTP response object
    data = response.json() # contains a Python data structure that corresponds to the JSON data found in the response.
    
    labels = {} #initializing empty dictionary
    # loop to retrieve json data and shove them into labels dictionary.
    for code in variable_codes:
        if code in data["variables"]:#searches for the string variables in data
            label = data["variables"][code]["label"]#code is a unique identifier for a person 
            # Custom replacements based on the specific labels
            if label == "Estimate!!Total:":
                label = "Estimated Population"
            elif label == "Estimate!!Median age --!!Total:":
                label = "Median Age"
            elif "Median household income" in label:
                label = "Median Household Income"
            else:
                label = label.replace("Estimate!!Total:!!", "").replace("Estimate!!", "")
            labels[code] = label
        else:
            print(f"Warning: {code} not found in the API response.")
            
    return labels

base_url = "https://api.census.gov/data/2021/acs/acs5"
variables_list = ["NAME","B01001_001E","B01002_001E","B19013_001E","B24022_060E","B19001B_014E"]# why are we only looking for specific variables. this only accounts for a fraction of them. 
variables_labels = get_variable_labels(variables_list)
variables = ",".join(variables_list)#seperates everything with commas

florida_code = "12"
#This variable contains the URL for making an API request to retrieve data for specific variables at the county level in Florida. It includes parameters like get=NAME, 
# which indicates that you want to retrieve the county names, for=county:*, which specifies that you want data at the county level, 
# and in=state:12, which restricts the query to Florida. It also includes an API key for authentication.
county_url = f"{base_url}?get=NAME&for=county:*&in=state:{florida_code}&key=39a6ddc087c074ec8657a6df51e84575df9809f1"
county_response = requests.get(county_url)
#county response is list that gives you all of the counties, their names the state, and county codes
#[["NAME","state","county"],["Alachua County, Florida","12","001"],["Baker County, Florida","12","003"],...]
counties = [item[2] for item in county_response.json()[1:]]

file_path = 'data.csv'
with open(file_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    header = ["Block Group", "Census Tract", "County"] + list(variables_labels.values()) + ["State Code", "County Code","Block Group Code"]# all one row
    writer.writerow(header)
    for county_code in counties:
        # updates url for specifice census data
        api_url = f"{base_url}?get={variables}&for=block group:*&in=state:{florida_code}&in=county:{county_code}&key=39a6ddc087c074ec8657a6df51e84575df9809f1"
        response = requests.get(api_url)
        #brute force read and write the data.
        if response.status_code == 200:
            try:
                data = response.json()[1:]
            except ValueError:
                continue
            for row in data:
                parts = row[0].split(", ")
                if len(parts) < 3:
                    continue
                block_group = parts[0]
                census_tract = parts[1]
                county = parts[2]
                # Exclude the last value (row[-1]) and keep the rest
                writer.writerow([block_group, census_tract, county] + row[1:-1])
        else:
            print(f"Failed to retrieve data for Florida county:{county_code}. Error: {response.text}")

print(f"Data saved successfully to {file_path}")