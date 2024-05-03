
import os
import re
import time
import random 
import requests
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from utils import organise_posting, load_UA_list, get_transcript_html, organise_single_html
import warnings

warnings.filterwarnings('ignore')


class RawHTMLCrawler:
    def __init__(
            self,
            tic_list,
            ):
        
        self.tic_list = tic_list
        self.num_tics = len(tic_list)
    
    def get_art_list_single_tic(self, tic):
        print('-'*20)
        print(f'TARGET TICKER: {tic}')
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
                            print('-'*page, f'PAGE {page}')
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

        print('-'*page,'END')
        print('RECORDS FOUND: ', len(df))
        print('PAGES FOUND: ', page)
        return df
    
    def get_art_list_multi_tics(self, tic_start=0):
        print('///////// START SCRAPING ////////')
        print('#TICKERS: ', self.num_tics)
        print('START FROM: ', tic_start)

        tic_count = tic_start
        df = pd.DataFrame()
        
        for tic in self.tic_list[tic_start:]:
            
            tmp_df = self.get_art_list_single_tic(tic=tic)
            df = pd.concat([df, tmp_df])
            df.reset_index(drop=True, inplace=True)
            df.to_excel(f'Raw_backup_start{tic_start}.xlsx', index=False)

            print(f'TIC NO.{tic_count} FINISHED')
            print('#TICKERS LEFT: ', self.num_tics - tic_count)
            tic_count += 1

        return df


class HTMLRawContentsSaver:
    def __init__(
            self,
            user_agent_list_dir,
            store_master_dir,
            raw_content_df_dir,
            ):
        
        self.user_agent_list = load_UA_list(user_agent_list_dir)
        self.store_master_dir = store_master_dir     
        self.raw_df = pd.read_csv(raw_content_df_dir)
    
    def save_by_tic(self, tic):
        tic_df = self.raw_df[self.raw_df['std_tic'] == tic]
        local_folder_dir = '/'.join(
            [self.store_master_dir, tic]
            )
        os.makedirs(local_folder_dir, exist_ok=True)
        local_dir_list = []
        for idx in tic_df.index:
            title = tic_df.loc[idx, 'title']
            url = tic_df.loc[idx, 'url']
            
            local_dir = local_folder_dir + '/' + title + '.txt'
            local_dir_list.append(local_dir)
            trans_html = get_transcript_html(url, user_agent=random.choice(self.user_agent_list) )
            with open(local_dir, 'w', encoding='u8') as f:
                f.write(trans_html)
            
            time.sleep(3)
        
        self.raw_df.loc[tic_df.index, 'local_dir'] = local_dir_list
    
    def save(self):
        tic_list = self.raw_df['std_tic'].drop_duplicates().to_list()
        
        for tic in tic_list:
            self.save_by_tic(tic)


class MP3Saver:
    def __init__(
            self,
            user_agent_list_dir,
            store_master_dir,
            raw_content_df_dir,
            ):
            
        self.user_agent_list = load_UA_list(user_agent_list_dir)
        self.store_master_dir = store_master_dir     
        self.raw_df = pd.read_parquet(raw_content_df_dir)  
        
    def save_by_tic(self, tic):
        tic_df = self.raw_df[self.raw_df['ticker'] == tic]
        local_folder_dir = '/'.join(
            [self.store_master_dir, tic]
            )
        os.makedirs(local_folder_dir, exist_ok=True)
        local_dir_list = []
        
        keep_on = True
        start = list(tic_df.index)[0]+19
        end = list(tic_df.index)[-1]
        idx = start
        
        while keep_on == True:
            trans_id = tic_df.loc[idx, 'trans_id']
            mp3_url =  f'https://static.seekingalpha.com/cdn/s3/transcripts_audio/{trans_id}.mp3'
            
            response = requests.get(
                mp3_url,
                headers={'User-Agent':random.choice(self.user_agent_list)},
                )
            if response.status_code == 200:
                local_dir = '/'.join([local_folder_dir, f'{trans_id}.mp3'])
                local_dir_list.append(local_dir)
                with open(local_dir, "wb") as file:
                    file.write(response.content)
                self.raw_df.loc[idx, 'mp3_local_dir'] = local_dir
                print(f'{tic}: {idx} in {start}-{end}')
                idx += 1
            elif response.status_code == 404:
                idx += 1
                print(f'No recording for {trans_id}')
                
            if idx > end:
                keep_on = False
            
            time.sleep(4)


class HTMLContentsOrganiser:
    def __init__(
            self,
            save_master_dir,
            local_dir_df_dir,
            speech_master_dir,
            ):
        self.save_master_dir = save_master_dir
        self.local_dir_df = pd.read_csv(local_dir_df_dir)
        self.speech_master_dir = speech_master_dir
    
    def gen_local_dirs(self):
        for tic in tqdm(self.local_dir_df['tic'].drop_duplicates().to_list()):
            tic_df = self.local_dir_df[self.local_dir_df['tic'] == tic]
            local_folder_dir = '/'.join(
                [self.save_master_dir, tic]
                )
            local_dir_list = []
            if os.path.exists(local_folder_dir):
                saved_dir_list = os.listdir(local_folder_dir) 
            else: continue
        
            saved_idx_list = []
            
            for idx in tic_df.index:
                title = tic_df.loc[idx, 'title']
                title = title.replace('/', '(slash)')
                
                local_dir = local_folder_dir + '/' + title + '.txt'
                if title + '.txt' in saved_dir_list:
                    local_dir_list.append(local_dir)
                    saved_idx_list.append(idx)
            
            self.local_dir_df.loc[saved_idx_list, 'raw_dir'] = local_dir_list
        
    def process_single_tic(self, tic):
        tic_df = self.local_dir_df[self.local_dir_df['tic'] == tic]
        local_folder_dir = '/'.join(
            [self.speech_master_dir, tic]
            )
        os.makedirs(local_folder_dir, exist_ok=True)
        success = []
        success_dir_list = []
        for idx in tic_df.index:
            raw_dir = tic_df.loc[idx, 'raw_dir']
            title = tic_df.loc[idx, 'title']            
            with open(raw_dir, 'r', encoding='u8') as f:
                html = f.read()
            try:
                p_info_df, speech_df = organise_single_html(html)
                success.append(1)
                local_file_dir = local_folder_dir + '/' + title
                os.makedirs(local_file_dir, exist_ok=True)        
                p_info_df.to_csv(local_file_dir + '/participant_info.csv', index=False, encoding='u8')
                speech_df.to_csv(local_file_dir + '/speech.csv', index=False, encoding='u8')
                success_dir_list.append(local_file_dir)
            except:
                success.append(0)
                success_dir_list.append(None)
        return success, success_dir_list
    
    def process(self):
        self.local_dir_df.dropna(subset=['raw_dir'],inplace=True)
        tic_list = self.local_dir_df['tic'].drop_duplicates().to_list()

        for tic in tqdm(tic_list):
            success, success_dir_list = self.process_single_tic(tic)
            self.local_dir_df.loc[
                self.local_dir_df['tic'] == tic,
                'success'
                ] = success
            self.local_dir_df.loc[
                self.local_dir_df['tic'] == tic,
                'cleaned_dir'
                ] = success_dir_list
            
            
if __name__ == '__main__':

    
    ## test HTMLContentsOrganiser
    save_master_dir = 'F:/Seeking Alpha Crawler/raw_transcripts'
    local_dir_df_dir = './2021-2023_saved_transcripts.csv'
    speech_master_dir = 'F:/Seeking Alpha Crawler/cleaned data'

    organiser = HTMLContentsOrganiser(save_master_dir, local_dir_df_dir, speech_master_dir) 
    # test = organiser.process_single_tic('A')
    organiser.process()
    organiser.local_dir_df.to_csv('./2021-20223_cleaned_transcripts.csv', index=False)
    # organiser.local_dir_df.to_csv('F:/Seeking Alpha Crawler/second_round_local_dirs.csv', index=False)
    
    
    
