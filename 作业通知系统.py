#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox, scrolledtext
import json
import os
from datetime import datetime
import requests
import base64
import threading
import time
import hmac
import hashlib
from urllib.parse import quote

class SimpleHomework:
    def __init__(self):
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("多班级作业通知系统 - 教师版")
        
        # 配置文件
        home_dir = os.path.expanduser("~")
        self.config_file = os.path.join(home_dir, "multi_class_homework_config.json")
        self.local_data_file = os.path.join(home_dir, "homework_data.json")
        
        # 自动同步相关变量
        self.auto_sync_enabled = True
        self.sync_interval = 300  # 5分钟同步一次
        self.last_remote_update = ""
        self.sync_thread = None
        self.stop_sync = False
        
        # 初始化配置
        self.setup_files()
        
        # 创建界面
        self.create_main_window()
        
        # 启动自动同步
        self.start_auto_sync()
        
        # 更新显示
        self.update_display()
        
        # 检查是否需要显示晨读提醒
        self.check_morning_reading()
        
    def setup_files(self):
        """创建配置和数据文件如果不存在"""
        if not os.path.exists(self.config_file):
            default_config = {
                "cos_bucket": "class-homework-1257663765",  # COS存储桶名称
                "cos_region": "ap-beijing",  # COS区域
                "secret_id": "AKID2zr8sS5E5x5x5x5x5x5x5x5x5x5x5x5x",  # 教师端默认SecretId
                "secret_key": "5x5x5x5x5x5x5x5x5x5x5x5x5x5x5x5x5x5x",  # 教师端默认SecretKey
                "last_sync": "",
                "auto_sync": True,
                "sync_interval": 300,
                "classes": ["720班", "719班", "721班"],  # 默认班级列表
                "current_class": "720班"  # 当前选中的班级
            }
            self.save_config(default_config)
            
        if not os.path.exists(self.local_data_file):
            default_data = self.get_empty_data()
            self.save_local_data(default_data)
    
    def load_config(self):
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 确保新配置项存在
                if "cos_bucket" not in config:
                    config["cos_bucket"] = "class-homework-1257663765"
                if "cos_region" not in config:
                    config["cos_region"] = "ap-beijing"
                if "secret_id" not in config:
                    config["secret_id"] = "AKID2zr8sS5E5x5x5x5x5x5x5x5x5x5x5x5x"
                if "secret_key" not in config:
                    config["secret_key"] = "5x5x5x5x5x5x5x5x5x5x5x5x5x5x5x5x5x5x"
                if "auto_sync" not in config:
                    config["auto_sync"] = True
                if "sync_interval" not in config:
                    config["sync_interval"] = 300
                if "classes" not in config:
                    config["classes"] = ["720班", "719班", "721班"]
                if "current_class" not in config:
                    config["current_class"] = "720班"
                return config
        except:
            return {
                "cos_bucket": "class-homework-1257663765",
                "cos_region": "ap-beijing", 
                "secret_id": "AKID2zr8sS5E5x5x5x5x5x5x5x5x5x5x5x5x",
                "secret_key": "5x5x5x5x5x5x5x5x5x5x5x5x5x5x5x5x5x5x",
                "last_sync": "", 
                "auto_sync": True, 
                "sync_interval": 300,
                "classes": ["720班", "719班", "721班"],
                "current_class": "720班"
            }
    
    def save_config(self, config):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def get_empty_data(self):
        """获取空数据结构"""
        config = self.load_config()
        classes = config.get("classes", ["720班"])
        
        data = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 为每个班级创建空数据
        for class_name in classes:
            data[class_name] = {
                "语文": "暂无作业",
                "数学": "暂无作业", 
                "英语": "暂无作业",
                "科学": "暂无作业",
                "道法": "暂无作业",
                "社会": "暂无作业",
                "晨读": "暂无晨读任务"
            }
        
        return data
    
    def save_local_data(self, data):
        """保存本地数据"""
        try:
            with open(self.local_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def load_local_data(self):
        """加载本地数据"""
        try:
            with open(self.local_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return self.get_empty_data()
    
    def get_current_class_data(self):
        """获取当前班级的数据"""
        data = self.load_local_data()
        config = self.load_config()
        current_class = config.get("current_class", "720班")
        
        if current_class in data:
            return data[current_class]
        else:
            # 如果当前班级不存在，返回默认数据
            return {
                "语文": "暂无作业",
                "数学": "暂无作业", 
                "英语": "暂无作业",
                "科学": "暂无作业",
                "道法": "暂无作业",
                "社会": "暂无作业",
                "晨读": "暂无晨读任务"
            }
    
    def save_current_class_data(self, class_data):
        """保存当前班级的数据"""
        data = self.load_local_data()
        config = self.load_config()
        current_class = config.get("current_class", "720班")
        
        data[current_class] = class_data
        data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return self.save_local_data(data)
    
    def check_morning_reading(self):
        """检查是否需要显示晨读提醒"""
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        # 检查是否在7:50之前
        if current_hour < 7 or (current_hour == 7 and current_minute < 50):
            class_data = self.get_current_class_data()
            morning_reading = class_data.get("晨读", "暂无晨读任务")
            
            # 如果有晨读任务，显示提醒窗口
            if morning_reading != "暂无晨读任务" and morning_reading.strip():
                config = self.load_config()
                current_class = config.get("current_class", "720班")
                self.show_morning_reading_reminder(morning_reading, current_class)
    
    def show_morning_reading_reminder(self, content, class_name):
        """显示晨读提醒窗口"""
        reminder_window = tk.Toplevel(self.root)
        reminder_window.title(f"晨读提醒 - {class_name}")
        reminder_window.configure(bg='lightyellow')
        reminder_window.attributes('-topmost', True)
        
        # 设置窗口大小和位置 - 更大更醒目
        window_width = 800
        window_height = 600
        screen_width = reminder_window.winfo_screenwidth()
        screen_height = reminder_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        reminder_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 标题
        title_label = tk.Label(reminder_window, 
                             text="⏰ 晨读时间到！", 
                             font=('Arial', 28, 'bold'),
                             fg='darkred',
                             bg='lightyellow')
        title_label.pack(pady=30)
        
        # 时间提示
        time_label = tk.Label(reminder_window,
                            text="请在7:50之前完成晨读任务",
                            font=('Arial', 18, 'bold'),
                            fg='blue',
                            bg='lightyellow')
        time_label.pack(pady=15)
        
        # 晨读内容框架
        content_frame = tk.Frame(reminder_window, bg='white', bd=3, relief='solid')
        content_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # 晨读内容标签
        content_label = tk.Label(content_frame, 
                               text="今日晨读内容：",
                               font=('Arial', 20, 'bold'),
                               bg='white')
        content_label.pack(anchor='w', padx=15, pady=10)
        
        # 晨读内容文本框 - 字体更大
        content_text = scrolledtext.ScrolledText(content_frame,
                                               font=('Arial', 22),
                                               wrap=tk.WORD,
                                               bg='lightcyan',
                                               height=12)
        content_text.pack(fill='both', expand=True, padx=15, pady=15)
        content_text.insert('1.0', content)
        content_text.config(state='disabled')  # 设为只读
        
        # 按钮框架
        button_frame = tk.Frame(reminder_window, bg='lightyellow')
        button_frame.pack(fill='x', padx=30, pady=20)
        
        # 我知道了按钮
        ok_button = tk.Button(button_frame,
                            text="我已知晓，开始晨读",
                            command=reminder_window.destroy,
                            font=('Arial', 18, 'bold'),
                            bg='lightgreen',
                            width=20,
                            height=2)
        ok_button.pack(pady=10)
        
        # 自动关闭定时器（7:50自动关闭）
        self.schedule_reminder_close(reminder_window)
    
    def schedule_reminder_close(self, window):
        """安排提醒窗口在7:50自动关闭"""
        def check_time_and_close():
            now = datetime.now()
            if now.hour >= 7 and now.minute >= 50:
                window.destroy()
                return
            # 每分钟检查一次
            window.after(60000, check_time_and_close)
        
        check_time_and_close()
    
    def get_remote_update_time(self):
        """获取远程数据的更新时间"""
        config = self.load_config()
        
        try:
            # 使用简单的HTTP请求获取文件的最后修改时间
            url = f"https://{config['cos_bucket']}.cos.{config['cos_region']}.myqcloud.com/homework_data.json"
            response = requests.head(url, timeout=10)
            
            if response.status_code == 200:
                last_modified = response.headers.get('Last-Modified', '')
                if last_modified:
                    return last_modified
            return ""
        except:
            return ""
    
    def check_remote_updates(self):
        """检查远程是否有更新"""
        config = self.load_config()
        if not config.get('auto_sync', True):
            return False
            
        remote_update = self.get_remote_update_time()
        if not remote_update:
            return False
            
        local_data = self.load_local_data()
        local_update = local_data.get('last_updated', '')
        
        # 如果远程更新时间比本地新，则需要同步
        if remote_update > local_update:
            return True
            
        return False
    
    def auto_sync_worker(self):
        """自动同步工作线程"""
        while not self.stop_sync:
            try:
                if self.auto_sync_enabled:
                    config = self.load_config()
                    if config.get('auto_sync', True):
                        if self.check_remote_updates():
                            # 在GUI线程中执行更新
                            self.root.after(0, self.perform_auto_sync)
            except Exception as e:
                print(f"自动同步检查错误: {e}")
            
            # 等待下一次检查
            interval = self.sync_interval
            config = self.load_config()
            if 'sync_interval' in config:
                interval = config['sync_interval']
                
            for i in range(interval):
                if self.stop_sync:
                    break
                time.sleep(1)
    
    def perform_auto_sync(self):
        """执行自动同步"""
        success, message = self.download_from_cos()
        if success:
            self.update_display()
            # 显示通知（非阻塞）
            self.show_sync_notification("作业已自动更新")
        else:
            print(f"自动同步失败: {message}")
    
    def show_sync_notification(self, message):
        """显示同步通知"""
        # 临时更新状态栏显示通知
        original_status = self.status_label.cget("text")
        self.status_label.config(text=f"[通知] {message}")
        
        # 3秒后恢复原状态
        def restore_status():
            self.status_label.config(text=original_status)
        
        self.root.after(3000, restore_status)
    
    def start_auto_sync(self):
        """启动自动同步"""
        config = self.load_config()
        self.auto_sync_enabled = config.get('auto_sync', True)
        self.sync_interval = config.get('sync_interval', 300)
        
        if not self.sync_thread and self.auto_sync_enabled:
            self.stop_sync = False
            self.sync_thread = threading.Thread(target=self.auto_sync_worker, daemon=True)
            self.sync_thread.start()
    
    def stop_auto_sync(self):
        """停止自动同步"""
        self.stop_sync = True
        if self.sync_thread:
            self.sync_thread.join(timeout=2)
            self.sync_thread = None
    
    def generate_cos_signature(self, config, key_time, method='get', file_key=''):
        """生成COS签名"""
        sign_key = hmac.new(
            config['secret_key'].encode('utf-8'),
            key_time.encode('utf-8'),
            hashlib.sha1
        ).hexdigest()
        
        # 构建签名字符串
        http_string = f"{method.lower()}\n/{file_key}\n\n\n"
        string_to_sign = f"sha1\n{key_time}\n{hashlib.sha1(http_string.encode('utf-8')).hexdigest()}\n"
        
        # 计算签名
        signature = hmac.new(
            sign_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        ).hexdigest()
        
        return f"q-sign-algorithm=sha1&q-ak={config['secret_id']}&q-sign-time={key_time}&q-key-time={key_time}&q-header-list=&q-url-param-list=&q-signature={signature}"
    
    def download_from_cos(self):
        """从腾讯云COS下载数据"""
        config = self.load_config()
        
        if not config.get('secret_id') or not config.get('secret_key'):
            return False, "请先在设置中配置腾讯云SecretId和SecretKey"
        
        try:
            # 生成签名
            key_time = f"{int(time.time()) - 60};{int(time.time()) + 300}"
            signature = self.generate_cos_signature(config, key_time, 'get', 'homework_data.json')
            
            url = f"https://{config['cos_bucket']}.cos.{config['cos_region']}.myqcloud.com/homework_data.json"
            
            headers = {
                'Authorization': signature
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # 保存到本地
                self.save_local_data(data)
                
                # 更新同步时间
                config['last_sync'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.save_config(config)
                
                return True, "同步成功！"
            else:
                error_msg = f"下载失败: {response.status_code}"
                return False, error_msg
                
        except Exception as e:
            return False, f"网络错误: {str(e)}"
    
    def upload_to_cos(self):
        """上传数据到腾讯云COS"""
        config = self.load_config()
        
        if not config.get('secret_id') or not config.get('secret_key'):
            return False, "请先在设置中配置腾讯云SecretId和SecretKey"
        
        try:
            data = self.load_local_data()
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            
            # 生成签名
            key_time = f"{int(time.time()) - 60};{int(time.time()) + 300}"
            signature = self.generate_cos_signature(config, key_time, 'put', 'homework_data.json')
            
            url = f"https://{config['cos_bucket']}.cos.{config['cos_region']}.myqcloud.com/homework_data.json"
            
            headers = {
                'Authorization': signature,
                'Content-Type': 'application/json'
            }
            
            response = requests.put(url, data=json_data.encode('utf-8'), headers=headers, timeout=10)
            
            if response.status_code == 200:
                # 更新同步时间
                config['last_sync'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.save_config(config)
                
                return True, "上传成功！"
            else:
                error_msg = f"上传失败: {response.status_code}"
                return False, error_msg
                
        except Exception as e:
            return False, f"网络错误: {str(e)}"
    
    def get_weekday(self):
        """获取星期几"""
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        today = datetime.now().weekday()
        return weekdays[today]
    
    def create_main_window(self):
        """创建主窗口界面"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        window_width = 680
        window_height = 1000
        
        x = screen_width - window_width - 10
        y = 10
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.attributes('-topmost', True)
        self.root.configure(bg='lightblue')
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 主容器
        main_container = tk.Frame(self.root, bg='lightblue')
        main_container.pack(fill='both', expand=True)
        
        # 标题栏
        title_frame = tk.Frame(main_container, bg='darkblue', height=80)
        title_frame.pack(fill='x', padx=3, pady=3)
        
        config = self.load_config()
        current_class = config.get("current_class", "720班")
        title_text = f"多班级作业通知 · {current_class} · {self.get_weekday()} · 教师版"
        title_label = tk.Label(title_frame, text=title_text, fg='white', 
                              bg='darkblue', font=('Arial', 16, 'bold'))
        title_label.pack(expand=True)
        
        # 状态栏
        status_frame = tk.Frame(main_container, bg='lightyellow', height=30)
        status_frame.pack(fill='x', padx=3, pady=2)
        
        self.status_label = tk.Label(status_frame, text="正在初始化...", 
                                  fg='black', bg='lightyellow', font=('Arial', 10))
        self.status_label.pack(expand=True)
        
        # 内容区域
        content_frame = tk.Frame(main_container, bg='lightblue')
        content_frame.pack(fill='both', expand=True, padx=8, pady=8)
        
        # 创建Canvas和Scrollbar实现滚动
        self.canvas = tk.Canvas(content_frame, bg='lightblue', highlightthickness=0)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg='lightblue')
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind("<MouseWheel>", on_mousewheel)
        
        # 按钮区域 - 去掉上传作业按钮
        bottom_frame = tk.Frame(main_container, bg='lightblue', height=120)
        bottom_frame.pack(fill='x', side='bottom', padx=10, pady=10)
        bottom_frame.pack_propagate(False)
        
        # 按钮容器
        btn_container = tk.Frame(bottom_frame, bg='lightblue')
        btn_container.pack(expand=True)
        
        config_btn = tk.Button(btn_container, text="云存储设置", command=self.open_config,
                           bg='lightgreen', font=('Arial', 12, 'bold'),
                           height=1, width=12)
        config_btn.pack(side='left', padx=5, pady=5)
        
        download_btn = tk.Button(btn_container, text="立即同步", command=self.download_cos,
                           bg='lightyellow', font=('Arial', 12, 'bold'),
                           height=1, width=12)
        download_btn.pack(side='left', padx=5, pady=5)
        
        edit_btn = tk.Button(btn_container, text="编辑作业", command=self.open_editor,
                           bg='lightcoral', font=('Arial', 12, 'bold'),
                           height=1, width=12)
        edit_btn.pack(side='left', padx=5, pady=5)
    
    def update_display(self):
        """更新显示内容"""
        class_data = self.get_current_class_data()
        config = self.load_config()
        current_class = config.get("current_class", "720班")
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        subjects = ["语文", "数学", "英语", "科学", "道法", "社会", "晨读"]
        
        for subject in subjects:
            # 主框架
            subject_frame = tk.Frame(self.scrollable_frame, bg='white', bd=3, relief='solid')
            subject_frame.pack(fill='x', padx=5, pady=8)
            
            # 左侧科目名称
            subject_label_frame = tk.Frame(subject_frame, bg='lightyellow', width=60)
            subject_label_frame.pack(side='left', fill='y', padx=5, pady=5)
            subject_label_frame.pack_propagate(False)
            
            # 晨读特殊样式
            if subject == "晨读":
                bg_color = 'lightpink'
                font_color = 'darkred'
            else:
                bg_color = 'lightyellow'
                font_color = 'black'
            
            subject_label = tk.Label(subject_label_frame, text=subject, 
                                   font=('Arial', 14, 'bold'),
                                   bg=bg_color,
                                   fg=font_color,
                                   justify='center')
            subject_label.pack(expand=True, fill='both', padx=5, pady=5)
            
            # 右侧作业内容
            content_frame = tk.Frame(subject_frame, bg='white')
            content_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
            
            homework_content = class_data.get(subject, "暂无作业")
            line_count = homework_content.count('\n') + 1
            display_height = max(1, min(10, line_count))
            
            # 所有科目内容都使用大字体，和晨读一样醒目
            if subject == "晨读":
                text_bg = 'lightcyan'
                text_font = ('Arial', 18, 'bold')  # 晨读字体
            else:
                text_bg = 'white'
                text_font = ('Arial', 18, 'bold')  # 其他科目也使用大字体
            
            content_text = tk.Text(content_frame, 
                                 font=text_font,
                                 bg=text_bg, fg='black',
                                 wrap=tk.WORD,
                                 width=35,
                                 height=display_height,
                                 relief='flat',
                                 borderwidth=0,
                                 highlightthickness=0)
            content_text.pack(fill='both', expand=True)
            content_text.insert('1.0', homework_content)
            content_text.config(state='disabled')
        
        # 更新状态
        config = self.load_config()
        secret_id = config.get("secret_id", "")
        last_sync = config.get("last_sync", "从未同步")
        auto_sync = config.get("auto_sync", True)
        
        sync_status = "[自动同步中]" if auto_sync else "[自动同步关闭]"
        
        if not secret_id:
            status_text = f"教师模式 | 当前班级: {current_class} | 请配置云存储密钥获得完整功能"
        else:
            status_text = f"教师模式 | 当前班级: {current_class} | 最后同步: {last_sync} | {sync_status}"
        
        self.status_label.config(text=status_text)
        
        # 更新标题
        title_text = f"多班级作业通知 · {current_class} · {self.get_weekday()} · 教师版"
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, tk.Label) and grandchild.cget('bg') == 'darkblue':
                                grandchild.config(text=title_text)
        
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_closing(self):
        """程序关闭时的处理"""
        self.stop_auto_sync()
        self.root.destroy()
    
    def download_cos(self):
        """从COS下载"""
        success, message = self.download_from_cos()
        if success:
            messagebox.showinfo("成功", message)
            self.update_display()
        else:
            messagebox.showerror("错误", message)
    
    def open_editor(self):
        EditorWindow(self)
    
    def open_config(self):
        ConfigWindow(self)
    
    def run(self):
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"程序运行错误: {e}")
            messagebox.showerror("错误", f"程序运行出错: {str(e)}")

class ConfigWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("多班级云存储设置")
        
        self.center_window(700, 900)
        self.window.configure(bg='white')
        self.window.attributes('-topmost', True)
        
        self.create_config_ui()
    
    def center_window(self, width, height):
        """将窗口居中显示"""
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_config_ui(self):
        config = self.parent.load_config()
        secret_id = config.get("secret_id", "")
        secret_key = config.get("secret_key", "")
        cos_bucket = config.get("cos_bucket", "class-homework-1257663765")
        cos_region = config.get("cos_region", "ap-beijing")
        last_sync = config.get("last_sync", "从未同步")
        auto_sync = config.get("auto_sync", True)
        sync_interval = config.get("sync_interval", 300)
        classes = config.get("classes", ["720班", "719班", "721班"])
        current_class = config.get("current_class", "720班")
        
        main_frame = tk.Frame(self.window, bg='white', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # 标题
        title_label = tk.Label(main_frame, text="多班级云存储设置", 
                              font=('Arial', 20, 'bold'), bg='white')
        title_label.pack(pady=(0, 20))
        
        # 说明文字
        info_text = """使用说明：
1. 系统已预置教师端默认密钥和存储桶
2. 可修改存储桶名称和地域信息
3. 可管理班级列表和设置当前班级
4. 支持多班级作业管理

默认存储桶信息：
- 存储桶名称：class-homework-1257663765
- 地域：ap-beijing（北京）"""
        
        info_label = tk.Label(main_frame, text=info_text, 
                             font=('Arial', 11), bg='white', justify='left')
        info_label.pack(pady=(0, 20))
        
        # SecretId输入框
        secret_id_frame = tk.Frame(main_frame, bg='white')
        secret_id_frame.pack(fill='x', pady=10)
        
        tk.Label(secret_id_frame, text="腾讯云SecretId:", font=('Arial', 12, 'bold'), bg='white').pack(anchor='w')
        self.secret_id_entry = tk.Entry(secret_id_frame, font=('Arial', 12), width=50)
        self.secret_id_entry.pack(fill='x', pady=5)
        self.secret_id_entry.insert(0, secret_id)
        
        # SecretKey输入框
        secret_key_frame = tk.Frame(main_frame, bg='white')
        secret_key_frame.pack(fill='x', pady=10)
        
        tk.Label(secret_key_frame, text="腾讯云SecretKey:", font=('Arial', 12, 'bold'), bg='white').pack(anchor='w')
        self.secret_key_entry = tk.Entry(secret_key_frame, font=('Arial', 12), width=50, show="*")
        self.secret_key_entry.pack(fill='x', pady=5)
        self.secret_key_entry.insert(0, secret_key)
        
        # 存储桶信息 - 可编辑
        bucket_frame = tk.Frame(main_frame, bg='white')
        bucket_frame.pack(fill='x', pady=10)
        
        tk.Label(bucket_frame, text="存储桶名称:", font=('Arial', 12, 'bold'), bg='white').pack(anchor='w')
        self.bucket_entry = tk.Entry(bucket_frame, font=('Arial', 12), width=50)
        self.bucket_entry.pack(fill='x', pady=5)
        self.bucket_entry.insert(0, cos_bucket)
        
        # 地域信息 - 可编辑
        region_frame = tk.Frame(main_frame, bg='white')
        region_frame.pack(fill='x', pady=10)
        
        tk.Label(region_frame, text="地域:", font=('Arial', 12, 'bold'), bg='white').pack(anchor='w')
        self.region_entry = tk.Entry(region_frame, font=('Arial', 12), width=50)
        self.region_entry.pack(fill='x', pady=5)
        self.region_entry.insert(0, cos_region)
        
        # 班级管理
        class_frame = tk.Frame(main_frame, bg='white')
        class_frame.pack(fill='x', pady=10)
        
        tk.Label(class_frame, text="班级管理 (每行一个班级):", font=('Arial', 12, 'bold'), bg='white').pack(anchor='w')
        
        class_edit_frame = tk.Frame(class_frame, bg='white')
        class_edit_frame.pack(fill='x', pady=5)
        
        self.classes_text = scrolledtext.ScrolledText(class_edit_frame, 
                                                    font=('Arial', 11),
                                                    wrap=tk.WORD,
                                                    width=50,
                                                    height=4,
                                                    bg='lightgray')
        self.classes_text.pack(fill='x', pady=5)
        self.classes_text.insert('1.0', '\n'.join(classes))
        
        # 当前班级选择
        current_class_frame = tk.Frame(main_frame, bg='white')
        current_class_frame.pack(fill='x', pady=10)
        
        tk.Label(current_class_frame, text="当前显示班级:", font=('Arial', 12, 'bold'), bg='white').pack(anchor='w')
        
        self.current_class_var = tk.StringVar(value=current_class)
        current_class_select_frame = tk.Frame(current_class_frame, bg='white')
        current_class_select_frame.pack(fill='x', pady=5)
        
        # 创建班级选择单选按钮
        for class_name in classes:
            class_radio = tk.Radiobutton(current_class_select_frame, 
                                       text=class_name,
                                       variable=self.current_class_var,
                                       value=class_name,
                                       font=('Arial', 11),
                                       bg='white')
            class_radio.pack(side='left', padx=10)
        
        # 同步时间
        sync_frame = tk.Frame(main_frame, bg='white')
        sync_frame.pack(fill='x', pady=10)
        
        tk.Label(sync_frame, text="最后同步:", font=('Arial', 12, 'bold'), bg='white').pack(anchor='w')
        sync_display = tk.Label(sync_frame, text=last_sync, 
                              font=('Arial', 11), bg='lightgray', relief='sunken', anchor='w')
        sync_display.pack(fill='x', pady=5, ipady=2)
        
        # 自动同步设置
        auto_sync_frame = tk.Frame(main_frame, bg='white')
        auto_sync_frame.pack(fill='x', pady=10)
        
        tk.Label(auto_sync_frame, text="自动同步设置:", font=('Arial', 12, 'bold'), bg='white').pack(anchor='w')
        
        # 自动同步开关
        sync_switch_frame = tk.Frame(auto_sync_frame, bg='white')
        sync_switch_frame.pack(fill='x', pady=5)
        
        self.auto_sync_var = tk.BooleanVar(value=auto_sync)
        auto_sync_check = tk.Checkbutton(sync_switch_frame, text="启用自动同步", 
                                       variable=self.auto_sync_var, font=('Arial', 11), 
                                       bg='white')
        auto_sync_check.pack(side='left')
        
        # 同步间隔设置
        self.interval_frame = tk.Frame(auto_sync_frame, bg='white')
        self.interval_frame.pack(fill='x', pady=5)
        
        tk.Label(self.interval_frame, text="同步间隔(秒):", font=('Arial', 10), bg='white').pack(side='left')
        self.interval_var = tk.StringVar(value=str(sync_interval))
        interval_entry = tk.Entry(self.interval_frame, textvariable=self.interval_var, 
                                font=('Arial', 10), width=8)
        interval_entry.pack(side='left', padx=5)
        
        # 按钮区域
        btn_frame = tk.Frame(main_frame, bg='white', height=80)
        btn_frame.pack(fill='x', pady=20)
        btn_frame.pack_propagate(False)
        
        btn_container = tk.Frame(btn_frame, bg='white')
        btn_container.pack(expand=True)
        
        test_btn = tk.Button(btn_container, text="测试连接", 
                           command=self.test_connection,
                           bg='lightblue', font=('Arial', 14),
                           width=10, height=1)
        test_btn.pack(side='left', padx=10)
        
        save_btn = tk.Button(btn_container, text="保存设置", 
                           command=self.save_config,
                           bg='lightgreen', font=('Arial', 14),
                           width=10, height=1)
        save_btn.pack(side='left', padx=10)
        
        close_btn = tk.Button(btn_container, text="关闭", 
                            command=self.window.destroy,
                            bg='lightcoral', font=('Arial', 14),
                            width=10, height=1)
        close_btn.pack(side='left', padx=10)
    
    def save_config(self):
        secret_id = self.secret_id_entry.get().strip()
        secret_key = self.secret_key_entry.get().strip()
        cos_bucket = self.bucket_entry.get().strip()
        cos_region = self.region_entry.get().strip()
        auto_sync = self.auto_sync_var.get()
        current_class = self.current_class_var.get()
        
        # 处理班级列表
        classes_text = self.classes_text.get('1.0', 'end-1c').strip()
        classes = [cls.strip() for cls in classes_text.split('\n') if cls.strip()]
        if not classes:
            classes = ["720班"]  # 默认班级
        
        # 确保当前班级在班级列表中
        if current_class not in classes:
            current_class = classes[0] if classes else "720班"
        
        try:
            sync_interval = int(self.interval_var.get())
            if sync_interval < 60:
                messagebox.showwarning("提示", "同步间隔不能小于60秒")
                return
        except ValueError:
            messagebox.showwarning("提示", "请输入有效的同步间隔时间（数字）")
            return
        
        config = self.parent.load_config()
        config["secret_id"] = secret_id
        config["secret_key"] = secret_key
        config["cos_bucket"] = cos_bucket
        config["cos_region"] = cos_region
        config["auto_sync"] = auto_sync
        config["sync_interval"] = sync_interval
        config["classes"] = classes
        config["current_class"] = current_class
        
        if self.parent.save_config(config):
            # 重启自动同步
            self.parent.stop_auto_sync()
            self.parent.start_auto_sync()
            
            messagebox.showinfo("成功", "设置已保存！")
            self.parent.update_display()
            self.window.destroy()
        else:
            messagebox.showerror("错误", "保存失败")
    
    def test_connection(self):
        """测试连接"""
        try:
            # 使用用户输入的存储桶信息
            bucket = self.bucket_entry.get().strip() or "class-homework-1257663765"
            region = self.region_entry.get().strip() or "ap-beijing"
            url = f"https://{bucket}.cos.{region}.myqcloud.com/homework_data.json"
            response = requests.head(url, timeout=10)
            
            if response.status_code == 200 or response.status_code == 404:
                messagebox.showinfo("成功", "连接存储桶成功！可以正常同步作业。")
            else:
                messagebox.showerror("错误", f"连接失败: {response.status_code}")
        except Exception as e:
            messagebox.showerror("错误", f"网络连接失败: {str(e)}")

class EditorWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        
        config = self.parent.load_config()
        current_class = config.get("current_class", "720班")
        self.window.title(f"编辑作业内容 - {current_class}")
        
        self.center_window(800, 700)
        self.window.configure(bg='lightgray')
        self.window.attributes('-topmost', True)
        
        self.create_editor()
    
    def center_window(self, width, height):
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_editor(self):
        main_container = tk.Frame(self.window, bg='lightgray')
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        config = self.parent.load_config()
        current_class = config.get("current_class", "720班")
        
        title_label = tk.Label(main_container, text=f"编辑作业内容 - {current_class}", 
                              font=('Arial', 22, 'bold'), bg='lightgray')
        title_label.pack(pady=(0, 15))
        
        content_container = tk.Frame(main_container, bg='lightgray')
        content_container.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(content_container, bg='lightgray', highlightthickness=0)
        scrollbar = tk.Scrollbar(content_container, orient="vertical", command=canvas.yview)
        
        scrollable_frame = tk.Frame(canvas, bg='lightgray')
        scrollable_frame.bind(
            "<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        class_data = self.parent.get_current_class_data()
        subjects = ["语文", "数学", "英语", "科学", "道法", "社会", "晨读"]
        
        self.text_widgets = {}
        
        for i, subject in enumerate(subjects):
            # 晨读特殊样式
            if subject == "晨读":
                frame_bg = 'lightpink'
                label_bg = 'lightcoral'
                label_fg = 'darkred'
                text_bg = 'lightcyan'
            else:
                frame_bg = 'white'
                label_bg = 'lightblue'
                label_fg = 'black'
                text_bg = 'white'
            
            subject_frame = tk.Frame(scrollable_frame, bg=frame_bg, bd=3, relief='solid')
            subject_frame.pack(fill='x', pady=8, padx=5)
            
            subject_label = tk.Label(subject_frame, text=subject, 
                                   font=('Arial', 14, 'bold'),
                                   bg=label_bg,
                                   fg=label_fg,
                                   width=6,
                                   height=2)
            subject_label.pack(side='left', padx=10, pady=10)
            
            content_frame = tk.Frame(subject_frame, bg=frame_bg)
            content_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
            
            current_content = class_data.get(subject, "暂无作业")
            
            # 晨读内容提示
            if subject == "晨读":
                hint_label = tk.Label(content_frame, 
                                    text="晨读内容将在7:50前自动弹出提醒",
                                    font=('Arial', 10, 'italic'),
                                    bg=frame_bg,
                                    fg='blue')
                hint_label.pack(anchor='w')
            
            text_widget = scrolledtext.ScrolledText(content_frame, 
                                                  font=('Arial', 12),
                                                  wrap=tk.WORD,
                                                  width=50,
                                                  height=4 if subject != "晨读" else 3,
                                                  bg=text_bg)
            text_widget.pack(fill='both', expand=True)
            text_widget.insert('1.0', current_content)
            
            self.text_widgets[subject] = text_widget
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        button_frame = tk.Frame(main_container, bg='lightgray', height=80)
        button_frame.pack(fill='x', pady=(15, 0))
        button_frame.pack_propagate(False)
        
        btn_container = tk.Frame(button_frame, bg='lightgray')
        btn_container.pack(expand=True)
        
        # 添加清除全部按钮
        clear_btn = tk.Button(btn_container, text="清除全部", 
                            command=self.clear_all_content,
                            bg='orange', font=('Arial', 16, 'bold'),
                            height=2, width=12)
        clear_btn.pack(side='left', padx=10)
        
        # 保存按钮，同时保存到本地和云端
        save_btn = tk.Button(btn_container, text="保存", 
                           command=self.save_and_upload,
                           bg='lightgreen', font=('Arial', 16, 'bold'),
                           height=2, width=12)
        save_btn.pack(side='left', padx=10)
        
        cancel_btn = tk.Button(btn_container, text="取消", 
                             command=self.window.destroy,
                             bg='lightcoral', font=('Arial', 16, 'bold'),
                             height=2, width=12)
        cancel_btn.pack(side='left', padx=10)
    
    def clear_all_content(self):
        """清除所有科目的内容"""
        if messagebox.askyesno("确认清除", "确定要清除所有科目的作业内容吗？\n此操作不可撤销！"):
            for subject, text_widget in self.text_widgets.items():
                text_widget.delete('1.0', 'end')
                if subject == "晨读":
                    text_widget.insert('1.0', "暂无晨读任务")
                else:
                    text_widget.insert('1.0', "暂无作业")
            messagebox.showinfo("成功", "所有科目内容已清除！")
    
    def save_and_upload(self):
        """同时保存到本地和云端"""
        # 先保存到本地
        class_data = {}
        
        for subject, text_widget in self.text_widgets.items():
            content = text_widget.get('1.0', 'end-1c').strip()
            if subject == "晨读":
                class_data[subject] = content if content else "暂无晨读任务"
            else:
                class_data[subject] = content if content else "暂无作业"
        
        if not self.parent.save_current_class_data(class_data):
            messagebox.showerror("错误", "本地保存失败")
            return
        
        # 然后上传到云端
        config = self.parent.load_config()
        if config.get('secret_id'):
            success, message = self.parent.upload_to_cos()
            if success:
                messagebox.showinfo("成功", "本地保存并云端上传成功！")
                self.parent.update_display()
                self.window.destroy()
            else:
                messagebox.showerror("错误", f"本地保存成功，但云端上传失败：{message}")
        else:
            messagebox.showwarning("提示", "本地保存成功！请先配置腾讯云密钥以启用云端上传")

if __name__ == "__main__":
    app = SimpleHomework()
    app.run()