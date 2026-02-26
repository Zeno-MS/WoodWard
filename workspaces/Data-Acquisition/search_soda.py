import requests
import json
import pandas as pd

# SODA API endpoints for S-275 data in WA often have specific dataset IDs.
# Searching catalog for S-275
url = "https://data.wa.gov/api/views?q=S-275"
try:
    resp = requests.get(url)
    data = resp.json()
    for item in data:
        print(item.get('id'), item.get('name'))
except Exception as e:
    print(e)
