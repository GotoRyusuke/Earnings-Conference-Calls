import pandas as pd
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'utils.log'),
        logging.StreamHandler()
    ]
)

def raw_content_dir_decoder(file_dir):
    extension = file_dir.split('.')[-1]
    if extension == 'csv':
        return pd.read_csv
    elif extension =='parquet':
        return pd.read_parquet
    elif extension in ['xlsx', 'xls']:
        return pd.read_excel
    elif extension == 'dta':
        return pd.read_stata
    else:
        logging.warning('Please save as a file in the following format: .csv, .parquet, .xlsx, .xls, or .dta.')

def load_UA_list(ua_list_dir):
    with open(ua_list_dir, 'r') as f:
        ua_list = f.readlines()
    return [ua.strip() for ua in ua_list]



