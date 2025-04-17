'''
Savers.py
│
├── Imports
│   ├── os
│   ├── time
│   ├── random
│   ├── logging
│   ├── requests
│   ├── webdriver from selenium
│   ├── BeautifulSoup from bs4
│   ├── Options from selenium.webdriver.chrome.options
│   ├── load_UA_list from utils
│   └── raw_content_dir_decoder from utils
│
├── Functions
│   ├── get_transcript_html(url)
│
└── Classes
    ├── HTMLRawContentsSaver
    │   ├── __init__(self, user_agent_list_dir, save_master_dir, raw_content_df_dir)
    │   ├── save_by_tic(self, tic)
    │   └── save(self)
    │
    └── MP3Saver
        ├── __init__(self, user_agent_list_dir, save_master_dir, raw_content_df_dir)
        ├── save_by_tic(self, tic)
'''

import os
import time
import random
import logging
import requests
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from utils import load_UA_list, raw_content_dir_decoder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'saver.log'),
        logging.StreamHandler()
    ]
)

'''
def get_transcript_html(url, user_agent):
    session = requests.Session()
    session.cookies.clear()
    headers = {'User-Agent': user_agent}

    trans_response = session.get(url, headers=headers)
    session.cookies.clear()

    session.close()
    return trans_response.text
'''

def get_transcript_html(url):
    count = 0
    while True:
        if count > 5: return None
        
        browser = webdriver.Edge
        options = Options()
        # options.add_argument('--incognito')
        driver = browser()#options=options)
        driver.delete_all_cookies()
        driver.get(url)

        time.sleep(5)
        html_content = driver.page_source
        driver.quit()
        driver.delete_all_cookies()
        soup = BeautifulSoup(html_content)

        if 'Create a free account' not in soup.text and \
            '确认您是人类' not in soup.text and \
            'we’ve hit a bottom.' not in soup.text:
            break
        # if len(html_content) > 670000:
        #     break
        else:
            time.sleep(random.randint(30, 45))
            count += 1
        
        return html_content
    

class HTMLRawContentsSaver:
    def __init__(
            self,
            user_agent_list_dir,
            save_master_dir,
            raw_content_df_dir,
            ):
        
        self.user_agent_list = load_UA_list(user_agent_list_dir)
        self.save_master_dir = save_master_dir

        decoder = raw_content_dir_decoder(raw_content_df_dir)  
        self.raw_df = decoder(raw_content_df_dir)
        self.raw_df['url'] = self.raw_df['url'].str.split('#source').str[0]
    
    def save_by_tic(self, tic):
        logging.info('-'*20)
        logging.info(f'TARGET TICKER: {tic}')
        tic_df = self.raw_df[self.raw_df['ticker'] == tic]
        local_folder_dir = '/'.join(
            [self.save_master_dir, tic]
            )
        os.makedirs(local_folder_dir, exist_ok=True)
        local_dir_list = []
        
        for idx in tic_df.index:
            title = tic_df.loc[idx, 'title']
            title = title.replace('/', '-')
            logging.info(f'Saving {title}')
            url = tic_df.loc[idx, 'url']
            
            local_dir = local_folder_dir + '/' + title + '.txt'
            local_dir_list.append(local_dir)
            
            while True:
                '''
                # deprecated
                trans_html = get_transcript_html(url, user_agent=random.choice(self.user_agent_list))
                if 'Press & Hold' not in trans_html:
                    break
                logging.warning('Encountered Press & Hold, retrying...')
                time.sleep(10)
                '''
                trans_html = get_transcript_html(url)

            with open(local_dir, 'w', encoding='u8') as f:
                f.write(trans_html)
            
            time.sleep(10)
        logging.info(f'END OF {tic}')
        self.raw_df.loc[tic_df.index, 'local_dir'] = local_dir_list
    
    def save(self):
        tic_list = self.raw_df['ticker'].drop_duplicates().to_list()
        
        for tic in tic_list:
            self.save_by_tic(tic)


class MP3Saver:
    def __init__(
            self,
            user_agent_list_dir,
            save_master_dir,
            raw_content_df_dir,
            ):
            
        self.user_agent_list = load_UA_list(user_agent_list_dir)
        self.save_master_dir = save_master_dir     
        self.raw_df = pd.read_parquet(raw_content_df_dir)  

        
    def save_by_tic(self, tic):
        logging.info(f'RETRIEVING MP3 FOR {tic}')
        tic_df = self.raw_df[self.raw_df['ticker'] == tic]
        tic_df['year'] = tic_df['date'].str.split('-').str[0].astype(int)
        tic_df = tic_df[tic_df['year'] > 2016]

        if len(tic_df) == 0: return None
        
        local_folder_dir = '/'.join(
            [self.save_master_dir, tic]
            )
        os.makedirs(local_folder_dir, exist_ok=True)
        local_dir_list = []
        
        keep_on = True
        start = list(tic_df.index)[0]
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
                tic_df.loc[idx, 'mp3_local_dir'] = local_dir
                logging.info(f'{tic}: {idx} in {start}-{end}')
                idx += 1 
            elif response.status_code == 404:
                idx += 1 
                logging.warning(f'No recording for {trans_id}')
            else:
                print(response.status_code)
                time.sleep(30)
             
            if idx > end:
                keep_on = False
            
            time.sleep(4)

        logging.info(f'END OF {tic}')
        tic_df.to_parquet(f'{local_folder_dir}/{tic}_recordings.parquet')