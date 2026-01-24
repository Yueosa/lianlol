/**
 * 管理后台主模块
 */

import { setAdminKey, verifyKey, getStats, getPendingList, getAllList, batchApprove, batchReject } from './api.js';
import { renderList, getSelectedIds, clearSelected, selectAll } from './list.js';
import { showToast } from '../../common/toast.js';

// 状态
let currentStatus = 'pending';
let currentPage = 1;
const pageSize = 20;

// DOM 元素
const loginSection = document.getElementById('loginSection');
const adminPanel = document.getElementById('adminPanel');
const adminKeyInput = document.getElementById('adminKeyInput');
const loginBtn = document.getElementById('loginBtn');
const loginError = document.getElementById('loginError');
const adminList = document.getElementById('adminList');
const adminPagination = document.getElementById('adminPagination');

// 初始化
function init() {
    // 尝试从 sessionStorage 恢复登录状态
    const savedKey = sessionStorage.getItem('adminKey');
    if (savedKey) {
        setAdminKey(savedKey);
        showPanel();
    }

    // 绑定登录事件
    loginBtn.addEventListener('click', handleLogin);
    adminKeyInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });

    // 绑定标签切换
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const status = btn.dataset.status;
            setActiveTab(status);
            loadList();
        });
    });

    // 绑定批量操作
    document.getElementById('selectAllBtn').addEventListener('click', selectAll);
    document.getElementById('batchApproveBtn').addEventListener('click', handleBatchApprove);
    document.getElementById('batchRejectBtn').addEventListener('click', handleBatchReject);
}

// 处理登录
async function handleLogin() {
    const key = adminKeyInput.value.trim();
    if (!key) {
        loginError.textContent = '请输入管理密钥';
        return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = '验证中...';
    loginError.textContent = '';

    const valid = await verifyKey(key);
    
    if (valid) {
        sessionStorage.setItem('adminKey', key);
        showPanel();
    } else {
        loginError.textContent = '密钥无效';
        loginBtn.disabled = false;
        loginBtn.textContent = '登录';
    }
}

// 显示管理面板
function showPanel() {
    loginSection.style.display = 'none';
    adminPanel.style.display = 'block';
    loadStats();
    loadList();
}

// 加载统计数据
async function loadStats() {
    try {
        const stats = await getStats();
        document.getElementById('statTotal').textContent = stats.total;
        document.getElementById('statApproved').textContent = stats.approved;
        document.getElementById('statPending').textContent = stats.pending;
    } catch (err) {
        showToast('加载统计失败: ' + err.message, 'error');
    }
}

// 设置激活标签
function setActiveTab(status) {
    currentStatus = status;
    currentPage = 1;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.status === status);
    });
}

// 加载列表
async function loadList() {
    adminList.innerHTML = '<div class="loading">加载中...</div>';
    clearSelected();

    try {
        let result;
        if (currentStatus === 'pending') {
            result = await getPendingList(currentPage, pageSize);
        } else if (currentStatus === 'approved') {
            result = await getAllList(currentPage, pageSize, true);
        } else {
            result = await getAllList(currentPage, pageSize, null);
        }

        renderList(result.items, adminList, () => {
            loadStats();
            loadList();
        });
        renderPagination(result.total, result.page, result.page_size);
    } catch (err) {
        adminList.innerHTML = `<div class="empty">加载失败: ${err.message}</div>`;
    }
}

// 渲染分页
function renderPagination(total, page, size) {
    const totalPages = Math.ceil(total / size);
    if (totalPages <= 1) {
        adminPagination.innerHTML = '';
        return;
    }

    let html = '';
    
    // 上一页
    html += `<button class="page-btn" ${page <= 1 ? 'disabled' : ''} data-page="${page - 1}">‹</button>`;
    
    // 页码
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(totalPages, page + 2);
    
    if (startPage > 1) {
        html += `<button class="page-btn" data-page="1">1</button>`;
        if (startPage > 2) html += '<span>...</span>';
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="page-btn ${i === page ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += '<span>...</span>';
        html += `<button class="page-btn" data-page="${totalPages}">${totalPages}</button>`;
    }
    
    // 下一页
    html += `<button class="page-btn" ${page >= totalPages ? 'disabled' : ''} data-page="${page + 1}">›</button>`;
    
    adminPagination.innerHTML = html;

    // 绑定分页事件
    adminPagination.querySelectorAll('.page-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const p = parseInt(btn.dataset.page);
            if (p && p !== currentPage) {
                currentPage = p;
                loadList();
            }
        });
    });
}

// 批量通过
async function handleBatchApprove() {
    const ids = getSelectedIds();
    if (ids.length === 0) return;

    if (!confirm(`确定要通过选中的 ${ids.length} 条记录吗？`)) return;

    try {
        const result = await batchApprove(ids);
        showToast(`✅ 已通过 ${result.updated} 条记录`, 'success');
        loadStats();
        loadList();
    } catch (err) {
        showToast('批量通过失败: ' + err.message, 'error');
    }
}

// 批量拒绝
async function handleBatchReject() {
    const ids = getSelectedIds();
    if (ids.length === 0) return;

    if (!confirm(`确定要拒绝选中的 ${ids.length} 条记录吗？`)) return;

    try {
        const result = await batchReject(ids);
        showToast(`✗ 已拒绝 ${result.deleted} 条记录`, 'success');
        loadStats();
        loadList();
    } catch (err) {
        showToast('批量拒绝失败: ' + err.message, 'error');
    }
}

// 启动
init();
