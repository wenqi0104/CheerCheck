// script.js
document.addEventListener("DOMContentLoaded", () => {
  // 配置管理
  const config = {
    api: {
      baseURL: "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat",
      accessToken: "your_access_token_here", // 需要替换为实际的access token
      model: "eb-instant" // 文心一言的模型名称
    },
    defaultPrompt: `
      分析文件里面内容，分辨出每条意见内容，对部门员工的意见进行分类，
      并且针对每一条意见给出一些建议。
      最后把结果用表格形式输出出来，按照原文件中每条意见的顺序列出。
      表格中的一列严格列出文档中的具体意见，另一列是简述意见内容。
    `
  };

  // API服务类
  class WenxinApiService {
    constructor(config) {
      this.config = config;
    }

    async callAPI(prompt, fileContent) {
      const url = `${this.config.api.baseURL}/${this.config.api.model}?access_token=${this.config.api.accessToken}`;
      
      const messages = [
        { role: "system", content: "您是一个专业的评论分析助手。" },
        { role: "user", content: prompt },
        { role: "user", content: `文件内容如下：\n${fileContent}` }
      ];

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ messages }),
        });

        if (!response.ok) {
          throw new Error(`API请求失败: ${response.status}`);
        }

        const data = await response.json();
        if (data.error_code) {
          throw new Error(`API错误: ${data.error_msg}`);
        }

        return this._parseResponse(data.result);
      } catch (error) {
        console.error("API调用错误:", error);
        throw error;
      }
    }

    _parseResponse(responseContent) {
      try {
        // 尝试解析JSON格式的响应
        return JSON.parse(responseContent);
      } catch (e) {
        // 如果不是JSON，直接返回文本
        return { result: responseContent };
      }
    }
  }

  // 初始化UI元素
  const fileRadio = document.getElementById("fileRadio");
  const urlRadio = document.getElementById("urlRadio");
  const fileGroup = document.getElementById("fileGroup");
  const urlGroup = document.getElementById("urlGroup");
  const promptCheckbox = document.getElementById("promptCheckbox");
  const promptGroup = document.getElementById("promptGroup");
  const promptInput = document.getElementById("promptInput");
  const fileInput = document.getElementById("fileInput");
  const generateButton = document.getElementById("generateButton");
  const resultsSection = document.getElementById("resultsSection");
  const resultsContent = document.getElementById("resultsContent");

  // UI事件处理
  fileRadio.addEventListener("change", () => {
    fileGroup.style.display = "block";
    urlGroup.style.display = "none";
  });

  urlRadio.addEventListener("change", () => {
    fileGroup.style.display = "none";
    urlGroup.style.display = "block";
  });

  promptCheckbox.addEventListener("change", () => {
    promptGroup.style.display = promptCheckbox.checked ? "block" : "none";
  });

  // 文件读取工具函数
  const readFileAsText = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => resolve(event.target.result);
    reader.onerror = (error) => reject(error);
    reader.readAsText(file);
  });

  // 生成Excel文件
  const generateExcelFile = (data) => {
    const workbook = XLSX.utils.book_new();
    const worksheetData = data.map((item) => ({
      具体意见: item.originalOpinion,
      简述意见内容: item.summary,
    }));
    const worksheet = XLSX.utils.json_to_sheet(worksheetData);
    XLSX.utils.book_append_sheet(workbook, worksheet, "分析结果");
    return XLSX.write(workbook, { bookType: "xlsx", type: "blob" });
  };

  // 下载文件
  const downloadFile = (blob, filename) => {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  // 显示加载状态
  const showLoading = (message = "正在处理...") => {
    resultsSection.style.visibility = "visible";
    resultsContent.innerHTML = `
      <div class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">加载中...</span>
        </div>
        <p class="mt-3 mb-0 fs-6">${message}</p>
      </div>
    `;
  };

  // 显示错误信息
  const showError = (message) => {
    resultsContent.innerHTML = `
      <div class="alert alert-danger text-center" role="alert">
        ${message}
      </div>
    `;
  };

  // 显示成功信息
  const showSuccess = (message) => {
    resultsContent.innerHTML = `
      <div class="alert alert-success text-center" role="alert">
        ${message}
      </div>
    `;
  };

  // 主处理函数
  generateButton.addEventListener("click", async () => {
    if (fileRadio.checked && fileInput.files.length === 0) {
      alert("请上传一个文件！");
      return;
    }

    if (!fileRadio.checked) {
      showError("目前仅支持本地文件上传方式！");
      return;
    }

    showLoading("正在分析评论数据并生成改进建议...");

    try {
      const file = fileInput.files[0];
      const fileContent = await readFileAsText(file);
      
      // 获取prompt
      const prompt = promptCheckbox.checked 
        ? promptInput.value.trim() 
        : config.defaultPrompt;

      // 初始化API服务
      const apiService = new WenxinApiService(config);
      
      // 调用API
      const analysisResult = await apiService.callAPI(prompt, fileContent);
      
      // 处理结果并下载
      const excelBlob = generateExcelFile(analysisResult);
      downloadFile(excelBlob, "分析结果.xlsx");
      
      showSuccess("分析完成！结果已下载为 Excel 文件。");
    } catch (error) {
      console.error("处理失败：", error);
      showError(`分析失败: ${error.message || "请稍后重试"}`);
    }
  });
});