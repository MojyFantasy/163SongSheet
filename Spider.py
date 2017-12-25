# coding: utf-8
import json
import traceback
from multiprocessing.pool import Pool
from urllib.parse import urlencode

import pymongo
import re
import requests
from bs4 import BeautifulSoup as bs

from config import MONGO_TABLE, MONGO_URL, MONGO_DB

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


def get_page_content(url, offset):
    headers = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) " \
              "Chrome/63.0.3239.108 Safari/537.36"
    data = {
        'order': 'hot',
        'cat': '全部',
        'limit': 35,
        'offset': offset
    }
    try:
        response = requests.get(url+urlencode(data))
        if response.status_code == 200:
            return response.content
    except:
        print(traceback.format_exc())
    return None


def parse_page_data(content):
    soup = bs(content, "lxml")
    ul_ele = soup.select("#m-pl-container")[0]
    li_ele_lst = ul_ele.find_all("li")
    for li_ele in li_ele_lst:
        # print(li_ele)
        img_ele = li_ele.select(".j-flag")[0]
        img_link = img_ele['src']
        detail_link = li_ele.select(".msk")[0]['href']
        name = li_ele.select(".msk")[0]['title']
        play_total = int(str(li_ele.select(".nb")[0].string).replace("万", "0000"))
        author = li_ele.select(".s-fc3")[0].string
        yield {
            'img_link': img_link,
            'detail_link': detail_link,
            'name': name,
            'play_total': play_total,
            'author': author
        }


def download_picture(url, pic_name):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            pic_name = re.sub('[\<\>\/\\\|\:\"\*\?]', ' ', pic_name)
            with open(r'pictures/{}.jpg'.format(pic_name), 'wb') as fp:
                fp.write(response.content)
            print("图片下载成功 ", pic_name)
    except:
        print(traceback.format_exc())
        print("图片下载失败！", pic_name, url)


def save_to_db(result):
    if db[MONGO_TABLE].insert(result):
        print("存储数据到MONGODB成功！", result)
        return True
    return False


def main(offset):
    url = "https://music.163.com/discover/playlist/?"
    content = get_page_content(url, offset)
    count = 0
    for item in parse_page_data(content):
        count += 1
        if save_to_db(item):
            download_picture(item['img_link'], item['name'])
    print(count)


if __name__ == '__main__':
    pool = Pool()
    pool.map(main, [x*35 for x in range(37)])
