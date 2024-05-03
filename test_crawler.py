import os
os.chdir('C:/Users/76782/Documents/GitHub/Earnings-Conference-Calls')

from SeekingAlphaCrawler import RawHTMLCrawler, organise_posting
import pandas as pd

tic_list = pd.read_csv('2021-2023_all-tickers_transcripts_url(refined).csv')['std_tic'].unique()

crawler = RawHTMLCrawler(tic_list=tic_list)

df = crawler.get_art_list_multi_tics(tic_start=379)
# df = crawler.get_art_list_single_tic('BAC')
