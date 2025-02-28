# Toolkit for Earnings Conference calls
This project provides modules for scraping [SeekingAlpha](https://seekingalpha.com/) along with processing transcripts and recordings (in `.mp3` format) scraped from the same website.
The workflow goes as:
1. Provided with a list of company tickers (optional), the [`RawHTMLCrawler`](https://github.com/GotoRyusuke/Earnings-Conference-Calls/blob/main/HTMLCrawler.py#L82) module will go through all available records for each company in the list and identify earnings conference calls.
An `.xlsx` file will be created to store the information, including the title, year, quarter, URL, and unique transcript ID assigned by SeekingAlpha to each record.
2. Using the information in Step 1, especifically the URLs, *transcripts* and *recordings* (if any) can be downloaded using the ~~[`HTMLRawContentsSaver`](https://github.com/GotoRyusuke/Earnings-Conference-Calls/blob/main/Savers.py#L173)~~(**not recommeded**) and the [`MP3Saver`](https://github.com/GotoRyusuke/Earnings-Conference-Calls/blob/main/Savers.py#L225) module, respectively.
3. **(Refer to R70225 Updates for the lastest instruction)** After saving HTML files of transcripts of conference calls, you can use the [`HTMLContentsOrganiser`](https://github.com/GotoRyusuke/Earnings-Conference-Calls/blob/main/Parsers.py#L276) to get preprocessed transcripts of all these conference calls.
4. Alternatively, if have access to LSEG, you can follow my lastest progress on a module to parse transcritps downloaded from there. See [`TXTContentOrganiser`](https://github.com/GotoRyusuke/Earnings-Conference-Calls/blob/main/Parsers.py#L356). 

# Updates
## (R7/02/25) Updates
1. The strucutre of the project are reorganised for simplicity. Refer to the structure below for details.
2. Due to the ungraded security on SA pages, full contents are no longer accessible for visitors. Major parts of a transcript are now blocked by a paywall. Therefore, I would not recommend `HTMLRaWContentsSaver` for scraping transcripts because it cannot capture the full content. You can either resort to another database for this data or subscribe SA contents for unlimitted access. The `MP3Saver` and `RawHTMLCrawler` still work fine, so you can use them to retrieve panel information and call recordings.

I am working on a new module to parse transcripts downloaded from [LSEG](https://www.lseg.com/en/data-analytics/refinitiv) AdvEvent Search app. If you have access to this database, you can follow the latest progress on it.

## (R7/02/24) Updates
Several collapses are solved. Loggings are now available to track the working status.
## (R6/05/03) Updates
The scraper module is now available for tests. Follow a [`test file`](test.py) to explore the modules.

# Structure
```
Project Root
│
├── Savers.py
│ ├── Functions
│ │ └── get_transcript_html(url)
│ │
│ └── Classes
│ ├── HTMLRawContentsSaver
│ │ ├── init(self, user_agent_list_dir, save_master_dir, raw_content_df_dir)
│ │ ├── save_by_tic(self, tic)
│ │ └── save(self)
│ │
│ └── MP3Saver
│ ├── init(self, user_agent_list_dir, save_master_dir, raw_content_df_dir)
│ └── save_by_tic(self, tic)
│
├── Parsers.py
│ ├── Functions
│ │ ├── find_strong_para(paras)
│ │ ├── organise_single_html(html_codes)
│ │ ├── convert_non_ascii(string)
│ │ ├── gen_name_title_pair(participant)
│ │ ├── extract_name_title_from_p(name_title_p_contents)
│ │ ├── gen_start_end_idx_dict(strong_paras_idx, trans_dict)
│ │ ├── gen_session_df(idx_dict, strong_paras_idx, paras, mode)
│ │ ├── gen_part_dict(idx_dict, paras, mode)
│ │ ├── organise_paragraphs(paras)
│ │ ├── gen_participant_info_df(participants_info)
│ │ └── extract_participants(file_path)
│ │
│ └── Classes
│ ├── HTMLContentsOrganiser
│ │ ├── init(self, save_master_dir, local_dir_df_dir, speech_master_dir)
│ │ ├── gen_local_dirs(self)
│ │ ├── process_single_tic(self, tic)
│ │ └── process(self)
│ │
│ └── TXTContentOrganiser
│ ├── init(self, save_master_dir, local_dir_df_dir, speech_master_dir)
│ └── process_single_tic(self, tic)
│
├── HTMLCrawlers.py
│ ├── Functions
│ │ ├── crawl_html(url)
│ │ └── parse_html(content)
│ │
│ └── Classes
│ ├── HTMLCrawler
│ │ ├── init(self, base_url)
│ │ ├── fetch_page(self, page_url)
│ │ └── extract_data(self, html_content)
│
└── utils.py
│ ├── Functions
│ ├── load_UA_list(file_path)
│ └── raw_content_dir_decoder(local_dir_df_dir)
```



