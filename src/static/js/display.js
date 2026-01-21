// 打卡展示页面逻辑

const checkinsList = document.getElementById('checkinsList');
const pagination = document.getElementById('pagination');
const totalCountSpan = document.getElementById('totalCount');
const currentPageSpan = document.getElementById('currentPage');
const imageModal = document.getElementById('imageModal');
const modalImage = document.getElementById('modalImage');

// 搜索面板元素
const searchToggle = document.getElementById('searchToggle');
const searchContentPanel = document.getElementById('searchContent');
const searchNickname = document.getElementById('searchNickname');
const searchEmail = document.getElementById('searchEmail');
const searchContentKeyword = document.getElementById('searchContentKeyword');
const excludeDefaultNickname = document.getElementById('excludeDefaultNickname');
const excludeShortContent = document.getElementById('excludeShortContent');
const minContentLength = document.getElementById('minContentLength');
const resetSearchBtn = document.getElementById('resetSearch');
const applySearchBtn = document.getElementById('applySearch');

// 排序按钮
const sortDescBtn = document.getElementById('sortDesc');
const sortAscBtn = document.getElementById('sortAsc');
const sortLoveBtn = document.getElementById('sortLove');

let currentPage = 1;
let totalPages = 1;
let currentFilters = {};
let currentSort = 'desc'; // 默认倒序（最新优先）
let currentSortBy = 'id'; // 默认按ID排序

// 搜索面板切换
searchToggle.addEventListener('click', () => {
    searchContentPanel.classList.toggle('show');
    const icon = searchToggle.querySelector('.toggle-icon');
    icon.textContent = searchContentPanel.classList.contains('show') ? '▲' : '▼';
});

// 重置搜索
resetSearchBtn.addEventListener('click', () => {
    searchNickname.value = '';
    searchEmail.value = '';
    searchContentKeyword.value = '';
    excludeDefaultNickname.checked = false;
    excludeShortContent.checked = false;
    minContentLength.value = '10';
    currentFilters = {};
    loadCheckins(1);
});

// 应用搜索
applySearchBtn.addEventListener('click', () => {
    currentFilters = {};
    
    if (searchNickname.value.trim()) {
        currentFilters.nickname = searchNickname.value.trim();
    }
    if (searchEmail.value.trim()) {
        currentFilters.email = searchEmail.value.trim();
    }
    if (searchContentKeyword.value.trim()) {
        currentFilters.content = searchContentKeyword.value.trim();
    }
    if (excludeDefaultNickname.checked) {
        currentFilters.exclude_default_nickname = true;
    }
    if (excludeShortContent.checked) {
        const minLen = parseInt(minContentLength.value) || 10;
        currentFilters.min_content_length = minLen;
    }
    
    loadCheckins(1);
});

// 排序按钮事件
sortDescBtn.addEventListener('click', () => {
    if (currentSort !== 'desc' || currentSortBy !== 'id') {
        currentSort = 'desc';
        currentSortBy = 'id';
        updateSortButtons();
        loadCheckins(1);
    }
});

sortAscBtn.addEventListener('click', () => {
    if (currentSort !== 'asc' || currentSortBy !== 'id') {
        currentSort = 'asc';
        currentSortBy = 'id';
        updateSortButtons();
        loadCheckins(1);
    }
});

sortLoveBtn.addEventListener('click', () => {
    if (currentSortBy !== 'love') {
        currentSort = 'desc'; // 点赞数默认倒序（最多优先）
        currentSortBy = 'love';
        updateSortButtons();
        loadCheckins(1);
    }
});

// 更新排序按钮状态
function updateSortButtons() {
    sortDescBtn.classList.remove('active');
    sortAscBtn.classList.remove('active');
    sortLoveBtn.classList.remove('active');
    
    if (currentSortBy === 'love') {
        sortLoveBtn.classList.add('active');
    } else if (currentSort === 'desc') {
        sortDescBtn.classList.add('active');
    } else {
        sortAscBtn.classList.add('active');
    }
}

// 加载打卡记录
async function loadCheckins(page = 1) {
    try {
        // 构建查询参数
        const params = new URLSearchParams({
            page: page,
            limit: 20,
            sort: currentSort,
            sort_by: currentSortBy,
            ...currentFilters
        });
        
        const response = await fetch(`/api/checkins?${params}`);
        const result = await response.json();

        if (result.success) {
            currentPage = result.page;
            totalPages = result.pages;
            
            // 更新统计
            totalCountSpan.textContent = result.total;
            currentPageSpan.textContent = currentPage;

            // 渲染打卡列表
            renderCheckins(result.data);

            // 渲染分页
            renderPagination();
        }
    } catch (error) {
        console.error('加载失败:', error);
        checkinsList.innerHTML = '<div class="loading">❌ 加载失败，请刷新重试</div>';
    }
}

// 渲染打卡列表
function renderCheckins(checkins) {
    if (checkins.length === 0) {
        checkinsList.innerHTML = '<div class="loading">暂无打卡记录</div>';
        return;
    }

    checkinsList.innerHTML = checkins.map(checkin => {
        const content = parseUrls(escapeHtml(checkin.content));
        const mediaFiles = checkin.media_files || [];
        const time = formatTime(checkin.created_at);

        // 用户信息
        const avatar = checkin.avatar || '🥰';
        const nickname = checkin.nickname || '用户0721';
        const email = checkin.email;
        const qq = checkin.qq;
        const url = checkin.url;
        const love = checkin.love || 0;
        const liked = checkin.liked || false;

        // 联系方式HTML
        const contactsHtml = (email || qq || url) ? `
            <div class="card-contacts">
                ${email ? `<span class="contact-item contact-email" title="点击复制邮箱" onclick="copyToClipboard('${escapeHtml(email)}', '邮箱')"><span class="contact-icon">📧</span><span class="contact-text">${escapeHtml(email)}</span></span>` : ''}
                ${qq ? `<span class="contact-item contact-qq" title="点击复制QQ号" onclick="copyToClipboard('${escapeHtml(qq)}', 'QQ号')"><span class="contact-icon">🐧</span><span class="contact-text">${escapeHtml(qq)}</span></span>` : ''}
                ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="contact-item contact-url" title="点击访问链接"><span class="contact-icon">🔗</span><span class="contact-text">${escapeHtml(url).length > 30 ? escapeHtml(url).substring(0, 30) + '...' : escapeHtml(url)}</span></a>` : ''}
            </div>
        ` : '';

        const mediaHtml = mediaFiles.length > 0 ? `
            <div class="card-media">
                ${mediaFiles.map(url => {
                    const isVideo = url.match(/\.(mp4|webm|mov|avi)$/i);
                    if (isVideo) {
                        return `
                            <div class="media-item">
                                <video src="${url}" controls></video>
                            </div>
                        `;
                    } else {
                        return `
                            <div class="media-item" onclick="openImageModal('${url}')">
                                <img src="${url}" alt="打卡图片">
                            </div>
                        `;
                    }
                }).join('')}
            </div>
        ` : '';

        // 点赞按钮HTML
        const likeClass = liked ? 'like-btn liked' : 'like-btn';
        const likeHtml = `
            <button class="${likeClass}" data-id="${checkin.id}" onclick="handleLike(${checkin.id}, this)">
                <span class="like-icon">${liked ? '❤️' : '🤍'}</span>
                <span class="like-count">${love}</span>
            </button>
        `;

        // 新布局：上下分区，上半区2:8布局
        return `
            <div class="checkin-card">
                <div class="card-upper">
                    <div class="card-avatar">${avatar}</div>
                    <div class="card-main">
                        <div class="card-header">
                            <span class="card-nickname">${escapeHtml(nickname)}</span>
                            <span class="card-meta">
                                <span class="card-id">#${checkin.id}</span>
                                <span class="card-time" title="${formatAbsoluteTime(checkin.created_at)}">${time}</span>
                            </span>
                        </div>
                        <div class="card-content">${content}</div>
                        ${contactsHtml}
                    </div>
                </div>
                ${mediaHtml}
                <div class="card-footer">
                    ${likeHtml}
                </div>
            </div>
        `;
    }).join('');
}

// 渲染分页
function renderPagination() {
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let paginationHtml = '';

    // 上一页
    paginationHtml += `
        <button ${currentPage === 1 ? 'disabled' : ''} onclick="loadCheckins(${currentPage - 1})">
            ← 上一页
        </button>
    `;

    // 页码
    const maxButtons = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);

    if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }

    if (startPage > 1) {
        paginationHtml += `<button onclick="loadCheckins(1)">1</button>`;
        if (startPage > 2) {
            paginationHtml += `<button disabled>...</button>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <button 
                class="${i === currentPage ? 'active' : ''}" 
                onclick="loadCheckins(${i})"
            >
                ${i}
            </button>
        `;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHtml += `<button disabled>...</button>`;
        }
        paginationHtml += `<button onclick="loadCheckins(${totalPages})">${totalPages}</button>`;
    }

    // 下一页
    paginationHtml += `
        <button ${currentPage === totalPages ? 'disabled' : ''} onclick="loadCheckins(${currentPage + 1})">
            下一页 →
        </button>
    `;

    pagination.innerHTML = paginationHtml;
}

// URL 解析和渲染
function parseUrls(text) {
    // URL 正则表达式
    const urlRegex = /(https?:\/\/[^\s<>"']+)/gi;
    
    return text.replace(urlRegex, (url) => {
        // 简单验证 URL
        try {
            new URL(url);
            return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
        } catch {
            return url;
        }
    });
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 时间格式化
function formatTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;

    // 小于1分钟
    if (diff < 60000) {
        return '刚刚';
    }

    // 小于1小时
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}分钟前`;
    }

    // 小于24小时
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}小时前`;
    }

    // 小于7天
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days}天前`;
    }

    // 格式化日期
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');

    return `${year}-${month}-${day} ${hour}:${minute}`;
}

// 绝对时间格式化
function formatAbsoluteTime(isoString) {
    const date = new Date(isoString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    const second = String(date.getSeconds()).padStart(2, '0');

    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

// 打开图片模态框
function openImageModal(url) {
    modalImage.src = url;
    imageModal.classList.add('show');
}

// 关闭模态框
imageModal.addEventListener('click', (e) => {
    if (e.target === imageModal || e.target.classList.contains('modal-close')) {
        imageModal.classList.remove('show');
    }
});

// 复制到剪贴板
function copyToClipboard(text, label) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            alert(`✅ ${label}已复制: ${text}`);
        }).catch(err => {
            console.error('复制失败:', err);
            // 降级方案
            fallbackCopy(text, label);
        });
    } else {
        // 降级方案
        fallbackCopy(text, label);
    }
}

// 降级复制方案
function fallbackCopy(text, label) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        alert(`✅ ${label}已复制: ${text}`);
    } catch (err) {
        alert(`❌ 复制失败，请手动复制: ${text}`);
    }
    document.body.removeChild(textarea);
}

// 页面加载时获取数据
loadCheckins(1);

// 点赞处理函数
async function handleLike(checkinId, button) {
    // 防止重复点击
    if (button.disabled) return;
    button.disabled = true;
    
    // 检查本地是否已点赞（辅助检查，后端才是真正防线）
    const likedIds = JSON.parse(localStorage.getItem('likedCheckins') || '[]');
    if (likedIds.includes(checkinId)) {
        showToast('你已经点过赞了 💕');
        button.disabled = false;
        return;
    }
    
    try {
        const response = await fetch(`/api/like/${checkinId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 更新按钮状态
            button.classList.add('liked');
            button.querySelector('.like-icon').textContent = '❤️';
            button.querySelector('.like-count').textContent = result.love;
            
            // 保存到 localStorage
            likedIds.push(checkinId);
            localStorage.setItem('likedCheckins', JSON.stringify(likedIds));
            
            // 添加动画效果
            button.classList.add('like-animate');
            setTimeout(() => button.classList.remove('like-animate'), 300);
            
            showToast('点赞成功 ❤️');
        } else {
            showToast(result.message || '点赞失败');
        }
    } catch (error) {
        console.error('点赞失败:', error);
        showToast('点赞失败，请重试');
    } finally {
        button.disabled = false;
    }
}

// 显示提示信息
function showToast(message) {
    // 移除已有的 toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // 显示动画
    setTimeout(() => toast.classList.add('show'), 10);
    
    // 3秒后隐藏
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}
