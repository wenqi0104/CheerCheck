from app import app  # 导入你的 Flask 应用实例

if __name__ == '__main__':
    # 启动 Flask 服务（可自定义端口）
    app.run(host='127.0.0.1', port=5000, debug=False)