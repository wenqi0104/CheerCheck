import os
import requests
import base64
import re
import json
from openai import OpenAI

# 文心一言文档解析模型：https://ai.baidu.com/ai-doc/OCR/Klxag8wiy
# 1.提交请求，结果会输出在json中，获取json里的result.task_id
def create_task(url, file_path, file_url):
    """
    Args:
        url: string, 服务请求链接
        file_path: 本地文件路径
        file_url: 文件链接
    Returns: 响应
    """
    # 文件请求
    with open(file_path, "rb") as f:
        file_data = base64.b64encode(f.read())
    data = {
        "file_data": file_data,
        "file_url": file_url,
        "file_name": os.path.basename(file_path)
    }
    
    # 文档切分参数，非必传
    # return_doc_chunks = json.dumps({"switch": True, "chunk_size": -1})
    # data["return_doc_chunks"] = return_doc_chunks
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(url, headers=headers, data=data)
    return response

# 2.将请求结果的task_id 输入到获取结果里，输出结果如下，取其中的markdown_url，之后需要用方法转存markdown内容，喂给deepseek
# 如下为运行出来的结果eg：
## {'log_id': '11351417030026975614803050383398', 'error_code': 0, 'error_msg': '', 'result': {'task_id': 'task-Czn4Kc4UVwgH7tSP6F7g4n9CNDx50yH1', 'status': 'success', 'task_error': None, 'parse_result_url': 'https://xmind-parser.bj.bcebos.com/cloud/parseResult//task-Czn4Kc4UVwgH7tSP6F7g4n9CNDx50yH1/file-HuQsMyfHtpEaByf7m8OTR7e1wnUPHwjr.json?authorization=bce-auth-v1%2FALTAK7IDj758EUbA1igu04rHAh%2F2025-07-23T03%3A10%3A01Z%2F259200%2F%2F7db3165faceeb2e2cbd1604295745b74f502b80738037cefac53c8126020e13e', 'markdown_url': 'https://xmind-parser.bj.bcebos.com/cloud/parseResult//task-Czn4Kc4UVwgH7tSP6F7g4n9CNDx50yH1/file-HuQsMyfHtpEaByf7m8OTR7e1wnUPHwjr.md?authorization=bce-auth-v1%2FALTAK7IDj758EUbA1igu04rHAh%2F2025-07-23T03%3A10%3A01Z%2F259200%2F%2F35e638c3415d3daf333486e789e73b2968e887e6a8397d0ac5f2278851ed63e0'}}
def query_task(url, task_id):
    """
    Args:
        url: string, 请求链接
        task_id: string, task id
    Returns: 响应
    """
    data = {
        "task_id": task_id
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    print(url)
    response = requests.post(url, headers=headers, data=data)
    return response

# 3.将markdown url 下载转存成markdown str，之后喂给deepseek接口即可
def fetch_and_clean_markdown(markdown_url):
    """
    从指定的 URL 获取 Markdown 内容并清理异常值。

    参数:
        markdown_url (str): Markdown 文件的 URL。

    返回:
        str: 清理后的 Markdown 内容。如果请求失败或发生错误，返回错误信息。
    """
    try:
        # 发送 GET 请求
        response = requests.get(markdown_url)
        response.encoding = 'utf-8'
        
        # 检查请求是否成功
        if response.status_code == 200:
            # 获取 Markdown 内容
            markdown_content = response.text
            
            # 清理 Markdown 内容中的 HTML 标签
            clean_markdown_content = re.sub(r'<[^>]*>', '', markdown_content)
            
            return clean_markdown_content
        else:
            return f"请求失败，状态码：{response.status_code}"
    except Exception as e:
        return f"发生错误：{e}"

# 4.deepseek 处理markdown
def call_deepseek_api(markdown_content):
    """
    调用 DeepSeek API 分析 Markdown 内容，并生成表格形式的结果。
    
    参数:
        markdown_content (str): Markdown 文件内容。
    
    返回:
        list: 表格形式的结果，每行是一个字典，包含 '具体意见' 和 '简述意见内容'。
    """
    # DeepSeek API 的 URL 和 API 密钥
    api_key = "sk-7e8ab23cf1124fbb80502138fb3a888a"  # 替换为你的 API 密钥
    api_url = "https://api.deepseek.com/chat/completions"
    
    # 动态生成 prompt
    default_prompt = """
    分析文件里面内容，分辨出每条意见内容，对部门员工的意见进行分类，
    并且针对每一条意见给出一些建议。
    最后把结果用表格形式输出出来，按照原文件中每条意见的顺序列出。
    表格中的一列严格列出文档中的具体意见，另一列是简述意见内容。
    """
    
    # 构造 API 请求体
    request_body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "您是一个专业的评论分析助手。"},
            {"role": "user", "content": default_prompt},
            {"role": "user", "content": f"文件内容如下：\n{markdown_content}"}
        ],
        "stream": False
    }
    
    # 发起 API 请求
    response = requests.post(api_url, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }, json=request_body)
    
    # 检查响应状态
    if response.status_code == 200:
        # 解析响应数据
        data = response.json()
        try:
            # 假设返回的内容是 JSON 格式
            table_data = data["choices"][0]["message"]["content"]
            return table_data
        except KeyError:
            print("响应数据格式不正确")
            return []
    else:
        print(f"DeepSeek API 请求失败，状态码: {response.status_code}")
        print(f"错误信息: {response.text}")
        return []

# 主函数
def main(file_path, request_host, request_host2):
 
    # Step 1: OCR 识别文件内容    
    # 拿到task id
    # response = create_task(request_host, file_path, "")
    # response_data = response.json()
    # task_id = response_data["result"]["task_id"]
    # print('task_id:',task_id)
    # print(response_data)
    # print('--------------------------')

    #测试用task_id: 
    # task_id = 'task-yjSerT5twFZgcflRKk22gi3TQGZ0dWhp'
    task_id = 'task-Czn4Kc4UVwgH7tSP6F7g4n9CNDx50yH1'
    

    # # 用task id 拿markdown url
    response2 = query_task(request_host2, task_id)
    response2_data = response2.json()
    markdown_url = response2_data["result"]["markdown_url"]
    print("markdown_url:",markdown_url)
    print(response2_data)
    print('--------------------------')
    # # 测试mk_url
    # # markdown_url = "https://xmind-parser.bj.bcebos.com/cloud/parseResult//task-Czn4Kc4UVwgH7tSP6F7g4n9CNDx50yH1/file-HuQsMyfHtpEaByf7m8OTR7e1wnUPHwjr.md?authorization=bce-auth-v1%2FALTAK7IDj758EUbA1igu04rHAh%2F2025-07-23T03%3A10%3A01Z%2F259200%2F%2F35e638c3415d3daf333486e789e73b2968e887e6a8397d0ac5f2278851ed63e0"
    
    # # python 处理markdown link转存为markdown内容
    clean_markdown_content = fetch_and_clean_markdown(markdown_url) 
    print('等待结果生成中：')

    # # Step 2: 表格内容分发给Deepseek生成结果
    table_result = call_deepseek_api(clean_markdown_content)
    if table_result:
        print('--------------------------------------')
        print("表格结果:",table_result)
        print('--------------------------------------')
    else:
        print("未能生成表格结果。")


# 示例调用
if __name__ == "__main__":
    # 替换为你的文件路径、文心一言和 DeepSeek 的访问令牌
    # access_token = "24.f8181834e0100bf1ca4ee64ed17b9950.2592000.1755831652.282335-119570165####"
    request_host = "https://aip.baidubce.com/rest/2.0/brain/online/v2/parser/task?" \
    "access_token=24.f8181834e0100bf1ca4ee64ed17b9950.2592000.1755831652.282335-119570165"
    request_host2 = "https://aip.baidubce.com/rest/2.0/brain/online/v2/parser/task/query?access_token=24.f8181834e0100bf1ca4ee64ed17b9950.2592000.1755831652.282335-119570165"

    file_path = "Tool3/研发意见_test.pdf"
    # task_id = 'task-Czn4Kc4UVwgH7tSP6F7g4n9CNDx50yH1'

    main(file_path, request_host, request_host2)