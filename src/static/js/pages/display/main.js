/**
 * Display 页面主入口
 * 打卡展示页面
 */

import '../../common/theme.js';
import { getCheckins } from '../../common/api.js';
import { initSearch, getFilters, clearFilters } from './search.js';
import { initSort, getSortState } from './sort.js';
import { renderPagination } from './pagination.js';
import { renderCheckins } from './checkins.js';
import { initModal } from './modal.js';
import './like.js'; // 导入以注册全局 handleLike

// 状态
let currentPage = 1;
let totalPages = 1;

// DOM 元素
const elements = {
    // 列表容器
    checkinsList: document.getElementById('checkinsList'),
    pagination: document.getElementById('pagination'),
    totalCountSpan: document.getElementById('totalCount'),
    currentPageSpan: document.getElementById('currentPage'),
    
    // 搜索面板
    searchToggle: document.getElementById('searchToggle'),
    searchContent: document.getElementById('searchContent'),
    searchNickname: document.getElementById('searchNickname'),
    searchEmail: document.getElementById('searchEmail'),
    searchContentKeyword: document.getElementById('searchContentKeyword'),
    excludeDefaultNickname: document.getElementById('excludeDefaultNickname'),
    excludeShortContent: document.getElementById('excludeShortContent'),
    minContentLength: document.getElementById('minContentLength'),
    resetSearchBtn: document.getElementById('resetSearch'),
    applySearchBtn: document.getElementById('applySearch'),
    
    // 排序按钮
    sortDescBtn: document.getElementById('sortDesc'),
    sortAscBtn: document.getElementById('sortAsc'),
    sortLoveBtn: document.getElementById('sortLove'),
    
    // 模态框
    imageModal: document.getElementById('imageModal'),
    modalImage: document.getElementById('modalImage')
};

/**
 * 加载打卡记录
 * @param {number} page 
 */
async function loadCheckins(page = 1) {
    try {
        const { sort, sortBy } = getSortState();
        const filters = getFilters();
        
        const params = {
            page,
            limit: 20,
            sort,
            sort_by: sortBy,
            ...filters
        };
        
        const result = await getCheckins(params);

        if (result.success) {
            currentPage = result.page;
            totalPages = result.pages;
            
            // 更新统计
            elements.totalCountSpan.textContent = result.total;
            elements.currentPageSpan.textContent = currentPage;

            // 渲染列表
            renderCheckins(elements.checkinsList, result.data);

            // 渲染分页
            renderPagination(
                elements.pagination,
                currentPage,
                totalPages,
                loadCheckins
            );
        }
    } catch (error) {
        console.error('加载失败:', error);
        elements.checkinsList.innerHTML = '<div class="loading">❌ 加载失败，请刷新重试</div>';
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化搜索
    initSearch(elements, () => loadCheckins(1));
    
    // 初始化排序
    initSort({
        sortDescBtn: elements.sortDescBtn,
        sortAscBtn: elements.sortAscBtn,
        sortLoveBtn: elements.sortLoveBtn
    }, () => loadCheckins(1));
    
    // 初始化模态框
    initModal(elements.imageModal, elements.modalImage);
    
    // 加载数据
    loadCheckins(1);
});
