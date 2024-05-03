
import os
import re
import time
import random 
import requests
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver


def load_UA_list(ua_list_dir):
    with open(ua_list_dir, 'r') as f:
        ua_list = f.readlines()
    return [ua.strip() for ua in ua_list]

def get_transcript_html(url, user_agent):
    headers = {'User-Agent': user_agent}
    trans_response = requests.get(url, headers=headers)
    return trans_response.text

def find_strong_para(paras):
    strong_paras_idx = []
    for p_i, p in enumerate(paras):
        for sub_tag in p.find_all():
            if 'strong' in sub_tag.name:
                strong_paras_idx.append(p_i)
                break
    return strong_paras_idx

def organise_single_html(html_codes):
        
    soup = BeautifulSoup(html_codes, 'html.parser')
    container = soup.find('div', attrs={'data-test-id': 'content-container'})
    paras = container.find_all('p')
    
    return organise_paragraphs(paras)

def convert_non_ascii(string):
    return re.sub(r'[^\x00-\x7F]+', '-', string)

def gen_name_title_pair(participant):
    participant = convert_non_ascii(participant)
    part_pairs = participant.split('-')
    person_name = part_pairs[0]
    if len(part_pairs) == 1:
        person_title = None
    else:
        person_title = part_pairs[1]
    
    if person_title is not None:
        person_title = person_title.strip()
    
    return person_name.strip(), person_title

def gen_start_end_idx_dict(strong_paras_idx, trans_dict):
    trans_value_list = [value.lower() for value in trans_dict.values()]
    
    # get MD start index
    if 'operator' in trans_value_list:
        md_start_idx = [
            idx
            for idx in strong_paras_idx
            if trans_dict[idx].lower() == 'operator'
            ][0]
    else:
        if 'analysts' in trans_value_list or 'conference call participants' in trans_value_list:
            md_start_idx = strong_paras_idx[2]
        else:
            md_start_idx = strong_paras_idx[1]

    # get company participants and analysts start and end indices
    if 'analysts' in trans_value_list:
        comp_part_start_idx = [
            idx 
            for idx in strong_paras_idx 
            if trans_dict[idx].lower() == 'participants'
            ][0]
        confcall_part_start_idx = [
            idx 
            for idx in strong_paras_idx 
            if trans_dict[idx].lower() == 'analysts'
            ][0]
        confcall_part_end_idx = strong_paras_idx[
            strong_paras_idx.index(confcall_part_start_idx)+1
            ]
        comp_part_end_idx = confcall_part_start_idx

    else:
        comp_part_start_idx = [
            idx 
            for idx in strong_paras_idx 
            if 'company' in trans_dict[idx].lower() or 'corporate' in trans_dict[idx].lower()
            ][0]
        if 'conference call participants' in trans_value_list:
            confcall_part_start_idx = [idx for idx in strong_paras_idx if trans_dict[idx].lower() == 'conference call participants'][0]
            confcall_part_end_idx = strong_paras_idx[strong_paras_idx.index(confcall_part_start_idx)+1]
            comp_part_end_idx = confcall_part_start_idx
        else:
            confcall_part_start_idx, confcall_part_end_idx = None, None
            comp_part_end_idx = md_start_idx
        
    if 'question-and-answer session' in trans_value_list:
        md_end_idx = [idx for idx in strong_paras_idx if trans_dict[idx].lower() == 'question-and-answer session'][0]
        qa_start_idx = md_end_idx + 1
        qa_end_idx = len(trans_dict) - 1
    else:
        md_end_idx = len(trans_dict) - 1
        qa_start_idx, qa_end_idx = None, None
    
    return {
        'company start': comp_part_start_idx,
        'company end': comp_part_end_idx,
        'others start': confcall_part_start_idx,
        'others end': confcall_part_end_idx,
        'md start': md_start_idx,
        'md end': md_end_idx,
        'qa start': qa_start_idx,
        'qa end': qa_end_idx,
        }
        
def gen_session_df(idx_dict,strong_paras_idx, paras, mode):
    start_idx, end_idx = idx_dict[f'{mode} start'], idx_dict[f'{mode} end']
    if start_idx is None:
        return pd.DataFrame()

    session_df = pd.DataFrame(
        columns=['speech_idx', 'name', 'speech'],
        index=range(start_idx, end_idx)
        )
    session_idx_list = [idx for idx in range(len(paras)) if idx >= start_idx and idx < end_idx]
    strong_idx_list = [idx for idx in strong_paras_idx if idx in session_idx_list]
    
    for strong_i, para_idx in enumerate(strong_idx_list):
        person = paras[para_idx].text.split('-')[-1].strip()
        person_start_idx = para_idx + 1
        
        if len(strong_idx_list) - strong_i == 1:
            person_end_idx = end_idx
        else:
            person_end_idx = strong_idx_list[strong_i + 1]
        
        for idx in range(person_start_idx, person_end_idx):
            session_df.loc[idx, 'speech_idx'] = idx
            session_df.loc[idx, 'speech'] = paras[idx].text
        
        session_df.loc[person_start_idx:person_end_idx, 'name'] = person
    session_df.dropna(subset=['speech'], inplace=True)
    session_df['session'] = mode.upper()
    
    return session_df
    
def organise_paragraphs(paras):
    strong_paras_idx = find_strong_para(paras)            
    trans_dict = dict(
        [(para_idx, para.text.strip()) for para_idx, para in enumerate(paras)]
        )
    participants_info = {}
    idx_dict = gen_start_end_idx_dict(strong_paras_idx, trans_dict)
    
    # get participants info
    comp_part_start_idx, comp_part_end_idx = idx_dict['company start'], idx_dict['company end']
    comp_participants = [para.text for para in paras[comp_part_start_idx+1:comp_part_end_idx]]
    for comp_part in comp_participants:
        person_name, person_title = gen_name_title_pair(comp_part)
        participants_info[person_name] = person_title
        
    confcall_part_start_idx, confcall_part_end_idx = idx_dict['others start'], idx_dict['others end']
    if confcall_part_start_idx is not None:
        confcall_participants = [para.text for para in paras[confcall_part_start_idx+1:confcall_part_end_idx]]
        for confcall_part in confcall_participants:
            person_name, person_affiliation = gen_name_title_pair(confcall_part)
            participants_info[person_name] = person_affiliation        
        
    participant_df = gen_participant_info_df(participants_info)
    
    # get md session df
    md_session_df = gen_session_df(idx_dict, strong_paras_idx, paras, mode='md')
    
    # get qa session df 
    qa_session_df = gen_session_df(idx_dict, strong_paras_idx, paras, mode='qa')
    speech_df = pd.concat([md_session_df, qa_session_df])
    
    return participant_df, speech_df

def gen_participant_info_df(participants_info):       
    p_info_df = pd.DataFrame(
        columns=['name', 'title/affiliation']
        )
    p_info_df_idx = 0
    for name, title in participants_info.items():
        p_info_df.loc[p_info_df_idx, 'name'] = name
        p_info_df.loc[p_info_df_idx, 'title/affiliation'] = title
        p_info_df_idx += 1
    
    return p_info_df

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
            #user_agent_list_dir,
            #proxy_list,
            ):
        pass
        #self.user_agent_list = load_UA_list(user_agent_list_dir)
        #self.proxy_list = proxy_list
    
    def get_art_list_single_tic(self, tic):
        url = f'https://seekingalpha.com/symbol/{tic}/earnings/transcripts'
        df = pd.DataFrame()
        keep_on = True
        page = 1

        #session = requests.Session() 
        # start scraping
        driver = webdriver.Edge()
        while keep_on:
            print(f'page={page}')
            url = f'https://seekingalpha.com/symbol/{tic}/earnings/transcripts?page={page}'
            #session.headers.update({'User-Agent':random.choice(self.user_agent_list)})
            '''
            response = requests.get(
                url,
                headers={'User-Agent':random.choice(self.user_agent_list)},
                #proxies={'http':random.choice(self.proxy_list)}
                )
            soup = BeautifulSoup(response.content, "html.parser")
            '''
            driver.get(url)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source)

            time.sleep(5)
            if 'denied' not in soup.text.lower() and '确认您是人类' not in soup.text:
                if 'we’ve hit a bottom' in soup.text.lower():
                    keep_on = False
                    driver.close()
                # and 'ad-blocker enabled' not in soup.text.lower()
                else:
                    post_list = soup.find(name='div', attrs={'data-test-id':'post-list'})
                    if post_list is not None:
                        print('found')
                        tmp_art_list = list(post_list.findAll('article'))
                        if len(tmp_art_list) != 0:
                            tmp_df = organise_posting(art_list=tmp_art_list)
                            df = pd.concat([df, tmp_df])
                            page += 1
                        else:
                            keep_on = False
                            driver.close()
                    else:
                        driver.close()
                        driver = webdriver.Edge()
                        continue                
            else:
                print(soup.text.strip())
                driver.close()
                driver = webdriver.Edge()

                continue
        df['ticker'] = tic
        return df
    
    def get_art_list_multi_tics(self, tic_list, tic_start=0):
        # df = pd.DataFrame()
        # for tic in tqdm(tic_list):
        #     print(f'start {tic}')
        #     try:
        #         tic_df = self.get_art_list_single_tic(tic)
        #         df = pd.concat([df, tic_df])
        #         time.sleep(2)
        #     except:
        #         print(f'stop at {tic}')
        #         return df    
            
        tic_count = 0
        df = pd.DataFrame()

        with tqdm (total=len(tic_list) - tic_start) as t:
            while tqdm(tic_count < len(tic_list) - tic_start):
                tic = tic_list[tic_start + tic_count]
                tic_df = self.get_art_list_single_tic(tic)
                df = pd.concat([df, tic_df])
                tic_count += 1
                t.update()

                df.to_excel('Raw_backup.xlsx', index=False)
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
    
    
    
