/**
 * 工具函数模块
 * 包含通用的辅助函数
 */

/**
 * HTML 转义，防止 XSS
 * @param {string} text 
 * @returns {string}
 */
export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * URL 解析和链接化
 * @param {string} text 
 * @returns {string}
 */
export function parseUrls(text) {
    const urlRegex = /(https?:\/\/[^\s<>"']+)/gi;
    
    return text.replace(urlRegex, (url) => {
        try {
            new URL(url);
            return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
        } catch {
            return url;
        }
    });
}

/**
 * 相对时间格式化
 * @param {string} isoString ISO 时间字符串
 * @returns {string}
 */
export function formatRelativeTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`;

    return formatAbsoluteTime(isoString);
}

/**
 * 绝对时间格式化
 * @param {string} isoString ISO 时间字符串
 * @returns {string}
 */
export function formatAbsoluteTime(isoString) {
    const date = new Date(isoString);
    const pad = n => String(n).padStart(2, '0');
    
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

/**
 * 邮箱验证
 * @param {string} email 
 * @returns {boolean}
 */
export function validateEmail(email) {
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(email);
}

/**
 * URL 验证
 * @param {string} url 
 * @returns {boolean}
 */
export function validateURL(url) {
    return url.startsWith('http://') || url.startsWith('https://');
}

/**
 * 复制到剪贴板
 * @param {string} text 要复制的文本
 * @param {string} label 用于提示的标签
 * @param {Function} onSuccess 成功回调
 * @param {Function} onError 失败回调
 */
export async function copyToClipboard(text, label, onSuccess, onError) {
    try {
        if (navigator.clipboard) {
            await navigator.clipboard.writeText(text);
        } else {
            // 降级方案
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.cssText = 'position:fixed;opacity:0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
        }
        
        if (onSuccess) {
            onSuccess(text, label);
        }
    } catch (err) {
        console.error('复制失败:', err);
        if (onError) {
            onError(text, label, err);
        }
    }
}

/**
 * 防抖函数
 * @param {Function} fn 
 * @param {number} delay 
 * @returns {Function}
 */
export function debounce(fn, delay) {
    let timer = null;
    return function(...args) {
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

/**
 * 节流函数
 * @param {Function} fn 
 * @param {number} limit 
 * @returns {Function}
 */
export function throttle(fn, limit) {
    let inThrottle = false;
    return function(...args) {
        if (!inThrottle) {
            fn.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}
