/**
 * 管理后台 API 模块
 */

let adminKey = '';

export function setAdminKey(key) {
    adminKey = key;
}

export function getAdminKey() {
    return adminKey;
}

async function apiRequest(endpoint, options = {}) {
    const headers = {
        'X-Admin-Key': adminKey,
        ...options.headers
    };

    const response = await fetch(`/api/admin${endpoint}`, {
        ...options,
        headers
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '请求失败' }));
        throw new Error(error.detail || '请求失败');
    }

    return response.json();
}

// 验证密钥
export async function verifyKey(key) {
    const tempKey = adminKey;
    adminKey = key;
    try {
        await apiRequest('/stats');
        return true;
    } catch (e) {
        adminKey = tempKey;
        return false;
    }
}

// 获取统计数据
export async function getStats() {
    const res = await apiRequest('/stats');
    return res.data;
}

// 获取待审核列表
export async function getPendingList(page = 1, pageSize = 20) {
    const res = await apiRequest(`/pending?page=${page}&limit=${pageSize}`);
    return res.data;
}

// 获取全部列表
export async function getAllList(page = 1, pageSize = 20, approvedOnly = null) {
    let url = `/all?page=${page}&limit=${pageSize}`;
    if (approvedOnly !== null) {
        url += `&status=${approvedOnly ? 'approved' : 'all'}`;
    }
    return apiRequest(url).then(res => res.data);
}

// 通过审核
export async function approve(id) {
    return apiRequest(`/approve/${id}`, { method: 'POST' });
}

// 拒绝
export async function reject(id) {
    return apiRequest(`/reject/${id}`, { method: 'POST' });
}

// 拒绝并加入黑名单
export async function ban(id, fingerprint) {
    return apiRequest(`/ban/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fingerprint })
    });
}

// 批量通过
export async function batchApprove(ids) {
    return apiRequest('/batch/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids })
    });
}

// 批量拒绝
export async function batchReject(ids) {
    return apiRequest('/batch/reject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids })
    });
}
