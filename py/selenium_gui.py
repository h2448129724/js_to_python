# import warnings
#
# warnings.filterwarnings("ignore", category=UserWarning, module='PIL')
#
# import tkinter as tk
# from tkinter import filedialog, scrolledtext, messagebox
# from tkinter import ttk
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import threading
# import queue
# import traceback
# import asyncio
# from send import send_messages_from_excel
# from register import register_accounts_from_excel
#
#
# class App:
#     def __init__(self, parent, title):
#         self.parent = parent
#         self.frame = tk.Frame(parent)
#         self.frame.grid(row=0, column=0, sticky="nsew")
#
#         self.file_path = tk.StringVar()
#         self.input_text = tk.StringVar()
#         self.queue = queue.Queue()
#
#         self.create_widgets(title)
#         self.parent.after(100, self.process_queue)
#
#     def create_widgets(self, title):
#         self.frame.grid(row=0, column=0, sticky="nsew")
#
#         # 分组输入框
#         self.input_label = tk.Label(self.frame, text=f"{title} - 输入框:")
#         self.input_label.grid(row=0, column=0, pady=5)
#
#         self.input_entry = tk.Entry(self.frame, textvariable=self.input_text, width=50)
#         self.input_entry.grid(row=0, column=1, pady=5)
#
#         # 文件选择
#         self.file_label = tk.Label(self.frame, text=f"{title} - 选择一个 .txt 文件:")
#         self.file_label.grid(row=1, column=0, pady=5)
#
#         self.file_entry = tk.Entry(self.frame, textvariable=self.file_path, width=50)
#         self.file_entry.grid(row=1, column=1, pady=5)
#
#         self.browse_button = tk.Button(self.frame, text="浏览", command=self.browse_file)
#         self.browse_button.grid(row=1, column=2, pady=5)
#
#         # 控制按钮
#         self.control_frame = tk.Frame(self.frame)
#         self.control_frame.grid(row=2, column=0, columnspan=3, pady=10)
#
#         self.add_app_button = tk.Button(self.control_frame, text="新建窗口", command=self.add_app)
#         self.add_app_button.grid(row=0, column=0, padx=5, pady=5)
#
#         self.start_button = tk.Button(self.control_frame, text="开始运行", command=self.run_script)
#         self.start_button.grid(row=0, column=1, padx=5, pady=5)
#
#         self.stop_button = tk.Button(self.control_frame, text="停止运行", command=self.stop_script)
#         self.stop_button.grid(row=0, column=2, padx=5, pady=5)
#
#         # 日志和文件内容选项卡
#         self.tab_control = ttk.Notebook(self.frame)
#         self.log_tab = tk.Frame(self.tab_control)
#         self.file_content_tab = tk.Frame(self.tab_control)
#
#         self.tab_control.add(self.log_tab, text='日志')
#         self.tab_control.add(self.file_content_tab, text='文件内容')
#
#         self.tab_control.grid(row=3, column=0, columnspan=3, sticky="nsew")
#
#         self.log_text = scrolledtext.ScrolledText(self.log_tab, wrap=tk.WORD, width=70, height=20)
#         self.log_text.pack(expand=1, fill='both', padx=10, pady=10)
#
#         self.file_text = scrolledtext.ScrolledText(self.file_content_tab, wrap=tk.WORD, width=70, height=20)
#         self.file_text.pack(expand=1, fill='both', padx=10, pady=10)
#
#     def browse_file(self):
#         file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
#         self.file_path.set(file_path)
#         if file_path:
#             with open(file_path, 'r', encoding='utf-8') as file:
#                 content = file.read()
#                 self.file_text.delete(1.0, tk.END)
#                 self.file_text.insert(tk.INSERT, content)
#
#     def run_script(self):
#         if not self.file_path.get():
#             messagebox.showwarning("警告", "请先选择一个文件!")
#             return
#
#         self.log_text.insert(tk.INSERT, "开始执行脚本...\n")
#
#         # 在一个单独的线程中运行Selenium以避免阻塞GUI
#         threading.Thread(target=self.selenium_task).start()
#
#     def selenium_task(self):
#         try:
#             self.log("设置浏览器...\n")
#             self.driver = webdriver.Chrome()  # 或使用webdriver.Firefox()或其他浏览器
#
#             self.log("打开百度...\n")
#             self.driver.get("https://www.baidu.com")
#
#             # 读取文件内容
#             with open(self.file_path.get(), 'r', encoding='utf-8') as file:
#                 search_query = file.read().strip()
#
#             self.log(f"搜索内容: {search_query}\n")
#
#             # 找到搜索输入框，输入查询并提交
#             search_box = WebDriverWait(self.driver, 10).until(
#                 EC.visibility_of_element_located((By.NAME, 'wd'))
#             )
#             search_box.send_keys(search_query)
#             search_box.send_keys(Keys.RETURN)
#
#             self.log("搜索完成。\n")
#
#         except Exception as e:
#             self.log(f"错误: {str(e)}\n")
#             self.log(traceback.format_exc() + "\n")
#
#     def process_queue(self):
#         while not self.queue.empty():
#             message = self.queue.get_nowait()
#             self.log_text.insert(tk.INSERT, message)
#         self.parent.after(100, self.process_queue)
#
#     def log(self, message):
#         self.queue.put(message)
#
#     def stop_script(self):
#         # 停止Selenium浏览器
#         try:
#             self.driver.quit()
#             self.log("浏览器已停止。\n")
#         except Exception as e:
#             self.log(f"停止浏览器时出错: {str(e)}\n")
#
#     def add_app(self):
#         tab_title = f"演示界面 {len(self.app_frames) + 1}"
#         tab_frame = tk.Frame(self.tab_control)
#         self.tab_control.add(tab_frame, text=tab_title)
#         app_frame = App(tab_frame, tab_title)
#         self.app_frames.append(app_frame)
#
#     def remove_app(self):
#         if self.app_frames:
#             app_frame = self.app_frames.pop()
#             index = self.tab_control.index("current")
#             self.tab_control.forget(index)
#
#     def run_send(self):
#         input_text = self.input_text.get()
#         file_path = self.file_path.get()
#         threading.Thread(target=asyncio.run, args=(send_messages_from_excel(input_text, file_path),)).start()
#
#     def run_register(self):
#         input_text = self.input_text.get()
#         file_path = self.file_path.get()
#         threading.Thread(target=asyncio.run, args=(register_accounts_from_excel(input_text, file_path),)).start()
#
#
# class MainApp:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Selenium 多演示界面")
#
#         # 主框架
#         main_frame = tk.Frame(self.root)
#         main_frame.pack(fill=tk.BOTH, expand=True)
#
#         # 左侧菜单
#         menu_frame = tk.Frame(main_frame, width=200)
#         menu_frame.pack(side=tk.LEFT, fill=tk.Y)
#
#         self.register_button = tk.Button(menu_frame, text="注册", command=self.register)
#         self.register_button.pack(fill=tk.X, pady=10)
#
#         self.send_message_button = tk.Button(menu_frame, text="发送短信", command=self.send_message)
#         self.send_message_button.pack(fill=tk.X, pady=10)
#
#         self.history_button = tk.Button(menu_frame, text="历史记录", command=self.history)
#         self.history_button.pack(fill=tk.X, pady=10)
#
#         # 右侧内容
#         self.tab_control = ttk.Notebook(main_frame)
#         self.tab_control.pack(side=tk.LEFT, expand=1, fill='both')
#
#         self.app_frames = []
#
#         # 添加默认的演示界面
#         self.add_app()
#
#     def add_app(self):
#         tab_title = f"演示界面 {len(self.app_frames) + 1}"
#         tab_frame = tk.Frame(self.tab_control)
#         self.tab_control.add(tab_frame, text=tab_title)
#         app_frame = App(tab_frame, tab_title)
#         self.app_frames.append(app_frame)
#
#     def remove_app(self):
#         if self.app_frames:
#             app_frame = self.app_frames.pop()
#             index = self.tab_control.index("current")
#             self.tab_control.forget(index)
#
#     def start_script(self):
#         current_tab = self.tab_control.index("current")
#         if current_tab >= 0 and current_tab < len(self.app_frames):
#             self.app_frames[current_tab].run_script()
#
#     def stop_script(self):
#         current_tab = self.tab_control.index("current")
#         if current_tab >= 0 and current_tab < len(self.app_frames):
#             self.app_frames[current_tab].stop_script()
#
#     def register(self):
#         current_tab = self.tab_control.index("current")
#         if current_tab >= 0 and current_tab < len(self.app_frames):
#             self.app_frames[current_tab].run_register()
#
#     def send_message(self):
#         current_tab = self.tab_control.index("current")
#         if current_tab >= 0 and current_tab < len(self.app_frames):
#             self.app_frames[current_tab].run_send()
#
#     def history(self):
#         print("历史记录功能待实现")
#
#
# if __name__ == "__main__":
#     root = tk.Tk()
#     main_app = MainApp(root)
#     root.mainloop()
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module='PIL')

import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from tkinter import ttk
import threading
import queue
import traceback
import asyncio
from send import send_messages_from_excel
from register import register_accounts_from_excel
from packages.index import main as index_main  # 引入index_main函数

class App:
    def __init__(self, parent, title):
        self.parent = parent
        self.frame = tk.Frame(parent)
        self.frame.grid(row=0, column=0, sticky="nsew")

        self.file_path = tk.StringVar()
        self.group_name = tk.StringVar()  # 修改变量名
        self.group_id = None  # 分组ID变量
        self.queue = queue.Queue()

        self.create_widgets(title)
        self.parent.after(100, self.process_queue)

    def create_widgets(self, title):
        self.frame.grid(row=0, column=0, sticky="nsew")

        # 分组名输入框
        self.input_label = tk.Label(self.frame, text=f"{title} - 分组名:")
        self.input_label.grid(row=0, column=0, pady=5)

        self.input_entry = tk.Entry(self.frame, textvariable=self.group_name, width=50)
        self.input_entry.grid(row=0, column=1, pady=5)

        # 文件选择
        self.file_label = tk.Label(self.frame, text=f"{title} - 选择一个 Excel 文件:")
        self.file_label.grid(row=1, column=0, pady=5)

        self.file_entry = tk.Entry(self.frame, textvariable=self.file_path, width=50)
        self.file_entry.grid(row=1, column=1, pady=5)

        self.browse_button = tk.Button(self.frame, text="浏览", command=self.browse_file)
        self.browse_button.grid(row=1, column=2, pady=5)

        # 控制按钮
        self.control_frame = tk.Frame(self.frame)
        self.control_frame.grid(row=2, column=0, columnspan=3, pady=10)

        self.add_app_button = tk.Button(self.control_frame, text="新建窗口", command=self.add_app)
        self.add_app_button.grid(row=0, column=0, padx=5, pady=5)

        self.start_button = tk.Button(self.control_frame, text="开始运行", command=self.run_script)
        self.start_button.grid(row=0, column=1, padx=5, pady=5)

        self.stop_button = tk.Button(self.control_frame, text="停止运行", command=self.stop_script)
        self.stop_button.grid(row=0, column=2, padx=5, pady=5)

        # 日志和文件内容选项卡
        self.tab_control = ttk.Notebook(self.frame)
        self.log_tab = tk.Frame(self.tab_control)
        self.file_content_tab = tk.Frame(self.tab_control)

        self.tab_control.add(self.log_tab, text='日志')
        self.tab_control.add(self.file_content_tab, text='文件内容')

        self.tab_control.grid(row=3, column=0, columnspan=3, sticky="nsew")

        self.log_text = scrolledtext.ScrolledText(self.log_tab, wrap=tk.WORD, width=70, height=20)
        self.log_text.pack(expand=1, fill='both', padx=10, pady=10)

        self.file_text = scrolledtext.ScrolledText(self.file_content_tab, wrap=tk.WORD, width=70, height=20)
        self.file_text.pack(expand=1, fill='both', padx=10, pady=10)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        self.file_path.set(file_path)
        if file_path:
            with open(file_path, 'rb') as file:
                content = file.read()
                self.file_text.delete(1.0, tk.END)
                self.file_text.insert(tk.INSERT, content)

    def run_script(self):
        if not self.file_path.get():
            messagebox.showwarning("警告", "请先选择一个文件!")
            return

        self.log_text.insert(tk.INSERT, "开始执行脚本...\n")

        # 在一个单独的线程中运行index_main以避免阻塞GUI
        threading.Thread(target=self.run_index_script).start()

    def run_index_script(self):
        asyncio.run(index_main())

    def process_queue(self):
        while not self.queue.empty():
            message = self.queue.get_nowait()
            self.log_text.insert(tk.INSERT, message)
        self.parent.after(100, self.process_queue)

    def log(self, message):
        self.queue.put(message)

    def stop_script(self):
        # 停止Selenium浏览器
        try:
            self.driver.quit()
            self.log("浏览器已停止。\n")
        except Exception as e:
            self.log(f"停止浏览器时出错: {str(e)}\n")

    def add_app(self):
        tab_title = f"演示界面 {len(self.app_frames) + 1}"
        tab_frame = tk.Frame(self.tab_control)
        self.tab_control.add(tab_frame, text=tab_title)
        app_frame = App(tab_frame, tab_title)
        self.app_frames.append(app_frame)

    def remove_app(self):
        if self.app_frames:
            app_frame = self.app_frames.pop()
            index = self.tab_control.index("current")
            self.tab_control.forget(index)

    def run_send(self):
        group_name = self.group_name.get()
        file_path = self.file_path.get()
        threading.Thread(target=asyncio.run, args=(send_messages_from_excel(group_name, file_path),)).start()

    def run_register(self):
        group_name = self.group_name.get()
        file_path = self.file_path.get()
        threading.Thread(target=asyncio.run, args=(register_accounts_from_excel(group_name, file_path),)).start()

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Selenium 多演示界面")

        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧菜单
        menu_frame = tk.Frame(main_frame, width=200)
        menu_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.register_button = tk.Button(menu_frame, text="注册", command=self.register)
        self.register_button.pack(fill=tk.X, pady=10)

        self.send_message_button = tk.Button(menu_frame, text="发送短信", command=self.send_message)
        self.send_message_button.pack(fill=tk.X, pady=10)

        self.history_button = tk.Button(menu_frame, text="历史记录", command=self.history)
        self.history_button.pack(fill=tk.X, pady=10)

        # 右侧内容
        self.tab_control = ttk.Notebook(main_frame)
        self.tab_control.pack(side=tk.LEFT, expand=1, fill='both')

        self.app_frames = []

        # 添加默认的演示界面
        self.add_app()

    def add_app(self):
        tab_title = f"演示界面 {len(self.app_frames) + 1}"
        tab_frame = tk.Frame(self.tab_control)
        self.tab_control.add(tab_frame, text=tab_title)
        app_frame = App(tab_frame, tab_title)
        self.app_frames.append(app_frame)

    def remove_app(self):
        if self.app_frames:
            app_frame = self.app_frames.pop()
            index = self.tab_control.index("current")
            self.tab_control.forget(index)

    def start_script(self):
        current_tab = self.tab_control.index("current")
        if current_tab >= 0 and current_tab < len(self.app_frames):
            self.app_frames[current_tab].run_script()

    def stop_script(self):
        current_tab = self.tab_control.index("current")
        if current_tab >= 0 and current_tab < len(self.app_frames):
            self.app_frames[current_tab].stop_script()

    def register(self):
        current_tab = self.tab_control.index("current")
        if current_tab >= 0 and current_tab < len(self.app_frames):
            self.app_frames[current_tab].run_register()

    def send_message(self):
        current_tab = self.tab_control.index("current")
        if current_tab >= 0 and current_tab < len(self.app_frames):
            self.app_frames[current_tab].run_send()

    def history(self):
        print("历史记录功能待实现")

if __name__ == "__main__":
    root = tk.Tk()
    main_app = MainApp(root)
    root.mainloop()
