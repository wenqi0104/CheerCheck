document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const generateButton = document.getElementById('generateButton');
    const resultsSection = document.getElementById('resultsSection');
    const resultsContent = document.getElementById('resultsContent');
    const urlInput = document.getElementById('urlInput');
    const fileInput = document.getElementById('fileInput');
    const promptInput = document.getElementById('promptInput');
    const promptCheckbox = document.getElementById('promptCheckbox');
    const urlGroup = document.getElementById('urlGroup');
    const fileGroup = document.getElementById('fileGroup');
    const urlRadio = document.getElementById('urlRadio');
    const fileRadio = document.getElementById('fileRadio');
    const statusDiv = document.createElement('div');
    statusDiv.id = 'status';
    statusDiv.className = 'mt-3 alert alert-info';
    document.querySelector('#cheerCheckForm').appendChild(statusDiv);

    // 数据源选择变化事件
    [urlRadio, fileRadio].forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.id === 'urlRadio') {
                urlGroup.style.display = 'block';
                fileGroup.style.display = 'none';
                fileInput.value = '';
            } else {
                urlGroup.style.display = 'none';
                fileGroup.style.display = 'block';
                urlInput.value = '';
            }
        });
    });

    // 提示词复选框变化事件
    promptCheckbox.addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('promptGroup').style.display = 'block';
        } else {
            document.getElementById('promptGroup').style.display = 'none';
            promptInput.value = '';
        }
    });

    // 生成按钮点击事件
    generateButton.addEventListener('click', async function() {
        // 验证输入
        if (!validateInputs()) {
            return;
        }
        
        // 显示加载状态
        showLoadingState();
        
        try {
            let dataSource;
            let data;
            
            // 确定数据源
            if (urlRadio.checked) {
                dataSource = 'url';
                // 这里可以添加从URL获取数据的逻辑
                data = { source: 'url', value: urlInput.value };
            } else {
                dataSource = 'file';
                const file = fileInput.files[0];
                data = await processFile(file);
            }
            
            // 获取提示词（如果提供）
            const prompt = promptCheckbox.checked ? promptInput.value : '';
            
            // 这里应该是调用API处理数据的逻辑
            // 为了示例，我们模拟处理过程
            await simulateProcessing(data, prompt);
            
            // 显示完成动画
            showCompletionAnimation();
            
        } catch (error) {
            showStatus(`处理过程中出错: ${error.message}`, 'alert-danger');
        }
    });

    // 输入验证
    function validateInputs() {
        let isValid = true;
        
        // 重置错误状态
        urlInput.classList.remove('is-invalid');
        fileInput.classList.remove('is-invalid');
        
        // 验证数据源
        if (urlRadio.checked && !urlInput.value.trim()) {
            urlInput.classList.add('is-invalid');
            isValid = false;
        } else if (fileRadio.checked && (!fileInput.files || fileInput.files.length === 0)) {
            fileInput.classList.add('is-invalid');
            isValid = false;
        }
        
        return isValid;
    }
    
    // 处理文件
    async function processFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (event) => {
                try {
                    let parsedData;
                    
                    if (file.name.endsWith('.json')) {
                        parsedData = JSON.parse(event.target.result);
                    } else if (file.name.endsWith('.csv')) {
                        parsedData = parseCSV(event.target.result);
                    } else {
                        parsedData = parseExcel(event.target.result);
                    }
                    
                    resolve({ 
                        source: 'file', 
                        value: parsedData,
                        fileName: file.name
                    });
                } catch (error) {
                    reject(error);
                }
            };
            
            if (file.name.endsWith('.json') || file.name.endsWith('.csv')) {
                reader.readAsText(file);
            } else {
                reader.readAsArrayBuffer(file);
            }
        });
    }
    
    // 解析CSV文件
    function parseCSV(csvText) {
        const lines = csvText.split('\n');
        const headers = lines[0].split(',');
        const result = [];
        
        for (let i = 1; i < lines.length; i++) {
            const obj = {};
            const currentLine = lines[i].split(',');
            
            for (let j = 0; j < headers.length; j++) {
                obj[headers[j]] = currentLine[j];
            }
            
            result.push(obj);
        }
        
        return result;
    }
    
    // 解析Excel文件
    function parseExcel(arrayBuffer) {
        const workbook = XLSX.read(arrayBuffer, { type: 'array' });
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];
        return XLSX.utils.sheet_to_json(worksheet);
    }
    
    // 模拟处理过程
    async function simulateProcessing(data, prompt) {
        return new Promise(resolve => {
            setTimeout(() => {
                // 这里应该是调用API处理数据的逻辑
                // 现在只是模拟处理时间
                resolve();
            }, 2000);
        });
    }
    
    // 显示状态信息
    function showStatus(message, type) {
        statusDiv.textContent = message;
        statusDiv.className = `mt-3 alert ${type}`;
    }
    
    // 显示加载状态
    function showLoadingState() {
        resultsSection.style.display = 'block';
        resultsContent.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-3 mb-0">正在分析评论数据并生成改进建议...</p>
            </div>
        `;
    }
    
    // 显示完成动画
    function showCompletionAnimation() {
        resultsContent.innerHTML = `
            <div class="animate-fadein text-center py-5">
                <div class="display-4 text-success mb-4">
                    <i class="bi bi-check-circle-fill"></i>
                </div>
                <h3 class="mb-3">处理完成！</h3>
                <p class="lead">您的改进建议已准备就绪。</p>
                <button id="newAnalysisBtn" class="btn btn-outline-primary btn-lg mt-4">
                    <i class="bi bi-arrow-counterclockwise me-2"></i>新建分析
                </button>
            </div>
        `;
        
        document.getElementById('newAnalysisBtn').addEventListener('click', function() {
            resultsSection.style.display = 'none';
            urlInput.value = '';
            fileInput.value = '';
            promptInput.value = '';
            promptCheckbox.checked = false;
            document.getElementById('promptGroup').style.display = 'none';
            urlRadio.checked = true;
            urlGroup.style.display = 'block';
            fileGroup.style.display = 'none';
            statusDiv.textContent = '';
        });
    }
});