import os
import json
from datetime import datetime
import openpyxl

def get_date():
    now = datetime.now()
    return now.strftime("%Y-%m-%d")

def get_json_file_info(file_name):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in {file_name}: {e}")
            return None
    else:
        print(f"File {file_name} does not exist, creating it")
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump([], file)
            return []
        except IOError as e:
            print(f"Failed to create file {file_name}: {e}")
            return None

def get_json_obj_file_info(file_name):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in {file_name}: {e}")
            return None
    else:
        print(f"File {file_name} does not exist, creating it")
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump({}, file)
            return {}
        except IOError as e:
            print(f"Failed to create file {file_name}: {e}")
            return None

def write_json_to_file(file_name, json_data):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(json_data, file, ensure_ascii=False, indent=2)
        return f"File {file_name} written successfully"
    except IOError as e:
        return f"Failed to write to file {file_name}: {e}"

def get_json_from_excel(file_name):
    try:
        full_path = os.path.join(os.path.dirname(__file__), file_name)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File does not exist: {full_path}")

        workbook = openpyxl.load_workbook(full_path)
        worksheet = workbook.active
        json_data = list(worksheet.values)
        
        if json_data and len(json_data) > 0:
            title_list = json_data[0]
            title_count = len(title_list)
            data_list = json_data[1:]
            new_json_data = []
            
            for element in data_list:
                if element:
                    new_json_obj = {}
                    for index in range(title_count):
                        value = element[index] if index < len(element) else None
                        key = title_list[index]
                        new_key = get_key(key)
                        if new_key == "address" and value:
                            address_list = value.split(":")
                            if len(address_list) == 4:
                                new_json_obj["host"] = address_list[0]
                                new_json_obj["port"] = address_list[1]
                                new_json_obj["proxyUserName"] = address_list[2]
                                new_json_obj["proxyPassword"] = address_list[3]
                            else:
                                new_json_obj[new_key] = value
                        else:
                            new_json_obj[new_key] = value
                    new_json_data.append(new_json_obj)
            return new_json_data
        else:
            return []
    except Exception as e:
        print("File reading failed", e)
        return []

def get_key(key_text):
    key_mapping = {
        "账号": "userName",
        "密码": "password",
        "辅助邮箱": "remark",
        "socks5": "address",
        "号码": "phone",
        "内容": "message"
    }
    return key_mapping.get(key_text, key_text)

