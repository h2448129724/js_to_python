import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module='PIL')
import json
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from tkinter import ttk
import threading
import queue
import traceback
import asyncio
import pandas as pd
from register_gv import main as register_main
from index import main1 as index_main1
from request import close_browser  # 导入 close_browser 函数


# 初始化检查文件夹
def initialize_folders():
    folders = [
        "account_info",
        "excel_info",
        "message_excel_info",
        "message_info",
        "setting",
        "window_info"
    ]
    for folder in folders:
        path = os.path.join("./file", folder)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"文件夹 {path} 已创建")
        else:
            print(f"文件夹 {path} 已存在")
    print("初始化检查完成。")


class App:
    def __init__(self, parent, title, main_app, group_name=""):
        self.parent = parent
        self.main_app = main_app
        self.frame = tk.Frame(parent)
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.current_action = None  # 功能选择
        self.file_path = tk.StringVar()

        self.group_name = tk.StringVar(value=group_name)
        self.group_id = None
        self.queue = queue.Queue()
        self.title = title
        self.create_widgets(title)
        self.parent.after(100, self.process_queue)

    def create_widgets(self, title):
        self.frame.grid(row=0, column=0, sticky="nsew")

        self.input_label = tk.Label(self.frame, text=f"{title} - 分组名:")
        self.input_label.grid(row=0, column=0, pady=5)

        self.input_entry = tk.Entry(self.frame, textvariable=self.group_name, width=50)
        self.input_entry.grid(row=0, column=1, pady=5)

        self.file_label = tk.Label(self.frame, text=f"{title} - 选择一个 Excel 文件:")
        self.file_label.grid(row=1, column=0, pady=5)

        self.file_entry = tk.Entry(self.frame, textvariable=self.file_path, width=50)
        self.file_entry.grid(row=1, column=1, pady=5)

        self.browse_button = tk.Button(self.frame, text="浏览", command=self.browse_file)
        self.browse_button.grid(row=1, column=2, pady=5)

        self.control_frame = tk.Frame(self.frame)
        self.control_frame.grid(row=2, column=0, columnspan=3, pady=10)

        self.add_app_button = tk.Button(self.control_frame, text="新建窗口", command=self.main_app.add_app)
        self.add_app_button.grid(row=0, column=0, padx=5, pady=5)

        self.start_button = tk.Button(self.control_frame, text="开始", command=self.start)
        self.start_button.grid(row=0, column=1, padx=5, pady=5)

        self.stop_button = tk.Button(self.control_frame, text="结束", command=self.end)
        self.stop_button.grid(row=0, column=2, padx=5, pady=5)

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

    def start(self):
        if self.current_action == "register":
            self.run_register()
        elif self.current_action == "send_message":
            self.run_send()
        else:
            messagebox.showwarning("警告", "请先选择注册或发送信息操作。")

    def end(self):
        self.close_browser_with_title(self.title)

    def close_browser_with_title(self, title):
        print(f'get id to close')
        try:
            with open(f'./file/window_info/{title}.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, list):
                    latest_entry = next((entry for entry in reversed(data) if entry.get("name") == title), None)
                    if latest_entry:
                        id = latest_entry.get("id")
                        if id:
                            close_browser(id)
        except Exception as e:
            self.log(f"关闭浏览器时出错: {str(e)}\n")

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        self.file_path.set(file_path)
        if file_path:
            try:
                df = pd.read_excel(file_path)
                content = df.to_string(index=False)  # 将 DataFrame 转换为字符串
                self.file_text.delete(1.0, tk.END)
                self.file_text.insert(tk.INSERT, content)
            except Exception as e:
                messagebox.showerror("错误", f"读取文件时出错: {e}")

    def validate_excel_format(self, file_path, required):
        try:
            user_df = pd.read_excel(file_path)
            user_columns = [col.strip().lower() for col in user_df.columns]
            required_columns = [col.strip().lower() for col in required]
            return set(user_columns) == set(required_columns)
        except Exception as e:
            print(f"Error validating Excel format: {e}")
            return False

    def run_send(self):
        group_name = self.title
        file_path = self.file_path.get()
        if not group_name:
            messagebox.showwarning("警告", "分组名不能为空!")
            return
        if not file_path:
            messagebox.showwarning("警告", "请先选择一个文件!")
            return
        required_headers = ["号码", "内容"]
        if not self.validate_excel_format(file_path, required_headers):
            messagebox.showwarning("警告", "发送消息的Excel文件格式不正确!")
            return
        print(f'发送消息{group_name}, {file_path}')
        threading.Thread(target=self.run_index_script, args=(group_name, file_path)).start()

    def run_register(self):
        group_name = self.title
        file_path = self.file_path.get()

        if not group_name:
            messagebox.showwarning("警告", "分组名不能为空!")
            return
        if not file_path:
            messagebox.showwarning("警告", "请先选择一个文件!")
            return
        required_headers = ["账号", "密码", "辅助邮箱", "socks5"]
        if not self.validate_excel_format(file_path, required_headers):
            messagebox.showwarning("警告", "注册的Excel文件格式不正确!")
            return
        print(f'注册{group_name}, {file_path}')
        threading.Thread(target=self.run_register_script, args=(group_name, file_path)).start()

    def run_index_script(self, group_name, file_path):
        asyncio.run(index_main1(group_name, file_path))

    def run_register_script(self, group_name, file_path):
        register_main(group_name, file_path)

    def process_queue(self):
        while not self.queue.empty():
            message = self.queue.get_nowait()
            self.log_text.insert(tk.INSERT, message)
        self.parent.after(100, self.process_queue)

    def log(self, message):
        self.queue.put(message)


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("应用标题")

        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        menu_frame = tk.Frame(main_frame, width=200)
        menu_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.register_button = tk.Button(menu_frame, text="注册", command=self.show_register)
        self.register_button.pack(fill=tk.X, pady=10)

        self.send_message_button = tk.Button(menu_frame, text="发送短信", command=self.show_send_message)
        self.send_message_button.pack(fill=tk.X, pady=10)

        self.history_button = tk.Button(menu_frame, text="历史记录", command=self.show_history)
        self.history_button.pack(fill=tk.X, pady=10)

        self.tab_control = ttk.Notebook(main_frame)
        self.tab_control.pack(side=tk.LEFT, expand=1, fill=tk.BOTH)

        self.pages = {}
        self.current_page = None

    def show_register(self):
        self.show_page("register")

    def show_send_message(self):
        self.show_page("send_message")

    def show_history(self):
        self.show_page("history")

    def show_page(self, page_name):
        if page_name not in self.pages:
            if page_name == "register":
                self.pages[page_name] = RegisterPage(self.tab_control, self)
            elif page_name == "send_message":
                self.pages[page_name] = SendMessagePage(self.tab_control, self)
            elif page_name == "history":
                self.pages[page_name] = HistoryPage(self.tab_control, self)

        if self.current_page:
            self.current_page.pack_forget()
        self.current_page = self.pages[page_name]
        self.current_page.pack(expand=1, fill=tk.BOTH)
        self.tab_control.add(self.current_page, text=page_name.capitalize())

    def add_app(self):
        current_page = self.current_page
        if isinstance(current_page, RegisterPage):
            current_page.add_app("注册")
        elif isinstance(current_page, SendMessagePage):
            current_page.add_app("发送短信")
        elif isinstance(current_page, HistoryPage):
            current_page.add_app("历史记录")


class RegisterPage(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.app_frames = []

        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill='both')

        self.add_app("注册")

    def add_app(self, title, group_name=""):
        tab_frame = tk.Frame(self.tab_control)
        self.tab_control.add(tab_frame, text=title)
        app_frame = App(tab_frame, title, self.main_app, group_name)
        self.app_frames.append(app_frame)


class SendMessagePage(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.app_frames = []

        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill='both')

        self.add_app("发送短信")

    def add_app(self, title, group_name=""):
        tab_frame = tk.Frame(self.tab_control)
        self.tab_control.add(tab_frame, text=title)
        app_frame = App(tab_frame, title, self.main_app, group_name)
        self.app_frames.append(app_frame)


class HistoryPage(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.app_frames = []

        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill='both')

        self.add_app("历史记录")

    def add_app(self, title, group_name=""):
        tab_frame = tk.Frame(self.tab_control)
        self.tab_control.add(tab_frame, text=title)
        app_frame = App(tab_frame, title, self.main_app, group_name)
        self.app_frames.append(app_frame)


if __name__ == "__main__":
    initialize_folders()
    root = tk.Tk()
    main_app = MainApp(root)
    root.mainloop()
