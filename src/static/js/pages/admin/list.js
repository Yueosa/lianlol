/**
 * 管理后台列表渲染模块
 */

import { approve, reject, ban } from './api.js';
import { showToast } from '../../common/toast.js';

// 当前选中的 ID 集合
const selectedIds = new Set();

// 渲染列表
export function renderList(items, container, onUpdate) {
    if (!items || items.length === 0) {
        container.innerHTML = '<div class="empty">暂无数据</div>';
        return;
    }

    container.innerHTML = items.map(item => renderItem(item)).join('');

    // 绑定事件
    bindItemEvents(container, onUpdate);
    updateBatchButtons();
}

// 渲染单个项目
function renderItem(item) {
    const statusClass = item.approved === 1 ? 'approved' : item.approved === 0 ? 'pending' : 'rejected';
    const avatarHtml = item.avatar 
        ? `<img src="${item.avatar}" alt="头像">`
        : '';
    
    const mediaHtml = item.media && item.media.length > 0
        ? `<div class="item-media">${item.media.map(m => `<img src="${m}" alt="图片" onclick="window.open('${m}', '_blank')">`).join('')}</div>`
        : '';

    const reasonHtml = item.review_reason
        ? `<div class="item-reason">⚠️ 触发原因: ${item.review_reason}</div>`
        : '';

    const actionsHtml = item.approved === 0
        ? `
            <div class="item-actions">
                <button class="action-btn approve" data-action="approve" data-id="${item.id}">✓ 通过</button>
                <button class="action-btn reject" data-action="reject" data-id="${item.id}">✗ 拒绝</button>
                <button class="action-btn ban" data-action="ban" data-id="${item.id}" data-fp="${item.fingerprint || ''}">🚫 加黑名单</button>
            </div>
        `
        : `
            <div class="item-actions">
                <button class="action-btn reject" data-action="reject" data-id="${item.id}">✗ 删除</button>
            </div>
        `;

    return `
        <div class="checkin-item ${statusClass}" data-id="${item.id}">
            <div class="item-checkbox">
                <input type="checkbox" class="item-select" data-id="${item.id}">
            </div>
            <div class="item-content">
                <div class="item-header">
                    <span class="item-nickname">
                        ${avatarHtml}
                        ${escapeHtml(item.nickname || '匿名')}
                    </span>
                    <div class="item-meta">
                        <span>ID: ${item.id}</span>
                        <span>${item.created_at}</span>
                        ${item.ip_location ? `<span>📍 ${item.ip_location}</span>` : ''}
                    </div>
                </div>
                <div class="item-body">
                    <div class="item-text">${escapeHtml(item.content || '').replace(/\n/g, '<br>')}</div>
                    ${mediaHtml}
                </div>
                ${reasonHtml}
                ${actionsHtml}
            </div>
        </div>
    `;
}

// 绑定项目事件
function bindItemEvents(container, onUpdate) {
    // 复选框事件
    container.querySelectorAll('.item-select').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            const id = parseInt(e.target.dataset.id);
            if (e.target.checked) {
                selectedIds.add(id);
            } else {
                selectedIds.delete(id);
            }
            updateBatchButtons();
        });
    });

    // 操作按钮事件
    container.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const action = btn.dataset.action;
            const id = parseInt(btn.dataset.id);
            
            btn.disabled = true;
            btn.textContent = '处理中...';

            try {
                if (action === 'approve') {
                    await approve(id);
                    showToast('✅ 已通过', 'success');
                } else if (action === 'reject') {
                    await reject(id);
                    showToast('✗ 已拒绝', 'success');
                } else if (action === 'ban') {
                    const fp = btn.dataset.fp;
                    await ban(id, fp);
                    showToast('🚫 已拒绝并加入黑名单', 'success');
                }
                onUpdate();
            } catch (err) {
                showToast(err.message, 'error');
                btn.disabled = false;
                btn.textContent = action === 'approve' ? '✓ 通过' : action === 'reject' ? '✗ 拒绝' : '🚫 加黑名单';
            }
        });
    });
}

// 更新批量按钮状态
function updateBatchButtons() {
    const approveBtn = document.getElementById('batchApproveBtn');
    const rejectBtn = document.getElementById('batchRejectBtn');
    
    if (approveBtn) approveBtn.disabled = selectedIds.size === 0;
    if (rejectBtn) rejectBtn.disabled = selectedIds.size === 0;
}

// 获取选中的 ID
export function getSelectedIds() {
    return Array.from(selectedIds);
}

// 清空选中
export function clearSelected() {
    selectedIds.clear();
    document.querySelectorAll('.item-select').forEach(cb => cb.checked = false);
    updateBatchButtons();
}

// 全选
export function selectAll() {
    document.querySelectorAll('.item-select').forEach(cb => {
        cb.checked = true;
        selectedIds.add(parseInt(cb.dataset.id));
    });
    updateBatchButtons();
}

// 转义 HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
