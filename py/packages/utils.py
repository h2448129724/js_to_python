import os
import json
import datetime
import time
import pandas as pd

def get_date():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d")

def get_json_file_info(file_name):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump([], file)
        return []

def get_json_obj_file_info(file_name):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump({}, file)
        return {}

def write_json_to_file(file_name, json_data):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(json_data, file)

def get_json_from_excel(file_name):
    full_path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(full_path):
        df = pd.read_excel(full_path)
        return df.to_dict(orient='records')
    return []

def delayed(seconds):
    time.sleep(seconds)
