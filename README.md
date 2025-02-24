# Toolkit for Earnings Conference calls
This project provides modules for scraping [SeekingAlpha](https://seekingalpha.com/) along with processing transcripts and recordings (in `.mp3` format) scraped from the same website.
The workflow goes as:
1. Provided with a list of company tickers (optional), the [`RawHTMLCrawler`](https://github.com/GotoRyusuke/Earnings-Conference-Calls/blob/main/SeekingAlphaCrawler.py#L82) module will go through all available records for each company in the list and identify earnings conference calls.
An `.xlsx` file will be created to store the information, including the title, year, quarter, URL, and unique transcript ID assigned by SeekingAlpha to each record.
2. Using the information in Step 1, especifically the URLs, *transcripts* and *recordings* (if any) can be downloaded using the `HTMLRawContentsSaver`(./SeekingALphaCrawler.py#L173) and the [`MP3Saver`](https://github.com/GotoRyusuke/Earnings-Conference-Calls/blob/main/SeekingAlphaCrawler.py#L225) module, respectively.
3. After saving HTML files of transcripts of conference calls, you can use the [`HTMLContentsOrganiser`](https://github.com/GotoRyusuke/Earnings-Conference-Calls/blob/main/SeekingAlphaCrawler.py#L276) to get preprocessed transcripts of all these conference calls

# Updates
## (R7/02/24) Updates
Several collaps are solved. Loggings are now available to track the working status.
## (R6/05/03) Updates
The scraper module is now available for tests. Follow a [`test file`](test.py) to explore the modules.

# Structure
## SeekingAlphaCrawler
### RawHTMLCrawler
- Handles the initial crawling of earnings call transcripts
- Methods:
  - `get_art_list_single_tic(tic)`: Crawls transcripts for a single ticker
  - `get_art_list_multi_tics(tic_list, tic_start)`: Crawls transcripts for multiple tickers

### HTMLRawContentsSaver
- Saves raw HTML content from crawled transcripts
- Methods:
  - `save_by_tic(tic)`: Saves content for a single ticker
  - `save()`: Saves content for all tickers

### MP3Saver
- Downloads and saves MP3 recordings of earnings calls
- Methods:
  - `save_by_tic(tic)`: Downloads MP3s for a single ticker

### HTMLContentsOrganiser
- Processes and organizes the crawled HTML content
- Methods:
  - `gen_local_dirs()`: Generates local directory structure
  - `process_single_tic(tic)`: Processes content for a single ticker
  - `process()`: Processes content for all tickers

## Dependencies

- Standard Library:
  - os
  - re
  - time
  - random
  - warnings
  - logging

- Third-party:
  - requests
  - pandas
  - tqdm
  - BeautifulSoup
  - selenium.webdriver

## utils
### File Operations
- `raw_content_dir_decoder`: Supports .csv, .parquet, .xlsx, .xls, .dta formats
- `load_UA_list`: Reads and cleans user agent list from file

### Web Scraping
- `get_transcript_html`: Makes HTTP requests with rotating user agents
- `find_strong_para`: Identifies important paragraph markers in HTML

### Text Processing
- `convert_non_ascii`: Sanitizes text for consistent processing
- `gen_name_title_pair`: Parses participant information

### HTML Organization
- `organise_single_html`: Coordinates overall HTML processing
- `organise_paragraphs`: Structures transcript content

### Index Management
- `gen_start_end_idx_dict`: Maps transcript sections:
  - Company participants
  - Conference call participants
  - Management Discussion (MD)
  - Q&A sections

### DataFrame Generation
- `gen_session_df`: Creates structured data for MD and Q&A sections
- `gen_participant_info_df`: Organizes participant information
- `organise_posting`: Processes transcript metadata including:
  - Ticker
  - Title
  - Year
  - Quarter
  - Date
  - URL
  - Transcript ID



