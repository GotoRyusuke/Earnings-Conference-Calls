'''
Parsers.py
│
├── Imports
│   ├── os
│   ├── re
│   ├── tqdm
│   ├── logging
│   ├── pandas as pd
│   ├── BeautifulSoup from bs4
│   └── raw_content_dir_decoder from utils
│
├── Functions
│   ├── find_strong_para(paras)
│   ├── organise_single_html(html_codes)
│   ├── convert_non_ascii(string)
│   ├── gen_name_title_pair(participant)
│   ├── extract_name_title_from_p(name_title_p_contents)
│   ├── gen_start_end_idx_dict(strong_paras_idx, trans_dict)
│   ├── gen_session_df(idx_dict, strong_paras_idx, paras, mode)
│   ├── gen_part_dict(idx_dict, paras, mode)
│   ├── organise_paragraphs(paras)
│   ├── gen_participant_info_df(participants_info)
│   ├── extract_participants(file_path)
│   ├── get_post_list(tree)
│   ├── process_post(post)
│   ├── process_html(file)
│   └──
└── Classes
    ├──CCHistoryOrganiser
    │  ├── __init__(self)
    │  ├── get_post_list(self, file)
    ├── HTMLContentsOrganiser
    │   ├── __init__(self, save_master_dir, local_dir_df_dir, speech_master_dir)
    │   ├── gen_local_dirs(self)
    │   ├── process_single_tic(self, tic)
    │   └── process(self)
    │
    └── TXTContentOrganiser
        ├── __init__(self, save_master_dir, local_dir_df_dir, speech_master_dir)
        └── process_single_tic(self, tic)
'''

import os
import re
import tqdm
import logging
import pandas as pd
from bs4 import BeautifulSoup
from utils import raw_content_dir_decoder
from dateutil import parser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'parsers.log'),
        logging.StreamHandler()
    ]
)

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

def extract_name_title_from_p(name_title_p_contents):
    name_title_dict = {}
    for name_title_pair in name_title_p_contents:
        if len(name_title_pair): # skip <br> tags
            name = name_title_pair.text.split('-')[0].strip()
            title = name_title_pair.text.split('-')[1].strip()
            name_title_dict[name] = title
    
    return name_title_dict

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

def gen_part_dict(idx_dict, paras, mode):
    # get company or conference call participants dict
    part_start_idx, part_end_idx = idx_dict[f'{mode} start'], idx_dict[f'{mode} end']
    if mode == 'others' and part_start_idx is None:
        return None
    else:
        participants_info = {}
        participants = [para for para in paras[part_start_idx+1:part_end_idx]]

        for part in participants:
            # name - title pairs can be included in a single <p> divided by <br>
            if '<br/>' in part.decode_contents():
                part = part.contents
                for person_name, person_title in extract_name_title_from_p(part).items():
                    participants_info[person_name] = person_title
            else:
                part = part.text
                person_name, person_title = gen_name_title_pair(part)
                participants_info[person_name] = person_title

        return participants_info

def organise_paragraphs(paras):
    strong_paras_idx = find_strong_para(paras)            
    trans_dict = dict(
        [(para_idx, para.text.strip()) for para_idx, para in enumerate(paras)]
        )
    participants_info = {}
    idx_dict = gen_start_end_idx_dict(strong_paras_idx, trans_dict)

    # get participants info df
    participants_info = {}
    for mode in ['company', 'others']:
        for name, title in gen_part_dict(idx_dict, paras, mode=mode).items():
            participants_info[name] = title
    participant_df = gen_participant_info_df(participants_info)
    
    # get session dfs
    md_session_df = gen_session_df(idx_dict, strong_paras_idx, paras, mode='md')
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

def extract_participants(file_path):
    participants = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        
        # Flag to indicate if we are in the participants section
        in_participants_section = False
        
        for line in lines:
            line = line.strip()
            # Check for the start of the Corporate Participants section
            if line == "Corporate Participants":
                in_participants_section = True
                continue
            # Check for the end of the participants section
            if line == "Conference Call Participiants":
                in_participants_section = False
                continue
            # If we are in the participants section, extract names and titles
            if in_participants_section and line:
                participants.append(line)
    
    return participants

def get_post_list(tree):
    return tree.find('div', attrs={'data-test-id':'post-list'}).find_all('article')

def process_post(post):
    # find transcript title
    title = post.find('h3').text
    # find transcript url
    url = post.find('h3').find('a').get('data-savepage-href').split('#source')[0]
    # find transcript ID
    transcript_id = int(url.split('-')[0].replace('/article/', '').strip())
    # find ticker
    try:
        ticker = post.find('footer').find('a', attrs={'data-test-id':'post-list-ticker'}).text
    except AttributeError:
        ticker = 'missing'
    # find post date
    post_date = post.find('footer').find('span', attrs={'data-test-id':'post-list-date'}).text
    try:
        post_date = parser.parse(post_date).strftime("%Y-%m-%d")
    except:
        pass
    
    return {
        'title': title,
        'url': url,
        'ID': transcript_id,
        'ticker': ticker,
        'date': post_date,
        }

def process_html(file):
    with open(file, 'r', encoding='u8') as f:
        content = f.read()
    
    tree = BS(content, features="lxml")
    post_list = get_post_list(tree)
    post_df = pd.DataFrame(
        columns=['ticker', 'ID', 'date', 'title', 'url', 'filename'],
        index=range(len(post_list))
        )
    
    for idx in post_df.index:
        for key, item in process_post(post_list[idx]).items():
            post_df.loc[idx, key] = item
    
    post_df['filename'] = file

class CCHistoryOrganiser:
    def __init__(self):
        pass

    def get_post_list(self, file):
        return process_html(file)


class HTMLContentsOrganiser:
    def __init__(
            self,
            save_master_dir,
            local_dir_df_dir,
            speech_master_dir,
            ):
        self.save_master_dir = save_master_dir
        decoder = raw_content_dir_decoder(local_dir_df_dir)
        self.local_dir_df = decoder(local_dir_df_dir)
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
        tic_df = self.local_dir_df[self.local_dir_df['ticker'] == tic]
        local_folder_dir = '/'.join(
            [self.speech_master_dir, tic]
            )
        os.makedirs(local_folder_dir, exist_ok=True)
        success = []
        success_dir_list = []

        logging.info(f'{len(tic_df)} FILES IN TOTAL')
        for idx in tic_df.index:
            raw_dir = tic_df.loc[idx, 'local_dir']
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
            

class TXTContentOrganiser:
    def __inti__(self,
            save_master_dir,
            local_dir_df_dir,
            speech_master_dir,
            ):
        self.save_master_dir = save_master_dir
        decoder = raw_content_dir_decoder(local_dir_df_dir)
        self.local_dir_df = decoder(local_dir_df_dir)
        self.speech_master_dir = speech_master_dir
    
    def process_single_tic(self, tic):
        tic_df = self.local_dir_df[self.local_dir_df['ticker'] == tic]
        local_folder_dir = '/'.join(
            [self.speech_master_dir, tic]
            )
        os.makedirs(local_folder_dir, exist_ok=True)
        success = []
        success_dir_list = []