document.getElementById("generateButton").addEventListener("click", async () => {
    const fileInput = document.getElementById("jsonFile");
    const statusDiv = document.getElementById("status");

    // 检查是否选择了文件
    if (!fileInput.files.length) {
        statusDiv.textContent = "Please select a JSON file.";
        return;
    }

    const file = fileInput.files[0];

    // 读取 JSON 文件内容
    const reader = new FileReader();
    reader.onload = async (event) => {
        try {
            const jsonData = JSON.parse(event.target.result);

            // 初始化处理后的数据
            const processedData = [];

            // 遍历 JSON 数据并调用 DeepSeek API
            for (const item of jsonData) {
                for (const [comment, content] of Object.entries(item)) {
                    const suggestion = await fetchSuggestion(content);
                    processedData.push({ comments: comment, contents: content, suggestions: suggestion });
                }
            }

            // 生成 Excel 文件
            generateExcel(processedData);
            statusDiv.textContent = "Excel file generated successfully!";
        } catch (error) {
            statusDiv.textContent = `Error: ${error.message}`;
        }
    };

    reader.readAsText(file);
});

// 调用 DeepSeek API
async function fetchSuggestion(content) {
    const apiKey = "sk-7e8ab23cf1124fbb80502138fb3a888a"; // 替换为您的 DeepSeek API 密钥
    const apiUrl = "https://api.deepseek.com/chat/completions";

    const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${apiKey}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            model: "deepseek-chat",
            messages: [
                { role: "system", content: "You are a helpful assistant, use Simply Chinese to generate content, should less than 30 charactors,do not show the total charactors" },
                { role: "user", content: `基于以下内容给出中文版的针对终端用户反馈的产品改善建议，比如:改进方向，优化策略等。内容需在50字以内：${content}` }
            ],
            stream: false
        }),
    });

    const data = await response.json();
    return data.choices[0].message.content;
}

// 生成 Excel 文件
function generateExcel(data) {
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.json_to_sheet(data);
    XLSX.utils.book_append_sheet(workbook, worksheet, "Sheet1");

    const excelFile = XLSX.write(workbook, { bookType: "xlsx", type: "binary" });
    const blob = new Blob([s2ab(excelFile)], { type: "application/octet-stream" });

    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "comments_with_descriptions.xlsx";
    link.click();
}

// 将字符串转换为 ArrayBuffer
function s2ab(s) {
    const buf = new ArrayBuffer(s.length);
    const view = new Uint8Array(buf);
    for (let i = 0; i < s.length; i++) view[i] = s.charCodeAt(i) & 0xFF;
    return buf;
}