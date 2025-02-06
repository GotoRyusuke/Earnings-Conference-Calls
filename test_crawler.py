import os
os.chdir('C:/Users/niccolo/Desktop/SeekingAlpha/Earnings-Conference-Calls')

from SeekingAlphaCrawler import RawHTMLCrawler, organise_posting
import pandas as pd

tic_list = pd.read_csv('2021-2023_all-tickers_transcripts_url(refined).csv')['std_tic'].unique()

crawler = RawHTMLCrawler(tic_list=tic_list)

df = crawler.get_art_list_multi_tics(tic_start=651)
# stop at 608
# df = crawler.get_art_list_single_tic('BAC')
# SPB is missed for now

#df608 = crawler.df
#df620 = crawler.df
#df636 = crawler.df
# df638 = crawler.df

tic_list = list(tic_list)
tic_list.index('REFR')
