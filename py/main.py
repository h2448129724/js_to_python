# test_send.py
import unittest
import asyncio
from send import send_messages_from_excel

class TestSendMessages(unittest.TestCase):
    def test_send_messages(self):
        config_file_name = "test_send_config"  # 测试配置文件名称
        asyncio.run(send_messages_from_excel(config_file_name))

if __name__ == '__main__':
    unittest.main()

# test_register.py
import unittest
import asyncio
from register import register_accounts_from_excel

class TestRegisterAccounts(unittest.TestCase):
    def test_register_accounts(self):
        config_file_name = "test_register_config"  # 测试配置文件名称
        asyncio.run(register_accounts_from_excel(config_file_name))

if __name__ == '__main__':
    unittest.main()
