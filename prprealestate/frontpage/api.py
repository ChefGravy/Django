#!/usr/bin/env python
import os

# Unauthenticated client only works with public data sets.
MyAppToken = os.getenv('SOCRATA_APP_TOKEN', '')
username = os.getenv('SOCRATA_USERNAME', '')
password = os.getenv('SOCRATA_PASSWORD', '')

# Example client setup:
# from sodapy import Socrata
# client = Socrata("data.seattle.gov", MyAppToken, username=username, password=password)
