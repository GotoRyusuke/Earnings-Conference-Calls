# -*- coding: utf-8 -*-

from HTMLCrawler import RawHTMLCrawler
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
#output.to_parquet('../test file.parquet')

# Test HTMLRawContentsSaver module on `AAPL`-----------------------------------
# Suppose you have crawled all records of AAPL in the last step and saved it
# to a .parquet file

from Savers import HTMLRawContentsSaver

user_agent_list_dir = '../user_agent_list.txt'
save_master_dir = '../Data_rawHTML'
raw_content_df_dir = '../test file.parquet'

saver = HTMLRawContentsSaver(
    user_agent_list_dir=user_agent_list_dir, 
    save_master_dir=save_master_dir,
    raw_content_df_dir=raw_content_df_dir,
    )
saver.save_by_tic('AAPL')
saver.raw_df.to_parquet('../test file raw html 2.parquet')

# Test MP3Saver module on `AAPL` ----------------------------------------------

from Savers import MP3Saver

user_agent_list_dir = '../user_agent_list.txt'
save_master_dir = '../Data_rawMP3'
raw_content_df_dir = '../test file.parquet'

saver = MP3Saver(
    user_agent_list_dir=user_agent_list_dir, 
    save_master_dir=save_master_dir,
    raw_content_df_dir=raw_content_df_dir,
    )

saver.save_by_tic('AAPL')
check_df = saver.raw_df
check_df.to_parquet('../test file raw mp3.parquet')

# Test HTMLContentsOrganiser --------------------------------------------------

from Parsers import HTMLContentsOrganiser

save_master_dir = '../Data_rawHTML'
local_dir_df_dir = '../test file raw HTML.parquet'
speech_master_dir = '../Data_speeches'

processor = HTMLContentsOrganiser(
    save_master_dir=save_master_dir,
    local_dir_df_dir=local_dir_df_dir, 
    speech_master_dir=speech_master_dir,
    )

df = processor.local_dir_df
indicator, dir_list = processor.process_single_tic('AAPL')

