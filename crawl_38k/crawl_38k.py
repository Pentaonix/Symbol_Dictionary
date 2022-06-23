import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from tqdm import tqdm
import urllib
import socket
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from datetime import datetime
import aspose.words as aw


socket.setdefaulttimeout(15)

# process for vector image
def processSVGImage_1(img_path):
    drawing = svg2rlg(img_path)
    new_img_path = img_path[:img_path.find(".svg")] + ".png"
    renderPM.drawToFile(drawing, new_img_path, fmt="PNG")

    return new_img_path


def processSVGImage_2(img_path):
    doc = aw.Document()
    builder = aw.DocumentBuilder(doc)
    shape = builder.insert_image(img_path)
    pageSetup = builder.page_setup
    pageSetup.page_width = shape.width
    pageSetup.page_height = shape.height
    pageSetup.top_margin = 0
    pageSetup.left_margin = 0
    pageSetup.bottom_margin = 0
    pageSetup.right_margin = 0
    new_img_path = img_path[:img_path.find(".svg")] + ".jpg"
    extractedPage = doc.extract_pages(0, 1)
    extractedPage.save(new_img_path)

    return new_img_path

def processSVGImage(img_path):
    f = open(img_path, "r")
    svgtag = f.read()
    f.close()

    if "Gradient" in svgtag or "gradient" in svgtag:
        processSVGImage_2(img_path)
        os.remove(img_path)
    else:
        try:
            processSVGImage_1(img_path)
            os.remove(img_path)
        except:
            processSVGImage_2(img_path)
            os.remove(img_path)

def download_img_from_url(img_url, save_dir, prefix, num):
    extensions = ['.png', '.jpeg', '.gif', '.jpg', '.webp', '.svg', '.psd']
    opener = urllib.request.build_opener()
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36')]
    urllib.request.install_opener(opener)

    try:
        # print(img_url)
        _img_name = img_url.split("/")[-1]
        ext = _img_name[_img_name.find("."):]
        img_name = f"{prefix}_{num}{ext}"

        if ext not in extensions:
            img_name = f"{prefix}_{num}.png"

        img_path = os.path.join(save_dir, img_name)
        urllib.request.urlretrieve(img_url, img_path)

        if ext == ".svg":
            new_img_path = processSVGImage(img_path)

    except Exception as e:
        print(save_dir, img_url, e)


def get_list_img_svg_from_site(lp_url, chromeDriverPath):
    initiatorTypes = ['img', 'css']
    except_file_ext = ['.woff2', '.js', '.html']

    driver = webdriver.Chrome(chromeDriverPath)
    driver.maximize_window()
    driver.set_page_load_timeout(30)
    driver.get(lp_url)

    img_path_list = []
    try:
        resources = driver.execute_script(
            "return window.performance.getEntriesByType('resource');")
        html_source = driver.execute_script(
            "return document.documentElement.outerHTML;")

        for resource in resources:
            if any(initType == resource['initiatorType'] for initType in initiatorTypes):
                if any(ext in resource["name"] for ext in except_file_ext):
                    continue
                img_path_list.append(resource["name"])

        html_soup = BeautifulSoup(html_source, 'html.parser')
        svg_tag = html_soup.find_all('svg')

    except Exception as e:
        driver.quit()
        print(e)

    return img_path_list, svg_tag


def crawl_image_by_url(lp_url, chromeDriverPath, save_dir, prefix, timeout_lp):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print(prefix)
    img_path_list, svg_tag = get_list_img_svg_from_site(
        lp_url, chromeDriverPath)

    # save image
    num_img = 0
    for img_path in img_path_list:
        num_img += 1
        try:
            download_img_from_url(img_path, save_dir, prefix, num_img)
        except socket.timeout:
            print("OK")
            timeout_lp.append(lp_url)
            break

    if svg_tag is not None:
        for svg in svg_tag:
            num_img += 1
            svg_path = f'{save_dir}/{prefix}_{num_img}.svg'

            with open(svg_path, 'w') as f:
                f.write(str(svg))

            new_img_path = processSVGImage(svg_path)

def crawl_image(chromeDriverPath, campaign_info_df, all_save_dir, client_key, campaignId_key, lp_key, limit=[0,0]):
    timeout_lp = []

    for i in tqdm(range(limit[0], limit[1])):
        campaign = campaign_info_df.iloc[i]
        client_name = campaign[client_key]
        campaign_id = campaign[campaignId_key]
        lp_url = campaign[lp_key]
        prefix = f"{campaign_id}_{client_name}"

        save_dir = f'{all_save_dir}/{campaign_id}_{client_name.replace(" ", "")}'
        # print(save_dir)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        try:
            crawl_image_by_url(lp_url, chromeDriverPath, save_dir, prefix, timeout_lp)
        except Exception as e:
            print("XXXX:\t", lp_url, e)

    return timeout_lp

if __name__ == '__main__':
    chromeDriverPath = r'C:\Users\QuangND\chromedriver_win32\chromedriver.exe'
    campaign_info_csv = "38k_test.csv"

    campaign_info_df = pd.read_csv(campaign_info_csv)
    client_key = 'OFFICIAL_NAME'
    campaignId_key = 'CLIENT_CODE'
    lp_key = 'HOMEPAGE_URL'
    campaign_info_df = campaign_info_df.sort_values(by=campaignId_key)

    for i in range(5):
        timestamp = datetime.now().strftime("%d%m%Y_%H%M")
        save_all_dir = f"c{i+1}_{timestamp}"
        timeout_lp = []
        limit = [i*1000, (i+1)*1000]
        timeout_lp = crawl_image(chromeDriverPath, campaign_info_df, save_all_dir, client_key, campaignId_key, lp_key, limit)

        if timeout_lp is not None:
            with open(f'{save_all_dir}_timeout_lp.txt', 'w') as fp:
                for lp in timeout_lp:
                    # write each item on a new line
                    fp.write("%s\n" % lp)
