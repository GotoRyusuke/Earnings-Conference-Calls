# -*- coding: utf-8 -*-

from SeekingAlphaCrawler import RawHTMLCrawler
import pandas as pd

# Test RawHTMLCralwer module on `AAPL`-----------------------------------------

## You can initialize the crawler module with a list of TICs
# panel = pd.read_csv('../2021-2023_all-tickers_transcripts_url(refined).csv')
# tic_list = panel['std_tic'].unique()
# crawler = RawHTMLCrawler(tic_lis=tic_list)
# output = crawler.get_art_list_multi_tics()

# Else if you want to try on a single TIC
crawler = RawHTMLCrawler()
output = crawler.get_art_list_single_tic('AAPL')
output.to_parquet('../test file.parquet')

# Test HTMLRawContentsSaver module on `AAPL`-----------------------------------
# Suppose you have crawled all records of AAPL in the last step and saved it
# to a .parquet file

from SeekingAlphaCrawler import HTMLRawContentsSaver

user_agent_list_dir = '../user_agent_list.txt'
store_master_dir = '../Data_rawHTML'
raw_content_df_dir = '../test file.parquet'

saver = HTMLRawContentsSaver(
    user_agent_list_dir=user_agent_list_dir, 
    store_master_dir=store_master_dir,
    raw_content_df_dir=raw_content_df_dir,
    )

saver.save_by_tic('AAPL')
saver.raw_df.to_parquet('../test file raw html.parquet')


