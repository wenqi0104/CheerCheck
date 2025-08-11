// static/script.js
document.addEventListener('DOMContentLoaded', function () {
    const urlRadio = document.getElementById('urlRadio');
    const fileRadio = document.getElementById('fileRadio');
    const urlGroup = document.getElementById('urlGroup');
    const fileGroup = document.getElementById('fileGroup');
    const promptCheckbox = document.getElementById('promptCheckbox');
    const promptGroup = document.getElementById('promptGroup');
    const resultsSection = document.getElementById('resultsSection');
    const resultsContent = document.getElementById('resultsContent');
    const organizeButton = document.getElementById('organizeDataButton');
    const generateButton = document.getElementById('generateButton');

    // 切换数据源
    urlRadio.addEventListener('change', () => {
        urlGroup.style.display = 'block';
        fileGroup.style.display = 'none';
    });
    fileRadio.addEventListener('change', () => {
        urlGroup.style.display = 'none';
        fileGroup.style.display = 'block';
    });

    // 切换提示词
    promptCheckbox.addEventListener('change', () => {
        promptGroup.style.display = promptCheckbox.checked ? 'block' : 'none';
    });

    // 一键整理数据（可选功能，比如预览/清洗）
    organizeButton.addEventListener('click', () => {
        alert('数据正在整理...');
        // 可添加预处理逻辑
    });

    // 生成改进建议
    generateButton.addEventListener('click', async () => {
        const formData = new FormData();
        const dataSource = document.querySelector('input[name="dataSource"]:checked').value;
        const prompt = document.getElementById('promptInput').value;

        formData.append('dataSource', dataSource);
        if (dataSource === 'url') {
            const url = document.getElementById('urlInput').value.trim();
            if (!url) {
                alert('请输入有效的 URL');
                return;
            }
            formData.append('url', 'https://' + url.replace(/^https?:\/\//, ''));
        } else if (dataSource === 'file') {
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files.length) {
                alert('请上传文件');
                return;
            }
            formData.append('file', fileInput.files[0]);
        }

        if (promptCheckbox.checked && prompt) {
            formData.append('prompt', prompt);
        }

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.error) {
                resultsContent.innerHTML = `<div class="alert alert-danger">${result.error}</div>`;
            } else {
                // 这里直接把formData传入接口，有result后前端模板渲染返回结果。 
                // 后端要同步生成并下载文件 ！！！！！！
                resultsContent.innerHTML = result.suggestions;
                resultsSection.style.visibility = 'visible';
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            }
        } catch (err) {
            resultsContent.innerHTML = `<div class="alert alert-danger">请求失败: ${err.message}</div>`;
            resultsSection.style.visibility = 'visible';
        }
    });
});