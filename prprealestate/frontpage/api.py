#!/usr/bin/env python

# make sure to install these packages before running:
# pip install pandas
# pip install sodapy

import pandas as pd
from sodapy import Socrata

# Unauthenticated client only works with public data sets. Note 'None'
# in place of application token, and no username or password:
#client = Socrata("data.seattle.gov", None)

MyAppToken = 'REDACTED_APP_TOKEN'

# Example authenticated client (needed for non-public datasets):
client = Socrata("data.seattle.gov", MyAppToken, username="h82w84u@gmail.com", password="REDACTED_PASSWORD")

# First 2000 results, returned as JSON from API / converted to Python list of
# dictionaries by sodapy.
results = client.get("33kz-ixgy", limit=2000)

# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)

for row in results_df.columns:
    print(row)
