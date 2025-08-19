# app.py
from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from utils import backend_methods  # 假设您把处理逻辑放在这里

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 限制

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_data():
    data = request.form
    data_source = data.get('dataSource')
    manualPrompt = data.get('prompt', '').strip()

    # 临时存储文本数据（用于AI处理）
    raw_text = ""

    # if data_source == 'url':
    #     url = data.get('url')
    #     if not url:
    #         return jsonify({'error': 'URL 不能为空'}), 400
    #     # 调用您已有的方法抓取网页评论（示例）
    #     raw_text = backend_methods.scrape_comments_from_url(url)

    # elif data_source == 'file':
    #     if 'file' not in request.files:
    #         return jsonify({'error': '未上传文件'}), 400
    #     file = request.files['file']
    #     if file.filename == '':
    #         return jsonify({'error': '未选择文件'}), 400
    #     if file and allowed_file(file.filename):

    #         # 这里是保存文件的
    #         filename = secure_filename(file.filename)
    #         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    #         file.save(filepath)
    #         # 输入源文件处理
    #         raw_text = backend_methods.excel_to_markdown_with_merged_cells(filepath)

    #         # 可选：处理完删除临时文件
    #         os.remove(filepath)

    #     else:
    #         return jsonify({'error': '不支持的文件类型'}), 400

    # else:
    #     return jsonify({'error': '无效的数据来源'}), 400

    if data_source == 'url':
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL 不能为空'}), 400
        # 调用您已有的方法抓取网页评论（示例）
        raw_text = backend_methods.scrape_comments_from_url(url)

    elif data_source == 'file':
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            file_ext = filename.rsplit('.', 1)[1].lower()

            try:
                if file_ext in ['xls', 'xlsx']:
                    # Excel 处理流程
                    raw_text = backend_methods.excel_to_markdown_with_merged_cells(filepath)

                elif file_ext == 'pdf':
                    # PDF 处理流程
                    request_host = "https://aip.baidubce.com/rest/2.0/brain/online/v2/parser/task?"
                    request_host2 = "https://aip.baidubce.com/rest/2.0/brain/online/v2/parser/task/query?access_token=24.f8181834e0100bf1ca4ee64ed17b9950.2592000.1755831652.282335-119570165"

                    # Step 1: OCR 识别文件内容
                    response = backend_methods.create_task(request_host, filepath, "")
                    response_data = response.json()
                    if "result" not in response_data or "task_id" not in response_data["result"]:
                        return jsonify({'error': 'OCR 任务创建失败'}), 500
                    task_id = response_data["result"]["task_id"]
                    print('task_id:', task_id)

                    # Step 2: 用 task_id 获取 markdown_url
                    response2 = backend_methods.query_task(request_host2, task_id)
                    response2_data = response2.json()
                    if "result" not in response2_data or "markdown_url" not in response2_data["result"]:
                        return jsonify({'error': '未获取到 markdown_url'}), 500
                    markdown_url = response2_data["result"]["markdown_url"]
                    print("markdown_url:", markdown_url)

                    # Step 3: 下载并清洗 markdown 内容
                    raw_text = backend_methods.fetch_and_clean_markdown(markdown_url)

                else:
                    return jsonify({'error': '不支持的文件类型'}), 400

            finally:
                # 确保删除临时文件
                if os.path.exists(filepath):
                    os.remove(filepath)

        else:
            return jsonify({'error': '不支持的文件类型'}), 400

    # 调用您的 AI 方法生成建议
    try:
        # 调接口处理md的raw data
        print('------------>等待结果生成中：')
        table_result = backend_methods.call_deepseek_api(raw_text,manualPrompt)

        if table_result:
            print('--------------------------------------')
            print('manualPrompt:',manualPrompt)
            print('--------------------------------------')
            filtered_table = backend_methods.filter_markdown_table(table_result)
            print("表格结果:",filtered_table)
            # 调用方法保存文件
            backend_methods.save_markdown_to_file(filtered_table)
            backend_methods.markdown_to_excel_with_style(filtered_table)
            print('--------------------------------------')
        else:
            print("未能生成表格结果。")

        return jsonify({'suggestions': filtered_table})
    except Exception as e:
        return jsonify({'error': f'生成建议失败: {str(e)}'}), 500

if __name__ == '__main__':
    app.run()