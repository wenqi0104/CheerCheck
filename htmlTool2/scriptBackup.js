// script.js
document.addEventListener("DOMContentLoaded", () => {
  // 输入源选择
  const fileRadio = document.getElementById("fileRadio");
  const urlRadio = document.getElementById("urlRadio");
  // 文件/url文件上传组件
  const fileGroup = document.getElementById("fileGroup");
  const urlGroup = document.getElementById("urlGroup");
  // 额外的prompt输入checkbox 和prompt input
  const promptCheckbox = document.getElementById("promptCheckbox");
  const promptGroup = document.getElementById("promptGroup");
  const promptInput = document.getElementById("promptInput");
  // 文件输入
  const fileInput = document.getElementById("fileInput");
  // 生成结果按钮
  const generateButton = document.getElementById("generateButton");
  // 最后的结果展示区域，初始隐藏
  const resultsSection = document.getElementById("resultsSection");
  const resultsContent = document.getElementById("resultsContent");

  // 切换数据源显示逻辑
  fileRadio.addEventListener("change", () => {
    fileGroup.style.display = "block";
    urlGroup.style.display = "none";
  });

  urlRadio.addEventListener("change", () => {
    fileGroup.style.display = "none";
    urlGroup.style.display = "block";
  });

  // 自定义提示词显示逻辑
  promptCheckbox.addEventListener("change", () => {
    promptGroup.style.display = promptCheckbox.checked ? "block" : "none";
  });

  // 生成改进意见按钮点击事件
  generateButton.addEventListener("click", async () => {
    // 检查是否选择了文件上传方式 并上传了文件
    if (fileRadio.checked && fileInput.files.length === 0) {
      alert("请上传一个文件！");
      return;
    }

    // 显示加载动画 前端渲染结果展示区域
    resultsSection.style.visibility = "visible";
    resultsContent.innerHTML = `
      <div class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">加载中...</span>
        </div>
        <p class="mt-3 mb-0 fs-6">正在分析评论数据并生成改进建议...</p>
      </div>
    `;

    try {
      if (fileRadio.checked) {
        // 处理本地文件上传
        const file = fileInput.files[0];

        // 调用 DeepSeek API 进行分析
        const analysisResult = await callDeepSeekAPI(file);

        // 将结果生成 Excel 文件
        const excelBlob = generateExcelFile(analysisResult);
        downloadFile(excelBlob, "分析结果.xlsx");

        // 更新结果展示区域
        resultsContent.innerHTML = `
          <div class="alert alert-success text-center" role="alert">
            分析完成！结果已下载为 Excel 文件。
          </div>
        `;
      } else {
        alert("目前仅支持本地文件上传方式！");
      }
    } catch (error) {
      console.error("处理失败：", error);
      resultsContent.innerHTML = `
        <div class="alert alert-danger text-center" role="alert">
          分析失败，请稍后重试。
        </div>
      `;
    }
  });

  // 读取文件内容为文本
  function readFileAsText(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (event) => resolve(event.target.result);
      reader.onerror = (error) => reject(error);
      reader.readAsText(file);
    });
  }




  // 调用 DeepSeek API
async function callDeepSeekAPI(file) {
  const apiKey = "sk-7e8ab23cf1124fbb80502138fb3a888a######"; 
  const apiUrl = "https://api.deepseek.com/chat/completions"; 

  // 动态生成 prompt
  const defaultPrompt = `
    分析文件里面内容，分辨出每条意见内容，对部门员工的意见进行分类，
    并且针对每一条意见给出一些建议。
    最后把结果用表格形式输出出来，按照原文件中每条意见的顺序列出。
    表格中的一列严格列出文档中的具体意见，另一列是简述意见内容。
  `;
  const userPrompt = promptCheckbox.checked ? promptInput.value.trim() : defaultPrompt;

  // 读取文件内容为文本
  const fileContent = await readFileAsText(file);

  // 构造 API 请求体
  const requestBody = {
    model: "deepseek-chat",
    messages: [
      { role: "system", content: "您是一个专业的评论分析助手。" },
      { role: "user", content: userPrompt },
      { role: "user", content: `文件内容如下：\n${fileContent}` }
    ],
    stream: false
  };

  // 发起 API 请求
  const response = await fetch(apiUrl, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  });

  // 检查响应状态
  if (!response.ok) {
    throw new Error("DeepSeek API 调用失败");
  }

  // 解析响应数据
  const data = await response.json();
  return JSON.parse(data.choices[0].message.content); // 假设返回的内容是 JSON 格式
}

  // 生成 Excel 文件
  function generateExcelFile(data) {
    const workbook = XLSX.utils.book_new();
    const worksheetData = data.map((item) => ({
      具体意见: item.originalOpinion,
      简述意见内容: item.summary,
    }));
    const worksheet = XLSX.utils.json_to_sheet(worksheetData);
    XLSX.utils.book_append_sheet(workbook, worksheet, "分析结果");
    return XLSX.write(workbook, { bookType: "xlsx", type: "blob" });
  }

  // 下载文件
  function downloadFile(blob, filename) {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  }
});
