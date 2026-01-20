// 打卡展示页面逻辑

const checkinsList = document.getElementById('checkinsList');
const pagination = document.getElementById('pagination');
const totalCountSpan = document.getElementById('totalCount');
const currentPageSpan = document.getElementById('currentPage');
const imageModal = document.getElementById('imageModal');
const modalImage = document.getElementById('modalImage');

let currentPage = 1;
let totalPages = 1;

// 加载打卡记录
async function loadCheckins(page = 1) {
    try {
        const response = await fetch(`/api/checkins?page=${page}&limit=20`);
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

        const mediaHtml = mediaFiles.length > 0 ? `
            <div class="checkin-media">
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

        return `
            <div class="checkin-card">
                <div class="checkin-header">
                    <span class="checkin-id">#${checkin.id}</span>
                    <div class="checkin-time-group">
                        <span class="checkin-time-relative">${time}</span>
                        <span class="checkin-time-absolute">${formatAbsoluteTime(checkin.created_at)}</span>
                    </div>
                </div>
                <div class="checkin-content">${content}</div>
                ${mediaHtml}
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

// 页面加载时获取数据
loadCheckins(1);
