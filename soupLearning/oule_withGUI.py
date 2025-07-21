import os
import hashlib
import requests
from urllib.parse import urljoin
from subprocess import run, CalledProcessError
import shutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit, QWidget, QFileDialog
from PyQt5.QtCore import Qt
# tts 防错机制
import urllib3
import sys
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 重试机制
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 忽略 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
}

# 创建带有重试机制的会话
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

class M3U8Downloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("M3U8 视频下载工具")
        self.setGeometry(100, 100, 600, 400)

        # 初始化界面
        self.init_ui()

    def init_ui(self):
        # 主窗口布局
        layout = QVBoxLayout()

        # 输入 .m3u8 文件 URL
        self.url_label = QLabel("请输入 .m3u8 文件 URL:")
        self.url_input = QLineEdit()
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)

        # 输入输出视频文件名
        self.output_label = QLabel("请输入输出视频文件名:")
        self.output_input = QLineEdit()
        layout.addWidget(self.output_label)
        layout.addWidget(self.output_input)

        # 是否删除 .ts 文件
        self.delete_ts_checkbox = QCheckBox("是否在生成 .mp4 文件后删除 .ts 文件")
        layout.addWidget(self.delete_ts_checkbox)

        # 日志输出窗口
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        # 下载按钮
        self.download_button = QPushButton("开始下载")
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        # 设置主窗口
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def log(self, message):
        """在日志窗口和终端中输出信息"""
        # 在 PyQt 的日志窗口中显示
        self.log_output.append(message)
        self.log_output.ensureCursorVisible()  # 确保滚动条自动滚动到最新内容
        QApplication.processEvents()  # 强制刷新界面

        # 在终端中显示
        print(message)
        sys.stdout.flush()  # 强制刷新终端输出

    def generate_folder_name(self, url):
        """根据 URL 生成唯一的文件夹名称"""
        hash_object = hashlib.md5(url.encode("utf-8"))
        hash_hex = hash_object.hexdigest()
        return f"video_segments_{hash_hex}"

    def check_ffmpeg_installed(self):
        """检查 ffmpeg 是否安装"""
        try:
            run(["ffmpeg", "-version"], check=True)
            self.log("ffmpeg 已安装")
        except CalledProcessError:
            raise Exception("ffmpeg 未正确安装，请确保 ffmpeg 已添加到系统环境变量中")
        except FileNotFoundError:
            raise Exception("ffmpeg 未安装，请安装 ffmpeg 并添加到系统环境变量中")

    def fetch_m3u8_content(self, m3u8_url, headers):
        """获取 .m3u8 文件内容"""
        with requests.get(m3u8_url, headers=headers) as response:
            if response.status_code == 200:
                self.log("成功获取 m3u8 文件内容")
                return response.text
            else:
                raise Exception(f"请求失败，状态码: {response.status_code}")

    def parse_m3u8_content(self, base_url, m3u8_content):
        """解析 .m3u8 文件内容，提取视频片段 URL"""
        lines = m3u8_content.splitlines()
        ts_urls = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                if line.endswith(".m3u8"):
                    nested_m3u8_url = urljoin(base_url, line)
                    self.log(f"发现嵌套的 m3u8 文件: {nested_m3u8_url}")
                    with requests.get(nested_m3u8_url, headers=HEADERS) as nested_response:
                        if nested_response.status_code == 200:
                            nested_m3u8_content = nested_response.text
                            ts_urls.extend(self.parse_m3u8_content(nested_m3u8_url.rsplit("/", 1)[0] + "/", nested_m3u8_content))
                        else:
                            self.log(f"嵌套 m3u8 文件下载失败: {nested_m3u8_url}")
                else:
                    ts_urls.append(urljoin(base_url, line))
        self.log(f"找到 {len(ts_urls)} 个视频片段")
        return ts_urls


    def download_ts_files(self, ts_urls, headers, folder):
        """下载所有 .ts 文件，支持断点续传并覆盖不完整文件"""
        os.makedirs(folder, exist_ok=True)
        failed_segments = []
        for i, ts_url in enumerate(ts_urls):
            ts_file_path = f"{folder}/segment_{i}.ts"
            if os.path.exists(ts_file_path):
                with requests.head(ts_url, headers=headers) as head_response:
                    if head_response.status_code == 200:
                        remote_file_size = int(head_response.headers.get("Content-Length", 0))
                        local_file_size = os.path.getsize(ts_file_path)
                        if local_file_size == remote_file_size:
                            self.log(f"片段 {i + 1}/{len(ts_urls)} 已完整下载，跳过: {ts_file_path}")
                            continue
                        else:
                            self.log(f"片段 {i + 1}/{len(ts_urls)} 文件不完整，重新下载: {ts_file_path}")
                            os.remove(ts_file_path)
                    else:
                        self.log(f"无法获取远程文件大小，重新下载: {ts_file_path}")
                        os.remove(ts_file_path)
            self.log(f"正在下载片段 {i + 1}/{len(ts_urls)}: {ts_url}")
            with requests.get(ts_url, headers=headers, stream=True) as ts_response:
                if ts_response.status_code == 200:
                    with open(ts_file_path, "wb") as ts_file:
                        for chunk in ts_response.iter_content(chunk_size=1024):
                            ts_file.write(chunk)
                else:
                    self.log(f"片段下载失败: {ts_url}，状态码: {ts_response.status_code}")
                    failed_segments.append(ts_url)
        if failed_segments:
            self.log(f"尝试重新下载失败的片段，共 {len(failed_segments)} 个")
            for ts_url in failed_segments:
                self.log(f"重新下载: {ts_url}")
                with requests.get(ts_url, headers=headers, stream=True) as ts_response:
                    if ts_response.status_code == 200:
                        ts_file_path = f"{folder}/segment_{ts_urls.index(ts_url)}.ts"
                        with open(ts_file_path, "wb") as ts_file:
                            for chunk in ts_response.iter_content(chunk_size=1024):
                                ts_file.write(chunk)
                        self.log(f"重新下载成功: {ts_url}")
                    else:
                        self.log(f"重新下载失败: {ts_url}")
        self.log("所有片段下载完成")

    def merge_ts_files(self, folder, output_video):
        """合并所有 .ts 文件为一个完整的视频"""
        file_list_path = "file_list.txt"
        with open(file_list_path, "w") as file_list:
            for ts_file in sorted(os.listdir(folder)):
                if ts_file.endswith(".ts"):
                    file_list.write(f"file '{folder}/{ts_file}'\n")
        self.log("正在合并视频片段...")
        run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", file_list_path, "-c", "copy", output_video])
        self.log(f"视频已合并为 {output_video}")

    def delete_ts_folder(self, folder):
        """删除 .ts 文件及文件夹"""
        if os.path.exists(folder):
            shutil.rmtree(folder)
            self.log(f"已删除文件夹及其内容: {folder}")
        else:
            self.log(f"文件夹不存在: {folder}")

    def start_download(self):
        """开始下载流程"""
        try:
            m3u8_url = self.url_input.text().strip()
            output_video = self.output_input.text().strip()
            output_video += ".mp4" if not output_video.endswith(".mp4") else ""
            delete_ts_files = self.delete_ts_checkbox.isChecked()

            self.log("检查 ffmpeg 是否安装...")
            self.check_ffmpeg_installed()

            self.log("获取 .m3u8 文件内容...")
            m3u8_content = self.fetch_m3u8_content(m3u8_url, HEADERS)

            self.log("解析 .m3u8 文件内容...")
            base_url = m3u8_url.rsplit("/", 1)[0] + "/"
            ts_urls = self.parse_m3u8_content(base_url, m3u8_content)

            self.log("下载视频片段...")
            folder_name = self.generate_folder_name(m3u8_url)
            self.download_ts_files(ts_urls, HEADERS, folder_name)

            self.log("合并视频片段...")
            self.merge_ts_files(folder_name, output_video)

            if delete_ts_files:
                self.log("删除 .ts 文件...")
                self.delete_ts_folder(folder_name)

            self.log("视频下载和合并完成！")
        except Exception as e:
            self.log(f"发生错误: {e}")


if __name__ == "__main__":
    app = QApplication([])
    window = M3U8Downloader()
    window.show()
    app.exec_()