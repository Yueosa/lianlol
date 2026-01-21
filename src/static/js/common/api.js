/**
 * API 请求模块
 * 封装与后端的通信
 */

const API_BASE = '/api';

/**
 * 通用请求函数
 * @param {string} endpoint 
 * @param {RequestInit} options 
 * @returns {Promise<any>}
 */
async function request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                ...options.headers
            }
        });
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error(`API请求失败: ${endpoint}`, error);
        throw error;
    }
}

/**
 * 获取打卡记录列表
 * @param {Object} params 查询参数
 * @returns {Promise<Object>}
 */
export async function getCheckins(params = {}) {
    const searchParams = new URLSearchParams(params);
    return request(`/checkins?${searchParams}`);
}

/**
 * 提交打卡
 * @param {FormData} formData 
 * @returns {Promise<Object>}
 */
export async function createCheckin(formData) {
    return request('/checkin', {
        method: 'POST',
        body: formData
    });
}

/**
 * 上传文件
 * @param {File} file 
 * @returns {Promise<Object>}
 */
export async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    return request('/upload', {
        method: 'POST',
        body: formData
    });
}

/**
 * 点赞
 * @param {number} checkinId 
 * @returns {Promise<Object>}
 */
export async function likeCheckin(checkinId) {
    return request(`/like/${checkinId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });
}

/**
 * 获取已点赞的打卡ID列表
 * @returns {number[]}
 */
export function getLikedCheckinIds() {
    return JSON.parse(localStorage.getItem('likedCheckins') || '[]');
}

/**
 * 保存已点赞的打卡ID
 * @param {number[]} ids 
 */
export function saveLikedCheckinIds(ids) {
    localStorage.setItem('likedCheckins', JSON.stringify(ids));
}
