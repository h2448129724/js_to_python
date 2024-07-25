# register.py
import os
from packages.utils import get_json_from_excel, get_json_file_info, write_json_to_file, delayed
from packages.register_gv import main as register_main
import asyncio

async def register_accounts_from_excel(config_file_name):
    await register_main(config_file_name)
