// ==UserScript==
// @name         亚马逊评论手动累积导出 Excel（自动化抓取+去重+评分+多语言标题）
// @namespace    http://tampermonkey.net/
// @version      3.0
// @description  手动保存每页评论，最后一次性导出为 Excel，支持断点续抓 + 去重 + 自动时间戳文件名 + 评论日期格式化 + 评分 + 多语言标题抓取 + 自动化抓取
// @author       Keyee
// @match        *://*/*
// @grant        none
// @require      https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js
// ==/UserScript==

/*
# 亚马逊评论抓取工具使用说明（SOP）

## 1. 工具简介
本工具是一个 **Tampermonkey（油猴）脚本**，用于在亚马逊商品评论页面：
- **批量抓取评论**（支持标题、内容、日期、评分、尺寸）
- **自动去重**
- **一键抓取所有评论并导出为Excel**
- **支持自动翻页抓取**

---

## 2. 使用方法

### 2.1 打开评论页面
1. 进入亚马逊商品页面
2. 点击 **查看所有评论**（All reviews）
3. 确保页面 URL 类似： https://www.amazon.com/product-reviews/商品ID/...


---

### 2.2 工具按钮说明
脚本加载后，页面右下角会出现一个工具面板，包含以下按钮：

| 按钮名称 | 功能说明 |
|----------|----------|
| **保存当页评论** | 抓取当前页的评论并保存到本地（去重） |
| **上一页** | 模拟点击亚马逊的“Previous page”按钮 |
| **下一页** | 模拟点击亚马逊的“Next page”按钮 |
| **一键抓取** | 从当前页开始，自动保存评论并翻页，直到最后一页，自动导出 Excel |
| **生成 Excel 文件** | 将已保存的评论导出为 Excel 文件 |
| **清空已保存数据** | 删除本地保存的所有评论数据 |

---

### 2.3 手动抓取流程
1. 打开评论第一页
2. 点击 **保存当页评论**
3. 点击 **下一页**
4. 重复步骤 2-3，直到最后一页
5. 点击 **生成 Excel 文件** 下载评论数据

---

### 2.4 一键抓取流程（推荐）
1. 打开评论第一页
2. 点击 **一键抓取**
3. 工具会自动：
- 保存当前页评论
- 翻到下一页
- 重复直到最后一页
4. 到最后一页时：
- 弹窗提示抓取完成和总评论数
- 自动下载 Excel 文件

---

## 3. 数据格式说明

导出的 Excel 文件包含以下列：

| 列名 | 说明 |
|------|------|
| 序号 | 自然编号 |
| 评论标题 | 评论的标题（支持多语言，优先原文） |
| 评论内容 | 评论的正文内容 |
| 评论日期 | 格式化为 `YYYY.M.D` |
| 评分 | 数字评分（如 `4.5`） |
| 尺寸 | 评论中提到的产品尺寸（如 `40-Inch`） |

---

## 4. 注意事项
- **必须在评论列表页面使用**，否则按钮不会出现
- **一键抓取** 会模拟翻页，建议网络稳定时使用
- 如果中途停止抓取，可以再次点击 **一键抓取** 按钮
- 数据保存在浏览器 `localStorage` 中，清空浏览器缓存会丢失数据
- 导出的 Excel 文件名包含时间戳，方便区分不同批次

---

## 5. 常见问题

### Q1: 按钮不显示？
- 确认 Tampermonkey 已启用
- 确认脚本已保存并启用
- 刷新评论页面

### Q2: 一键抓取中途停止？
- 可能是网络延迟导致翻页失败
- 可以手动点击 **下一页** 继续抓取

### Q3: 日期显示不正确？
- 脚本会自动提取 `on August 30, 2025` 这种格式并转换为 `2025.8.30`
- 如果亚马逊页面语言不同，可能需要调整正则匹配规则

---

## 6. 更新记录
- **v3.0**
- 支持多语言标题抓取（优先原文）
- 新增尺寸列
- 新增上一页、下一页按钮
- 新增一键抓取功能（自动导出 Excel）
- 评论日期格式化为 `YYYY.M.D`

*/

(function () {
    'use strict';

    const STORAGE_KEY = 'amazon_reviews_data';

    const loadSavedReviews = () => {
        try {
            const data = localStorage.getItem(STORAGE_KEY);
            return data ? JSON.parse(data) : [];
        } catch (e) {
            console.error('读取本地评论数据失败:', e);
            return [];
        }
    };

    const saveReviewsToStorage = (reviews) => {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(reviews));
        } catch (e) {
            console.error('保存评论数据失败:', e);
        }
    };

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        if (isNaN(date)) return dateStr;
        return `${date.getFullYear()}.${date.getMonth() + 1}.${date.getDate()}`;
    };

    const extractReviewData = () => {
        const titleElements = document.querySelectorAll('a[data-hook="review-title"]');
        const reviewElements = document.querySelectorAll('div.a-row.a-spacing-small.review-data');
        const dateElements = document.querySelectorAll('span[data-hook="review-date"]');
        const starElements = document.querySelectorAll('i[data-hook="review-star-rating"]');
        const sizeElements = document.querySelectorAll('div.review-format-strip a[data-hook="format-strip"]');

        const reviews = [];

        reviewElements.forEach((element, index) => {
            const text = element.textContent.trim();

            // 标题抓取：优先取原文，否则取最后一个 span
            let titleText = '';
            if (titleElements[index]) {
                const original = titleElements[index].querySelector('.cr-original-review-content');
                if (original) {
                    titleText = original.textContent.trim();
                } else {
                    const spans = titleElements[index].querySelectorAll('span');
                    if (spans.length > 0) {
                        titleText = spans[spans.length - 1].textContent.trim();
                    } else {
                        titleText = titleElements[index].textContent.trim();
                    }
                }
            }

            // 评论日期
            let dateText = '';
            if (dateElements[index]) {
                const rawDate = dateElements[index].textContent.trim();
                const match = rawDate.match(/on\s+(.+)$/i);
                const pureDate = match ? match[1] : rawDate;
                dateText = formatDate(pureDate);
            }

            // 评分
            let starText = '';
            if (starElements[index]) {
                const altText = starElements[index].querySelector('span.a-icon-alt')?.textContent.trim() || '';
                const match = altText.match(/^\d+(\.\d+)?/);
                starText = match ? match[0] : '';
            }

            // 尺寸
            let sizeText = '';
            if (sizeElements[index]) {
                const sizeMatch = sizeElements[index].textContent.match(/Size:\s*([^\|]+)/i);
                sizeText = sizeMatch ? sizeMatch[1].trim() : '';
            }

            if (text) {
                reviews.push({
                    评论标题: titleText,
                    评论内容: text,
                    评论日期: dateText,
                    评分: starText,
                    尺寸: sizeText
                });
            }
        });

        return reviews;
    };

    const mergeReviews = (oldReviews, newReviews) => {
        const seen = new Set(oldReviews.map(r => `${r.评论标题}||${r.评论内容}||${r.评论日期}||${r.评分}||${r.尺寸}`));
        const merged = [...oldReviews];

        newReviews.forEach(r => {
            const key = `${r.评论标题}||${r.评论内容}||${r.评论日期}||${r.评分}||${r.尺寸}`;
            if (!seen.has(key)) {
                merged.push(r);
                seen.add(key);
            }
        });

        return merged;
    };

    // 翻页函数
    const goToPreviousPage = () => {
        const prevLink = Array.from(document.querySelectorAll('.a-pagination a'))
        .find(a => a.textContent.trim().includes('Previous page'));
        if (prevLink) {
            prevLink.click();
        } else {
            alert('没有上一页按钮，可能已经在第一页。');
        }
    };

    const goToNextPage = () => {
        const nextLink = Array.from(document.querySelectorAll('.a-pagination a'))
        .find(a => a.textContent.trim().includes('Next page'));
        if (nextLink) {
            nextLink.click();
        } else {
            alert('没有下一页按钮，可能已经在最后一页。');
        }
    };

    // 自动抓取
    let autoCrawlRunning = false;

    const autoCrawl = (btn) => {
        if (!autoCrawlRunning) {
            autoCrawlRunning = true;
            btn.textContent = '停止抓取';
            crawlNextPage(btn);
        } else {
            autoCrawlRunning = false;
            btn.textContent = '一键抓取';
            alert('已停止自动抓取。');
        }
    };

    const crawlNextPage = (btn) => {
        if (!autoCrawlRunning) return;

        // 保存当前页评论
        const currentPageReviews = extractReviewData();
        if (currentPageReviews.length > 0) {
            let allReviews = loadSavedReviews();
            const beforeCount = allReviews.length;
            allReviews = mergeReviews(allReviews, currentPageReviews);
            const addedCount = allReviews.length - beforeCount;
            saveReviewsToStorage(allReviews);
            console.log(`本页新增 ${addedCount} 条评论，总计 ${allReviews.length} 条。`);
        } else {
            console.warn('当前页没有抓取到评论！');
        }

        // 找下一页按钮
        const nextLink = Array.from(document.querySelectorAll('.a-pagination a'))
        .find(a => a.textContent.trim().includes('Next page'));

        if (nextLink) {
            nextLink.click();
            // 等待页面加载后继续
            setTimeout(() => {
                crawlNextPage(btn);
            }, 3000); // 等 3 秒
        } else {
            autoCrawlRunning = false;
            btn.textContent = '一键抓取';
            const total = loadSavedReviews().length;
            alert(`已到最后一页，抓取完成！共抓取 ${total} 条评论。`);
            // 自动导出 Excel
            exportReviewsAsExcel();
        }
    };

    const getTimestamp = () => {
        const now = new Date();
        const pad = (n) => n.toString().padStart(2, '0');
        const date = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
        const time = `${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;
        return `${date}_${time}`;
    };

    const exportReviewsAsExcel = () => {
        const allReviews = loadSavedReviews();
        if (allReviews.length === 0) {
            alert('没有可导出的评论，请先保存评论数据！');
            return;
        }
        // 给每条评论加序号
        const reviewsWithIndex = allReviews.map((r, i) => ({
            序号: i + 1,
            ...r
        }));
        const ws = XLSX.utils.json_to_sheet(reviewsWithIndex);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, '评论数据');
        const filename = `reviews_${getTimestamp()}.xlsx`;
        XLSX.writeFile(wb, filename);
    };

    const createButtons = () => {
        const container = document.createElement('div');
        container.style.position = 'fixed';
        container.style.bottom = '20px';
        container.style.right = '20px';
        container.style.zIndex = '999999';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.gap = '10px';

        // 上一页按钮
        const prevBtn = document.createElement('button');
        prevBtn.textContent = '上一页';
        prevBtn.style.padding = '10px';
        prevBtn.style.backgroundColor = '#9E9E9E';
        prevBtn.style.color = 'white';
        prevBtn.style.border = 'none';
        prevBtn.style.cursor = 'pointer';
        prevBtn.style.fontSize = '14px';
        prevBtn.onclick = goToPreviousPage;

        // 下一页按钮
        const nextBtn = document.createElement('button');
        nextBtn.textContent = '下一页';
        nextBtn.style.padding = '10px';
        nextBtn.style.backgroundColor = '#9E9E9E';
        nextBtn.style.color = 'white';
        nextBtn.style.border = 'none';
        nextBtn.style.cursor = 'pointer';
        nextBtn.style.fontSize = '14px';
        nextBtn.onclick = goToNextPage;

        // 把按钮插入容器
        container.appendChild(prevBtn);
        container.appendChild(nextBtn);

        // 一键抓取按钮
        const autoCrawlBtn = document.createElement('button');
        autoCrawlBtn.textContent = '一键抓取';
        autoCrawlBtn.style.padding = '10px';
        autoCrawlBtn.style.backgroundColor = '#FF9800';
        autoCrawlBtn.style.color = 'white';
        autoCrawlBtn.style.border = 'none';
        autoCrawlBtn.style.cursor = 'pointer';
        autoCrawlBtn.style.fontSize = '14px';
        autoCrawlBtn.onclick = autoCrawl;

        container.appendChild(autoCrawlBtn);

        autoCrawlBtn.onclick = function() {
            autoCrawl(this);
        };

        const saveBtn = document.createElement('button');
        saveBtn.textContent = '保存当页评论';
        saveBtn.style.padding = '10px';
        saveBtn.style.backgroundColor = '#2196F3';
        saveBtn.style.color = 'white';
        saveBtn.style.border = 'none';
        saveBtn.style.cursor = 'pointer';
        saveBtn.style.fontSize = '14px';
        saveBtn.onclick = () => {
            const currentPageReviews = extractReviewData();
            if (currentPageReviews.length === 0) {
                alert('当前页没有抓取到评论！');
                return;
            }
            let allReviews = loadSavedReviews();
            const beforeCount = allReviews.length;
            allReviews = mergeReviews(allReviews, currentPageReviews);
            const addedCount = allReviews.length - beforeCount;
            saveReviewsToStorage(allReviews);
            alert(`本页新增 ${addedCount} 条评论，总计 ${allReviews.length} 条。`);
        };

        const exportBtn = document.createElement('button');
        exportBtn.textContent = '生成 Excel 文件';
        exportBtn.style.padding = '10px';
        exportBtn.style.backgroundColor = '#4CAF50';
        exportBtn.style.color = 'white';
        exportBtn.style.border = 'none';
        exportBtn.style.cursor = 'pointer';
        exportBtn.style.fontSize = '14px';
        exportBtn.onclick = () => {
            exportReviewsAsExcel();
        };

        const clearBtn = document.createElement('button');
        clearBtn.textContent = '清空已保存数据';
        clearBtn.style.padding = '10px';
        clearBtn.style.backgroundColor = '#f44336';
        clearBtn.style.color = 'white';
        clearBtn.style.border = 'none';
        clearBtn.style.cursor = 'pointer';
        clearBtn.style.fontSize = '14px';
        clearBtn.onclick = () => {
            if (confirm('确定要清空所有已保存的评论数据吗？')) {
                localStorage.removeItem(STORAGE_KEY);
                alert('已清空评论数据。');
            }
        };

        container.appendChild(saveBtn);
        container.appendChild(exportBtn);
        container.appendChild(clearBtn);
        document.body.appendChild(container);
    };

    if (document.readyState === 'complete') {
        createButtons();
    } else {
        window.addEventListener('load', createButtons);
    }
})();