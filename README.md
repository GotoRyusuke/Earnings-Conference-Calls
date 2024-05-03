# Toolkit for Earnings Conference calls
This project provides modules for scraping [SeekingAlpha](https://seekingalpha.com/) along with processing transcripts and recordings (in `.mp3` format) scraped from the same website.
The workflow goes as:
1. Provided with a list of company tickers, a scraper module will go through all available records for each company in the list and identify earnings conference calls.
An `.xlsx` file will be created to store the information, including the title, year, quarter, URL, and unique transcript ID assigned by SeekingAlpha to each record.
2. Using the information in Step 1, specifically the URLs, transcripts and recordings (if any) can be downloaded using a saver module.
3. To be continued


# Updates
## (R6/05/03) Updates
The scraper module is now available for tests. Follow a [Test file](../test_crawler.py) to explore the functions. 
