from SeekingAlphaCrawler import RawHTMLCrawler
import requests

user_agent_list_dir = 'user_agents_list.txt'
crawler = RawHTMLCrawler(user_agent_list_dir=user_agent_list_dir)

tic = 'AAPL'
aapl_confcall_list = crawler.get_art_list_single_tic(tic=tic)
aapl_confcall_list.to_parquet('test_raw_df.parquet')

# test downloading mp3 files
from SeekingAlphaCrawler import MP3Saver

user_agent_list_dir = 'user_agents_list.txt'
raw_content_df_dir = 'test_raw_df.parquet'
store_master_dir = 'Data_ConfCallRecordings'

mp3_saver = MP3Saver(user_agent_list_dir, store_master_dir, raw_content_df_dir)
mp3_saver.save_by_tic('AAPL')

# export ticker list
import pandas as pd

tic_list = pd.read_csv('E:/Project_ScrapingSeekingAlpha/2021-2023_all-tickers_transcripts_url(refined).csv')['std_tic'].unique()
with open('E:/Project_ScrapingSeekingAlpha/TIC_list.txt', 'w') as f:
    f.writelines([tic+'\n' for tic in tic_list])
    

# get confcall list for a subsample of 10 tics
from SeekingAlphaCrawler import RawHTMLCrawler, organise_posting
import os

os.chdir('E:/Project_ScrapingSeekingAlpha')
user_agent_list_dir = 'user_agents_list.txt'
proxy_list = [
    '185.217.136.67',
    '50.222.245.45',
    '50.170.90.27',
    '50.223.38.6',
    ]

crawler = RawHTMLCrawler(
    user_agent_list_dir=user_agent_list_dir,
    #proxy_list=proxy_list,
    )



sample_tic_list = tic_list[10:12]
test_single = crawler.get_art_list_single_tic('AAPL')
test_df = crawler.get_art_list_multi_tics(tic_list=sample_tic_list)

# test_df.to_parquet('first_10tickers.parquet')

# try to use selenium
from selenium import webdriver
from bs4 import BeautifulSoup as BS

driver = webdriver.Edge()
url = 'https://seekingalpha.com/symbol/AMD/earnings/transcripts?page=2'
driver.get(url)
page_source = driver.page_source
soup = BS(page_source)
tmp_art_list = list(soup.findAll('article'))
test = organise_posting(tmp_art_list)
driver.close()

# 
import os
os.chdir('C:/Users/niccolo/Desktop/SeekingAlpha')

from SeekingAlphaCrawler import RawHTMLCrawler, organise_posting
import pandas as pd

tic_list = pd.read_csv('2021-2023_all-tickers_transcripts_url(refined).csv')['std_tic'].unique()
user_agent_list_dir = 'user_agents_list.txt'

crawler = RawHTMLCrawler()

df = crawler.get_art_list_multi_tics(tic_list=tic_list[379:])

