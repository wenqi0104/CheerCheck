// static/script.js
document.addEventListener("DOMContentLoaded", function () {
  const urlRadio = document.getElementById("urlRadio");
  const fileRadio = document.getElementById("fileRadio");
  const urlGroup = document.getElementById("urlGroup");
  const fileGroup = document.getElementById("fileGroup");
  const promptCheckbox = document.getElementById("promptCheckbox");
  const promptGroup = document.getElementById("promptGroup");
  const resultsSection = document.getElementById("resultsSection");
  const resultsContent = document.getElementById("resultsContent");
  const organizeButton = document.getElementById("organizeDataButton");
  const generateButton = document.getElementById("generateButton");

  // 切换数据源
  urlRadio.addEventListener("change", () => {
    urlGroup.style.display = "block";
    fileGroup.style.display = "none";
  });
  fileRadio.addEventListener("change", () => {
    urlGroup.style.display = "none";
    fileGroup.style.display = "block";
  });

  // 切换提示词
  promptCheckbox.addEventListener("change", () => {
    promptGroup.style.display = promptCheckbox.checked ? "block" : "none";
  });

  // 一键整理数据（可选功能，比如预览/清洗）
  organizeButton.addEventListener("click", () => {
    alert("数据正在整理...");
    // 可添加预处理逻辑
  });

  // 生成改进建议
  generateButton.addEventListener("click", async () => {
    const formData = new FormData();
    const dataSource = document.querySelector(
      'input[name="dataSource"]:checked'
    ).value;
    const prompt = document.getElementById("promptInput").value;

    formData.append("dataSource", dataSource);
    if (dataSource === "url") {
      const url = document.getElementById("urlInput").value.trim();
      if (!url) {
        alert("请输入有效的 URL");
        return;
      }
      formData.append("url", "https://" + url.replace(/^https?:\/\//, ""));
    } else if (dataSource === "file") {
      const fileInput = document.getElementById("fileInput");
      if (!fileInput.files.length) {
        alert("请上传文件");
        return;
      }
      formData.append("file", fileInput.files[0]);
    }

    if (promptCheckbox.checked && prompt) {
      formData.append("prompt", prompt);
    }
    // 原请求+结果直接输出
    // try {
    //     const response = await fetch('/process', {
    //         method: 'POST',
    //         body: formData
    //     });

    //     const result = await response.json();

    //     if (result.error) {
    //         resultsContent.innerHTML = `<div class="alert alert-danger">${result.error}</div>`;
    //     } else {
    //         // 这里直接把formData传入接口，有result后前端模板渲染返回结果。
    //         // 后端要同步生成并下载文件 ！！！！！！
    //         resultsContent.innerHTML = result.suggestions;
    //         resultsSection.style.visibility = 'visible';
    //         resultsSection.scrollIntoView({ behavior: 'smooth' });
    //     }
    // } catch (err) {
    //     resultsContent.innerHTML = `<div class="alert alert-danger">请求失败: ${err.message}</div>`;
    //     resultsSection.style.visibility = 'visible';
    // }

    // markdown结果前端渲染
    try {
      const response = await fetch("/process", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      if (result.error) {
        resultsContent.innerHTML = `<div class="alert alert-danger">${result.error}</div>`;
      } else {
        // 1. 把 Markdown 转成 HTML
        let html = marked.parse(result.suggestions);

        // 2. 给表格加上 Bootstrap 样式
        html = html.replace(
          /<table>/g,
          '<table class="table table-bordered table-striped table-hover table-sm m-0">'
        );

        // 3. 包一层响应式容器
        resultsContent.innerHTML = `<div class="table-responsive">${html}</div>`;

        resultsSection.style.visibility = "visible";
        resultsSection.scrollIntoView({ behavior: "smooth" });
      }
    } catch (err) {
      resultsContent.innerHTML = `<div class="alert alert-danger">请求失败: ${err.message}</div>`;
      resultsSection.style.visibility = "visible";
    }

    
    
  });



  // 单元测试,模拟后端返回的 Markdown 表格
    const mockResult = {
      suggestions: `
| 序号 | 具体意见 | 内容简述 | 分类 | 改善建议 |
| --- | --- | --- | --- | --- |
| 4 | 管理层对员工不够尊重，常有不礼貌行为 | 管理层存在不礼貌/不尊重行为，损害员工感受；与序号5同类（管理方式-尊重/沟通） | 管理方式-尊重与沟通 | 发布管理者行为准则与零容忍政策；开展尊重与沟通培训；建立匿名投诉与问责机制（含处分梯度）；引入360反馈与脉搏调查跟踪改进。 |
| 5 | 部门领导经常骂人，导致员工士气低落 | 辱骂式管理，士气受损；与序号4同类（管理方式-尊重/沟通） | 管理方式-辱骂与不当言行 | HR与上级立即约谈并下达改善计划；将辱骂列为纪律红线，违规依规降级/调岗/处分；提供情绪管理与教练式领导培训；设立安全申诉与保护通道。 |
| 6 | 工作流程混乱，导致效率低下 | 流程缺失/不清，效率受阻；与2、3涉及流程问题相呼应 | 流程与制度-流程混乱/无流程 | 梳理并固化端到端SOP与RACI；指定流程Owner与变更管理；上线数字化工单/审批减少手工；设定TAT/一次通过率KPI并用VSM/Kaizen持续优化。 |
| 7 | 领导经常施加高压，员工压力过大 | 高压管理文化导致过度压力与潜在流失；与4/5同属管理风格问题 | 管理方式-高压文化 | 以目标与辅导替代高压；合理设定目标并匹配资源与加班上限；开展工作负载评估与人员补充；提供EAP/心理支持；将敬业度与团队流失等纳入管理者考核。 |
| 分析总结 | 全部7条意见中筛出尖锐问题4条（序号4、5、6、7） | 尖锐问题集中于管理方式（3条：不尊重/辱骂/高压）与流程混乱（1条）；重复主题：4与5高度重合，7同属管理风格 | 占比与高频：尖锐问题占比57.1%，常规问题占比42.9%；流程类问题共3条（2、3、6：权限/门禁、采购、SOP） | 优先路线图：先止血（制止辱骂与高压、建立问责），再固本（梳理SOP与数字化审批），后提升（管理者能力建设、文化与员工支持体系）。 |
`,
    };


    function renderMarkdownTable(result) {
      let html = marked.parse(result.suggestions);
      html = html.replace(
        /<table>/g,
        '<table class="table table-bordered table-striped table-hover table-sm m-0">'
      );
      resultsContent.innerHTML = `<div class="table-responsive">${html}</div>`;
      resultsSection.style.visibility = "visible";
      resultsSection.scrollIntoView({ behavior: "smooth" });
    }

    // 直接调用渲染函数
    // renderMarkdownTable(mockResult);
});
