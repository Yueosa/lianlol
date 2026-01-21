/**
 * 搜索筛选模块
 */

let currentFilters = {};

/**
 * 获取当前筛选条件
 * @returns {Object}
 */
export function getFilters() {
    return { ...currentFilters };
}

/**
 * 清空筛选条件
 */
export function clearFilters() {
    currentFilters = {};
}

/**
 * 设置筛选条件
 * @param {Object} filters 
 */
export function setFilters(filters) {
    currentFilters = { ...filters };
}

/**
 * 初始化搜索面板
 * @param {Object} elements DOM 元素
 * @param {Function} onSearch 搜索回调
 */
export function initSearch(elements, onSearch) {
    const {
        searchToggle,
        searchContent,
        searchNickname,
        searchEmail,
        searchContentKeyword,
        excludeDefaultNickname,
        excludeShortContent,
        minContentLength,
        resetSearchBtn,
        applySearchBtn
    } = elements;

    // 面板切换
    searchToggle.addEventListener('click', () => {
        searchContent.classList.toggle('show');
        const icon = searchToggle.querySelector('.toggle-icon');
        icon.textContent = searchContent.classList.contains('show') ? '▲' : '▼';
    });

    // 重置搜索
    resetSearchBtn.addEventListener('click', () => {
        resetSearchForm(elements);
        clearFilters();
        onSearch();
    });

    // 应用搜索
    applySearchBtn.addEventListener('click', () => {
        applyFilters(elements);
        onSearch();
    });
}

/**
 * 重置搜索表单
 */
function resetSearchForm(elements) {
    elements.searchNickname.value = '';
    elements.searchEmail.value = '';
    elements.searchContentKeyword.value = '';
    elements.excludeDefaultNickname.checked = false;
    elements.excludeShortContent.checked = false;
    elements.minContentLength.value = '10';
}

/**
 * 应用筛选条件
 */
function applyFilters(elements) {
    const filters = {};
    
    const nickname = elements.searchNickname.value.trim();
    const email = elements.searchEmail.value.trim();
    const content = elements.searchContentKeyword.value.trim();
    
    if (nickname) filters.nickname = nickname;
    if (email) filters.email = email;
    if (content) filters.content = content;
    
    if (elements.excludeDefaultNickname.checked) {
        filters.exclude_default_nickname = true;
    }
    
    if (elements.excludeShortContent.checked) {
        const minLen = parseInt(elements.minContentLength.value) || 10;
        filters.min_content_length = minLen;
    }
    
    setFilters(filters);
}
