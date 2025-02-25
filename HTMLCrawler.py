import re
import time
import logging
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

def organise_posting(art_list):
    # organise scraped contents
    master_url = 'https://seekingalpha.com'
    trans_df = pd.DataFrame(
        columns=['ticker', 'title', 'year', 'quarter', 'date', 'url']
        )

    df_idx = 0

    for art in art_list:
        # get url and full url for a single article
        ref = art.find('a', attrs={'data-test-id': 'post-list-item-title'}).get('href')
        full_url = master_url + ref
        
        # get tittle of the article
        title = art.find('a', attrs={'data-test-id': 'post-list-item-title'}).text
        if 'Call Transcript' not in title: continue 
    
        pattern_q = r'\s?Q[1-4]\s?|[Ff]\s?[1-4]Q\s?'
        pattern_y = r'20\d{2}|[Ff][1-4]Q\d{2}'
        #pattern_tic = r'\(([a-zA-Z]+)\)'
        
        quarter = re.findall(pattern_q, title)
        if len(quarter) == 0:
            quarter = None
        else:
            quarter = quarter[0].strip().replace('Q', '').replace('F', '')
            
        year = re.findall(pattern_y, title)
        if len(year) == 0:
            year = None
        else:
            year = year[0].strip()
            if 'Q' in year:
                year = '20' + year[-2:] 
            
        # if year not in ['2021', '2022', '2023']: continue    
        # std_tic = re.findall(pattern_tic, title)[0].strip()
            
        # get post date of the article
        post_date = art.find('span', attrs={'data-test-id': 'post-list-date'}).text
        
        # fill df with necessary info
        trans_df.loc[df_idx, 'title'] = title
        trans_df.loc[df_idx, 'year'] = year
        trans_df.loc[df_idx, 'quarter'] = quarter
        trans_df.loc[df_idx, 'date'] = post_date
        trans_df.loc[df_idx, 'url'] = full_url
        # trans_df.loc[df_idx, 'std_tic'] = std_tic
        
        df_idx += 1   
    # create a new column for transcript id from transcript url
    # sample transcript url: https://seekingalpha.com/article/4666956-apple-inc-aapl-q1-2024-earnings-call-transcript?source=content_type%3Areact%7Csection%3ATranscripts%7Csection_asset%3ATranscripts%7Cfirst_level_url%3Asymbol%7Cbutton%3ATitle%7Clock_status%3ANo%7Cline%3A1
    trans_df['trans_id'] = trans_df['url'].str.split('article/').str[1].str.split('-').str[0]

    return trans_df


class RawHTMLCrawler:
    def __init__(
            self,
            tic_list=None,
            ):
        
        if tic_list:
            self.tic_list = tic_list
            self.num_tics = len(tic_list)
        else:
            logging.info('Initialised without TICs')
    
    def get_art_list_single_tic(self, tic):
        logging.info('-'*20)
        logging.info(f'TARGET TICKER: {tic}')
        url = f'https://seekingalpha.com/symbol/{tic}/earnings/transcripts'
        df = pd.DataFrame()
        keep_on = True
        page = 1

        # start scraping
        driver = webdriver.Edge()
        while keep_on:
            url = f'https://seekingalpha.com/symbol/{tic}/earnings/transcripts?page={page}'
            
            driver.get(url)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source)

            time.sleep(5)
            if 'denied' not in soup.text.lower() and '确认您是人类' not in soup.text:
                if 'we’ve hit a bottom' in soup.text.lower():
                    keep_on = False
                    driver.close()
                else:
                    post_list = soup.find(name='div', attrs={'data-test-id':'post-list'})
                    if post_list is not None:
                        tmp_art_list = list(post_list.findAll('article'))
                        if len(tmp_art_list) != 0:
                            tmp_df = organise_posting(art_list=tmp_art_list)
                            df = pd.concat([df, tmp_df])
                            logging.info('-'*page+f'PAGE {page}')
                            page += 1
                        else:
                            keep_on = False
                            driver.close()
                    else:
                        driver.close()
                        driver = webdriver.Edge()
                        continue                
            else:
                driver.close()
                driver = webdriver.Edge()

                continue
        df['ticker'] = tic
        df = df.sort_values(by=['year', 'quarter']).reset_index(drop=True)

        logging.info('-'*page+'END')
        logging.info(f'RECORDS FOUND: {len(df)}')
        logging.info(f'PAGES FOUND: {page-1}')

        return df
    
    def get_art_list_multi_tics(self, tic_list=None, tic_start=0):
        if self.tic_list:
            tic_list = self.tic_list
        num_tics = len(tic_list)

        logging.info('///////// START SCRAPING ////////')
        logging.info('#TICKERS: ', self.num_tics)
        logging.info('START FROM: ', tic_start)

        tic_count = tic_start
        df = pd.DataFrame()
        
        for tic in tic_list[tic_start:]:
            
            tmp_df = self.get_art_list_single_tic(tic=tic)
            df = pd.concat([df, tmp_df])
            df.reset_index(drop=True, inplace=True)
            df.to_excel(f'Raw_backup_start{tic_start}.xlsx', index=False)

            logging.info(f'TIC NO.{tic_count} FINISHED')
            logging.info(f'#TICKERS LEFT: {num_tics - tic_count}', )
            tic_count += 1

            self.df = df
        return df