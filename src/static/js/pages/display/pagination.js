/**
 * 分页模块
 */

/**
 * 渲染分页控件
 * @param {HTMLElement} container 分页容器
 * @param {number} currentPage 当前页
 * @param {number} totalPages 总页数
 * @param {Function} onPageChange 页面变化回调
 */
export function renderPagination(container, currentPage, totalPages, onPageChange) {
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '';
    const maxButtons = 5;

    // 上一页
    html += `
        <button ${currentPage === 1 ? 'disabled' : ''} data-page="${currentPage - 1}">
            ← 上一页
        </button>
    `;

    // 计算页码范围
    let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);

    if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }

    // 第一页
    if (startPage > 1) {
        html += `<button data-page="1">1</button>`;
        if (startPage > 2) {
            html += `<button disabled>...</button>`;
        }
    }

    // 页码按钮
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <button 
                class="${i === currentPage ? 'active' : ''}" 
                data-page="${i}"
            >
                ${i}
            </button>
        `;
    }

    // 最后一页
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<button disabled>...</button>`;
        }
        html += `<button data-page="${totalPages}">${totalPages}</button>`;
    }

    // 下一页
    html += `
        <button ${currentPage === totalPages ? 'disabled' : ''} data-page="${currentPage + 1}">
            下一页 →
        </button>
    `;

    container.innerHTML = html;

    // 绑定事件
    container.querySelectorAll('button:not([disabled])').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = parseInt(btn.dataset.page);
            if (page && page !== currentPage) {
                onPageChange(page);
            }
        });
    });
}
