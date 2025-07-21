import os
import hashlib
import requests
from urllib.parse import urljoin
from subprocess import run, CalledProcessError
import shutil
# tts 防错机制
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 重试机制
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 忽略 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置
M3U8_URL = input("请输入 .m3u8 文件 URL: ")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
}
OUTPUT_VIDEO = input("请输入输出视频文件名: ")
OUTPUT_VIDEO += ".mp4" if not OUTPUT_VIDEO.endswith(".mp4") else ""

# 在开始时询问是否删除 .ts 文件
DELETE_TS_FILES = input("是否在生成 .mp4 文件后删除 .ts 文件？(y/n): ").strip().lower() == "y"

def generate_folder_name(url):
    """根据 URL 生成唯一的文件夹名称"""
    hash_object = hashlib.md5(url.encode("utf-8"))
    hash_hex = hash_object.hexdigest()
    return f"video_segments_{hash_hex}"


SEGMENTS_FOLDER = generate_folder_name(M3U8_URL)  # 根据 URL 生成文件夹名称


def check_ffmpeg_installed():
    """检查 ffmpeg 是否安装"""
    try:
        run(["ffmpeg", "-version"], check=True)
        print("ffmpeg 已安装")
    except CalledProcessError:
        raise Exception("ffmpeg 未正确安装，请确保 ffmpeg 已添加到系统环境变量中")
    except FileNotFoundError:
        raise Exception("ffmpeg 未安装，请安装 ffmpeg 并添加到系统环境变量中")


def fetch_m3u8_content(m3u8_url, headers):
    """获取 .m3u8 文件内容"""
    # response = requests.get(m3u8_url, headers=headers)
    with requests.get(m3u8_url, headers=headers) as response:
        if response.status_code == 200:
            print("成功获取 m3u8 文件内容")
            return response.text
        else:
            raise Exception(f"请求失败，状态码: {response.status_code}")


def parse_m3u8_content(base_url, m3u8_content):
    """解析 .m3u8 文件内容，提取视频片段 URL"""
    lines = m3u8_content.splitlines()
    ts_urls = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            # 如果是嵌套的 .m3u8 文件，递归解析
            if line.endswith(".m3u8"):
                nested_m3u8_url = urljoin(base_url, line)
                print(f"发现嵌套的 m3u8 文件: {nested_m3u8_url}")
                # nested_m3u8_content = fetch_m3u8_content(nested_m3u8_url, HEADERS)
                # ts_urls.extend(parse_m3u8_content(nested_m3u8_url.rsplit("/", 1)[0] + "/", nested_m3u8_content))
                with requests.get(nested_m3u8_url, headers=HEADERS) as nested_response:
                    if nested_response.status_code == 200:
                        nested_m3u8_content = nested_response.text
                        ts_urls.extend(parse_m3u8_content(nested_m3u8_url.rsplit("/", 1)[0] + "/", nested_m3u8_content))
                    else:
                        print(f"嵌套 m3u8 文件下载失败: {nested_m3u8_url}")
            else:
                ts_urls.append(urljoin(base_url, line))
    print(f"找到 {len(ts_urls)} 个视频片段")
    return ts_urls

# 创建带有重试机制的会话
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def download_ts_files(ts_urls, headers, folder):
    """下载所有 .ts 文件，支持断点续传并覆盖不完整文件"""
    os.makedirs(folder, exist_ok=True)
    failed_segments = []  # 记录下载失败的片段
    for i, ts_url in enumerate(ts_urls):
        ts_file_path = f"{folder}/segment_{i}.ts"
        # 检查文件是否已存在
        if os.path.exists(ts_file_path):
            # 检查文件大小是否完整（通过 HEAD 请求获取文件大小）
            # head_response = requests.head(ts_url, headers=headers)
            with requests.head(ts_url, headers=headers) as head_response:
                if head_response.status_code == 200:
                    remote_file_size = int(head_response.headers.get("Content-Length", 0))
                    local_file_size = os.path.getsize(ts_file_path)
                    if local_file_size == remote_file_size:
                        print(f"片段 {i + 1}/{len(ts_urls)} 已完整下载，跳过: {ts_file_path}")
                        continue
                    else:
                        print(f"片段 {i + 1}/{len(ts_urls)} 文件不完整，重新下载: {ts_file_path}")
                        os.remove(ts_file_path)  # 删除不完整文件
                else:
                    print(f"无法获取远程文件大小，重新下载: {ts_file_path}")
                    os.remove(ts_file_path)  # 删除文件以重新下载
        # 下载文件
        print(f"正在下载片段 {i + 1}/{len(ts_urls)}: {ts_url}")

        # ts_response = requests.get(ts_url, headers=headers, stream=True)
        with requests.get(ts_url, headers=headers, stream=True, verify=False) as ts_response:
            if ts_response.status_code == 200:
                with open(ts_file_path, "wb") as ts_file:
                    for chunk in ts_response.iter_content(chunk_size=1024):
                        ts_file.write(chunk)
            else:
                print(f"片段下载失败: {ts_url}，状态码: {ts_response.status_code}")
                failed_segments.append(ts_url)  # 记录失败的片段
    # 尝试重新下载失败的片段
    if failed_segments:
        print(f"尝试重新下载失败的片段，共 {len(failed_segments)} 个")
        for ts_url in failed_segments:
            print(f"重新下载: {ts_url}")
            # ts_response = requests.get(ts_url, headers=headers, stream=True)
            with requests.get(ts_url, headers=headers, stream=True, verify=False) as ts_response:
                if ts_response.status_code == 200:
                    ts_file_path = f"{folder}/segment_{ts_urls.index(ts_url)}.ts"
                    with open(ts_file_path, "wb") as ts_file:
                        for chunk in ts_response.iter_content(chunk_size=1024):
                            ts_file.write(chunk)
                    print(f"重新下载成功: {ts_url}")
                else:
                    print(f"重新下载失败: {ts_url}")
    print("所有片段下载完成")

# def merge_ts_files(folder, output_video):
#     """合并所有 .ts 文件为一个完整的视频"""
#     # 生成文件列表
#     file_list_path = "file_list.txt"
#     with open(file_list_path, "w") as file_list:
#         for ts_file in sorted(os.listdir(folder)):
#             # 仅处理 .ts 文件
#             if ts_file.endswith(".ts"):
#                 file_list.write(f"file '{folder}/{ts_file}'\n")
    
#     # 使用 ffmpeg 合并
#     print("正在合并视频片段...")
#     run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", file_list_path, "-c", "copy", output_video])
#     print(f"视频已合并为 {output_video}")
def merge_ts_files(self, folder, output_video):
    """合并所有 .ts 文件为一个完整的视频"""
    file_list_path = "file_list.txt"
    try:
        # 创建 file_list.txt 文件
        with open(file_list_path, "w") as file_list:
            for ts_file in sorted(os.listdir(folder)):
                if ts_file.endswith(".ts"):
                    file_list.write(f"file '{folder}/{ts_file}'\n")
        
        # 合并视频片段
        self.log("正在合并视频片段...")
        run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", file_list_path, "-c", "copy", output_video])
        self.log(f"视频已合并为 {output_video}")
    except Exception as e:
        self.log(f"合并视频时发生错误: {e}")
    finally:
        # 删除 file_list.txt 文件
        if os.path.exists(file_list_path):
            os.remove(file_list_path)
            self.log("已删除临时文件: file_list.txt")

def delete_ts_folder(folder):
    """删除 .ts 文件及文件夹"""
    if os.path.exists(folder):
        shutil.rmtree(folder)  # 递归删除文件夹及其内容
        print(f"已删除文件夹及其内容: {folder}")
    else:
        print(f"文件夹不存在: {folder}")

def main():
    try:
        # 检查 ffmpeg 是否安装
        check_ffmpeg_installed()
        
        # 获取 .m3u8 文件内容
        m3u8_content = fetch_m3u8_content(M3U8_URL, HEADERS)
        
        # 解析 .m3u8 文件内容
        base_url = M3U8_URL.rsplit("/", 1)[0] + "/"  # 获取 .m3u8 文件的基础路径
        ts_urls = parse_m3u8_content(base_url, m3u8_content)
        
        # 下载视频片段（支持断点续传并覆盖不完整文件）
        download_ts_files(ts_urls, HEADERS, SEGMENTS_FOLDER)
        
        # 合并视频片段
        merge_ts_files(SEGMENTS_FOLDER, OUTPUT_VIDEO)
        print("视频下载和合并完成！")

        # 根据用户选择删除 .ts 文件
        if DELETE_TS_FILES:
            delete_ts_folder(SEGMENTS_FOLDER)
        
        print("视频下载和合并完成！")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()