import requests

baseURL = "http://127.0.0.1:54345"

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json"
})

def request(method, url, data=None):
    response = session.request(method, f"{baseURL}{url}", json=data)
    response.raise_for_status()
    return response.json()

def open_browser(data):
    return request("POST", "/browser/open", data)

def close_browser(id):
    return request("POST", "/browser/close", {"id": id})

def create_browser(data):
    return request("POST", "/browser/update", data)

def delete_browser(id):
    return request("POST", "/browser/delete", {"id": id})

def get_browser_detail(id):
    return request("POST", "/browser/detail", {"id": id})

def get_browser_list(data):
    return request("POST", "/browser/list", data)

def get_group_list(page, page_size):
    return request("POST", "/group/list", {"page": page, "pageSize": page_size})

def add_group(group_name, sort_num):
    return request("POST", "/group/add", {"groupName": group_name, "sortNum": sort_num})

def edit_group(id, group_name, sort_num):
    return request("POST", "/group/edit", {"id": id, "groupName": group_name, "sortNum": sort_num})

def delete_group(id):
    return request("POST", "/group/delete", {"id": id})

def get_group_detail(id):
    return request("POST", "/group/detail", {"id": id})
