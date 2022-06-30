# import webdriver
import csv
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
import urllib

def get_html(lp_url, chromeDriverPath):
    
    description = ''
    try:
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(chromeDriverPath, options=options)
        # driver = webdriver.Chrome(chromeDriverPath)
        driver.set_page_load_timeout(15)
        driver.get(lp_url)
        html_source = driver.execute_script("return document.documentElement.outerHTML;")
        html_soup = BeautifulSoup(html_source, 'html.parser')
        soup = str(html_soup.find_all("meta")).lower()
        if "description" in soup:
            description = soup.split("description")[0]
            description = description.split('"')[-3]
        else:
            description = 'N/A'
        print(description)
        driver.quit()

    except Exception as e:
        driver.quit()
        print(e)

    return description
  
if __name__ == '__main__':
    filename = "meta_info_2.txt"
    chromeDriverPath = r'C:\Users\QuangND\chromedriver_win32\chromedriver.exe'

    df = pd.read_csv('38k_links_2.csv')
    url = df.loc[:,"HOMEPAGE_URL"]
    list_urls = url.to_list()
    # (list_urls)
    count_url = 0
    for lp_url in list_urls:
        row = [lp_url, get_html(lp_url,chromeDriverPath)]
        with open(filename, 'a', encoding = "utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        count_url = count_url + 1
        print(count_url)
        
       


