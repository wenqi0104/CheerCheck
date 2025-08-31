# CheerCheck
基于ai的用户满意度自动分析处理工具

#打包命令(./Tool)--for mac  
## 打包工具为pyinstaller,打包入口文件为run.py

```
pyinstaller --onefile --name "cheerCheck" \
    --add-data "templates:templates" \
    --add-data "static:static" \
    run.py
```