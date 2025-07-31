// ==UserScript==
// @name         精确抓取评论数据
// @namespace    http://tampermonkey.net/
// @version      1.8
// @description  自动翻页抓取所有 class="review-data" 的元素内容并输出到JSON文件
// @author       You
// @match        *://*/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    const extractReviewData = () => {
        const reviewElements = document.querySelectorAll('div.a-row.a-spacing-small.review-data');
        const reviews = [];

        reviewElements.forEach((element, index) => {
            const text = element.textContent.trim();
            if (text) {
                const key = `comment ${index + 1}`;
                const obj = {};
                obj[key] = text;
                reviews.push(obj);
            }
        });

        return reviews;
    };

    const exportReviewsAsJSON = function(filename = 'reviews.json') {
        const jsonStr = JSON.stringify(window.reviews || [], null, 2);
        const blob = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const fetchAllReviews = async () => {
    let allReviews = [];

    const waitForPageLoad = () => {
        return new Promise((resolve) => {
            const observer = new MutationObserver(() => {
                const reviewsLoaded = document.querySelector('.review'); // 替换为评论加载完成的标识
                if (reviewsLoaded) {
                    observer.disconnect();
                    resolve();
                }
            });
            observer.observe(document.body, { childList: true, subtree: true });
        });
    };

    const processPage = async () => {
        try {
            const currentPageReviews = extractReviewData();
            if (currentPageReviews.length > 0) {
                allReviews = allReviews.concat(currentPageReviews);
                console.log(`当前页抓取到 ${currentPageReviews.length} 条评论，总计 ${allReviews.length} 条。`);
            }

            const nextPageButton = document.querySelector('a.a-last:not(.a-disabled)');
            if (nextPageButton) {
                console.log('点击下一页按钮...');
                nextPageButton.click();
                await waitForPageLoad(); // 等待页面加载完成
                await processPage(); // 递归调用处理下一页
            } else {
                window.reviews = allReviews;
                console.log('=== 所有页面评论抓取完成 ===');
                console.log(`共抓取 ${allReviews.length} 条评论。`);
                exportReviewsAsJSON();
            }
        } catch (error) {
            console.error(`Error processing page: ${error.message}`);
        }
    };

    await processPage();
};

    const createButton = () => {
        const button = document.createElement('button');
        button.textContent = '生成 JSON 文件';
        button.style.position = 'fixed';
        button.style.bottom = '20px';
        button.style.right = '20px';
        button.style.zIndex = '999999';
        button.style.width = '150px';
        button.style.height = '150px';
        button.style.borderRadius = '50%';
        button.style.backgroundColor = '#4CAF50';
        button.style.color = 'white';
        button.style.border = 'none';
        button.style.cursor = 'pointer';
        button.style.fontSize = '16px';
        button.style.fontWeight = 'bold';
        button.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
        button.style.transition = 'all 0.3s ease';
        button.style.display = 'flex';
        button.style.alignItems = 'center';
        button.style.justifyContent = 'center';
        button.style.textAlign = 'center';
        button.style.lineHeight = '1.5';
        button.style.padding = '10px';
        button.style.outline = 'none';

        button.onmouseover = () => {
            button.style.backgroundColor = '#45a049';
            button.style.transform = 'scale(1.1)';
            button.style.boxShadow = '0 6px 12px rgba(0, 0, 0, 0.3)';
        };

        button.onmouseout = () => {
            button.style.backgroundColor = '#4CAF50';
            button.style.transform = 'scale(1)';
            button.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
        };

        button.onclick = () => {
            window.reviews = []; // 初始化评论数组
            fetchAllReviews();
        };

        document.body.appendChild(button);
    };

    if (document.readyState === 'complete') {
        createButton();
    } else {
        window.addEventListener('load', createButton);
    }
})();