
#Tkinker python 改善方案生成

import json
import pandas as pd
from openai import OpenAI
import tkinter as tk
from tkinter import filedialog, messagebox

# DeepSeek API 配置
API_KEY = "sk-7e8ab23cf1124fbb80502138fb3a888a"  # 替换为您的 DeepSeek API 密钥
BASE_URL = "https://api.deepseek.com"  # 替换为实际的 DeepSeek API URL

# 初始化 DeepSeek 客户端
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 定义处理 JSON 文件的函数
def process_json_file():
    # 弹窗选择 JSON 文件
    json_file_path = filedialog.askopenfilename(
        title="Select JSON File",
        filetypes=[("JSON Files", "*.json")]
    )
    if not json_file_path:
        messagebox.showwarning("Warning", "No file selected!")
        return

    # 读取 JSON 文件
    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read JSON file: {str(e)}")
        return

    # 初始化列表以存储处理后的数据
    processed_data = []

    # 遍历 JSON 数据
    for item in data:
        for comment, content in item.items():
            # 调用 DeepSeek API 生成 description
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant, use Simply Chinese to generate content, should less than 30 charactors"},
                        {"role": "user", "content": f"基于以下内容给出中文改善建议，50字以内：{content}"}
                    ],
                    stream=False
                )
                description = response.choices[0].message.content  # 提取生成的建议
            except Exception as e:
                description = f"Error: {str(e)}"  # 如果 API 调用失败，记录错误信息

            # 添加到处理后的数据列表
            processed_data.append({
                "comments": comment,
                "contents": content,
                "suggestions": description
            })

    # 将数据转换为 Pandas DataFrame
    df = pd.DataFrame(processed_data)

    # 弹窗选择保存结果的文件夹
    output_folder = filedialog.askdirectory(title="Select Output Folder")
    if not output_folder:
        messagebox.showwarning("Warning", "No folder selected!")
        return

    # 保存为 Excel 文件
    output_file = f"{output_folder}/comments_with_descriptions.xlsx"
    try:
        df.to_excel(output_file, index=False)
        messagebox.showinfo("Success", f"Excel file generated successfully:\n{output_file}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save Excel file: {str(e)}")

# 创建 GUI 界面
def create_gui():
    # 初始化主窗口
    root = tk.Tk()
    root.title("JSON to Excel Tool")

    # 设置窗口大小
    root.geometry("400x200")

    # 添加标题标签
    title_label = tk.Label(root, text="JSON to Excel Tool", font=("Arial", 16))
    title_label.pack(pady=20)

    # 添加按钮
    generate_button = tk.Button(root, text="Generate", font=("Arial", 14), command=process_json_file)
    generate_button.pack(pady=20)

    # 运行主循环
    root.mainloop()

# 启动 GUI
if __name__ == "__main__":
    create_gui()
    