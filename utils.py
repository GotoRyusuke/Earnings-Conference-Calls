import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

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