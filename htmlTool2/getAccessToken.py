
# encoding:utf-8
# access_token = 24.f0d107b2864bf642c7bd34eb56782aff.2592000.1755694468.282335-119570165

# {'log_id': '11351417030026975614803050383398', 'error_code': 0, 'error_msg': '', 'result': {'task_id': 'task-Czn4Kc4UVwgH7tSP6F7g4n9CNDx50yH1', 'status': 'success', 'task_error': None, 'parse_result_url': 'https://xmind-parser.bj.bcebos.com/cloud/parseResult//task-Czn4Kc4UVwgH7tSP6F7g4n9CNDx50yH1/file-HuQsMyfHtpEaByf7m8OTR7e1wnUPHwjr.json?authorization=bce-auth-v1%2FALTAK7IDj758EUbA1igu04rHAh%2F2025-07-23T03%3A10%3A01Z%2F259200%2F%2F7db3165faceeb2e2cbd1604295745b74f502b80738037cefac53c8126020e13e', 'markdown_url': 'https://xmind-parser.bj.bcebos.com/cloud/parseResult//task-Czn4Kc4UVwgH7tSP6F7g4n9CNDx50yH1/file-HuQsMyfHtpEaByf7m8OTR7e1wnUPHwjr.md?authorization=bce-auth-v1%2FALTAK7IDj758EUbA1igu04rHAh%2F2025-07-23T03%3A10%3A01Z%2F259200%2F%2F35e638c3415d3daf333486e789e73b2968e887e6a8397d0ac5f2278851ed63e0'}}
import requests
import os
import base64
import json


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



# def main():
        
#     url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=K4w7faNOpXRqKpZezSBx3uok&client_secret=GCbC9ZSltg2SjlNW0XNsqbXzw97GOK8D"
    
#     payload = ""
#     headers = {
#         'Content-Type': 'application/json',
#         'Accept': 'application/json'
#     }
    
#     response = requests.request("POST", url, headers=headers, data=payload)
    
#     print(response.text)
    

# if __name__ == '__main__':
#     main()

if __name__ == '__main__':
    request_host = "https://aip.baidubce.com/rest/2.0/brain/online/v2/parser/task?" \
    "access_token=24.f8181834e0100bf1ca4ee64ed17b9950.2592000.1755831652.282335-119570165"
    file_path = "Tool3/研发意见_test.pdf"
    response = create_task(request_host, file_path, "")
    print(response.json())

