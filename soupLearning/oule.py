import os
import requests
from urllib.parse import urljoin
from subprocess import run, CalledProcessError

# 配置
M3U8_URL = "https://europe.olemovienews.com/ts4/20250709/iwbefcc3/mp4/iwbefcc3.mp4/index-v1-a1.m3u8"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
}
OUTPUT_VIDEO = "output.mp4"
SEGMENTS_FOLDER = "video_segments"

def check_ffmpeg_installed():
    """检查 ffmpeg 是否安装"""
    try:
        run(["ffmpeg", "-version"], check=True)
        print("ffmpeg 已安装")
    except CalledProcessError:
        raise Exception("ffmpeg 未正确安装，请确保 ffmpeg 已添加到系统环境变量中")
    except FileNotFoundError:
        raise Exception("ffmpeg 未安装，请安装 ffmpeg 并添加到系统环境变量中")

def download_m3u8_file(m3u8_url, headers):
    """下载 .m3u8 文件"""
    response = requests.get(m3u8_url, headers=headers)
    if response.status_code == 200:
        with open("master.m3u8", "w") as file:
            file.write(response.text)
        print("m3u8 文件已成功下载")
    else:
        raise Exception(f"请求失败，状态码: {response.status_code}")

def parse_m3u8_file(base_url, m3u8_path="master.m3u8"):
    """解析 .m3u8 文件，提取视频片段 URL"""
    with open(m3u8_path, "r") as file:
        lines = file.readlines()
    ts_urls = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            # 如果是嵌套的 .m3u8 文件，递归解析
            if line.endswith(".m3u8"):
                nested_m3u8_url = urljoin(base_url, line)
                print(f"发现嵌套的 m3u8 文件: {nested_m3u8_url}")
                nested_m3u8_response = requests.get(nested_m3u8_url, headers=HEADERS)
                if nested_m3u8_response.status_code == 200:
                    nested_m3u8_path = "nested.m3u8"
                    with open(nested_m3u8_path, "w") as nested_file:
                        nested_file.write(nested_m3u8_response.text)
                    ts_urls.extend(parse_m3u8_file(nested_m3u8_url.rsplit("/", 1)[0] + "/", nested_m3u8_path))
                else:
                    print(f"嵌套 m3u8 文件下载失败: {nested_m3u8_url}")
            else:
                ts_urls.append(urljoin(base_url, line))
    print(f"找到 {len(ts_urls)} 个视频片段")
    return ts_urls

def download_ts_files(ts_urls, headers, folder):
    """下载所有 .ts 文件"""
    os.makedirs(folder, exist_ok=True)
    for i, ts_url in enumerate(ts_urls):
        print(f"正在下载片段 {i + 1}/{len(ts_urls)}: {ts_url}")
        ts_response = requests.get(ts_url, headers=headers)
        if ts_response.status_code == 200:
            with open(f"{folder}/segment_{i}.ts", "wb") as ts_file:
                ts_file.write(ts_response.content)
        else:
            print(f"片段下载失败: {ts_url}，状态码: {ts_response.status_code}")
    print("所有片段下载完成")

def merge_ts_files(folder, output_video):
    """合并所有 .ts 文件为一个完整的视频"""
    # 生成文件列表
    file_list_path = "file_list.txt"
    with open(file_list_path, "w") as file_list:
        for ts_file in sorted(os.listdir(folder)):
            file_list.write(f"file '{folder}/{ts_file}'\n")
    
    # 使用 ffmpeg 合并
    print("正在合并视频片段...")
    run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", file_list_path, "-c", "copy", output_video])
    print(f"视频已合并为 {output_video}")

def main():
    try:
        # 检查 ffmpeg 是否安装
        check_ffmpeg_installed()
        
        # 下载 .m3u8 文件
        download_m3u8_file(M3U8_URL, HEADERS)
        
        # 解析 .m3u8 文件
        base_url = M3U8_URL.rsplit("/", 1)[0] + "/"  # 获取 .m3u8 文件的基础路径
        ts_urls = parse_m3u8_file(base_url)
        
        # 下载视频片段
        download_ts_files(ts_urls, HEADERS, SEGMENTS_FOLDER)
        
        # 合并视频片段
        merge_ts_files(SEGMENTS_FOLDER, OUTPUT_VIDEO)
        
        print("视频下载和合并完成！")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()