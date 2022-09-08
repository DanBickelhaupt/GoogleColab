# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 17:08:00 2022

@author: BICKELDJ1
"""

# Given FlightAware aircraft & carrier codes and look-up csv paths, use function get_function_data() to get aircraft interior information from aerolopa.com.

# EXAMPLE:
# ac_id = 'A321'
# carrier_code = 'AAL'
# ac_decode = "ac_codes.csv"
# carrier_decoder = "carrier_codes.csv"
# aerolopa_decoder = "aerolopa_links_final.csv"
# comfort_data = get_comfort_data(ac_id, carrier_code, ac_decode, carrier_decoder, aerolopa_decoder)   
# seat_width = get_seat_width(comfort_data)

# Imports
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import numpy as np

# Functions
def get_html_data(url):
    headers = {
        "Accept-Language" : "en-US,en;q=0.5",
        "User-Agent": "Defined",
    }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    soup = soup.body
    results_all = soup.find_all('div', {'class':'text'})
    return str(results_all[1])

def remove_bracket_text(string):
    start = []
    stop = []
    removal_pair = []
    out = string
    for i, letter in enumerate(string):
        if letter == '<':
            start = i
        if letter == '>':
            stop = i
        if (start != []) and (stop != []):
            removal_pair.append((start, stop))
            start = []
            stop = []
    if len(removal_pair) > 0:
        idx_adjust = 0
        for pair in removal_pair:
            out = out[:pair[0]-idx_adjust] + " " + out[pair[1]-idx_adjust+1:]
            idx_adjust += pair[1] - pair[0]
    return out

def get_url_data(url):
    headers = {
        "Accept-Language" : "en-US,en;q=0.5",
        "User-Agent": "Defined",
    }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    soup = soup.body
    results_all = soup.find_all('div', {'class':'text'})
    output_final = ''
    for results in results_all:
        results = list(results)
        output_interim = ''
        for item in results: 
            item = str(item)
            if item == '<br/>':
                output_interim += '\n'
            else:
                item = item.replace("<p>","")
                item = item.replace("</p>", "")
                item = item.replace("<br/>", "\n")
                output_interim += item
        strip_list = ['<strong>', '</strong>', 'strong>', '</strong']
        for remove in strip_list:
            output_interim = output_interim.replace(remove, '')
        output_interim = output_interim.replace('\n\n','\n')
        if '=' not in output_interim:
            output_final += output_interim
    return remove_bracket_text(output_final)

def get_link(query, link_df):
    # Match query with table entry
    bool_list = (link_df['Airline'].str.contains(query[0])) & (link_df['OEM'] == query[1]) & (link_df['AC'].str.contains(query[2]))
    if bool_list.sum() > 0:
        link = str(link_df['Link'][bool_list].values[0])
    else:
        link = ''
    return link

def convert_fa_codes(ac_id, carrier_code, acid_df, carrier_df):
    # Get OEM and A/C type from aircraft_id
    carrier_code = carrier_code.strip()
    ac_id = ac_id.strip()
    oem_acmodel = acid_df[acid_df['Code'] == ac_id]['Aircraft Type'].iloc[0]
    idx = oem_acmodel.find(' ')
    oem = oem_acmodel[:idx]
    ac = oem_acmodel[idx+1:]
    # Get carrier name from carrier code
    carrier_name = carrier_df[carrier_df['Carrier Code'] == carrier_code]['Carrier'].iloc[0].replace(' Airlines', '')
    return [carrier_name, oem, ac]

def get_comfort_data(ac_id, carrier_code, ac_code_loc, carrier_code_loc, aerolopa_code_loc):
    # Load decoder rings
    acid_df = pd.read_csv(ac_code_loc, encoding="iso-8859-1")
    carrier_df = pd.read_csv(carrier_code_loc, encoding="iso-8859-1")
    aerolopa_lookup_df = pd.read_csv(aerolopa_code_loc, encoding="iso-8859-1")
    # Convert FlightAware codes into Aerolopa format for query
    query = convert_fa_codes(ac_id, carrier_code, acid_df, carrier_df)
    # Return plane comfort data
    base_url = "https://www.aerolopa.com/"
    html_suffix = get_link(query, aerolopa_lookup_df)
    if html_suffix != '':
        comfort_data = get_url_data(base_url+html_suffix)
    else:
        comfort_data = 'No cabin data available.'
    return comfort_data

def get_seat_width(string_in):
    idx = string_in.lower().rfind('seat width')
    start = idx-25
    try:
        text = string_in[idx-7:idx+17]
    except:
        try:
            text = string_in[:idx+17]
        except:
            text = string_in
    seat_width = []
    if idx != -1:
        seat_width = re.findall(r'\d+\.\d+', text)
        if seat_width == []:
            seat_width = re.findall(r'\d+', text)
    if len(seat_width)>0: seat_width = seat_width[-1]
    return 17.0 if isinstance(seat_width, list) and len(seat_width) == 0 else seat_width

# TODO: Update get_comfort_data to pull from .csv

headers = {
        "Accept-Language" : "en-US,en;q=0.5",
        "User-Agent": "Defined",
}
proxies = {
    'http': 'http://zs-servproxy.utc.com:80',
    'https': 'http://zs-servproxy.utc.com:80',
}
url = "https://www.aerolopa.com/"
page = requests.get(url, headers=headers, proxies=proxies)
soup = BeautifulSoup(page.content, 'html.parser')


# Get all aerolopa data
aerolopa_decoder = "aerolopa_links_final.csv"
aerolopa_df = pd.read_csv(aerolopa_decoder)
base_url = "https://www.aerolopa.com/"
scrape_save = []
for html_suffix in aerolopa_df["Link"]:
    comfort_data = get_url_data(base_url+html_suffix)
    scrape_save.append(comfort_data)
aerolopa_df["Website_Data"] = np.array(scrape_save).reshape(-1,1)