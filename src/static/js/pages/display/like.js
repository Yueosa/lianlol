/**
 * 点赞模块
 */

import { likeCheckin, getLikedCheckinIds, saveLikedCheckinIds } from '../../common/api.js';
import { showToast } from '../../common/toast.js';

/**
 * 处理点赞
 * @param {number} checkinId 
 * @param {HTMLElement} button 
 */
export async function handleLike(checkinId, button) {
    // 防止重复点击
    if (button.disabled) return;
    button.disabled = true;
    
    // 检查本地是否已点赞
    const likedIds = getLikedCheckinIds();
    if (likedIds.includes(checkinId)) {
        showToast('你已经点过赞了 💕');
        button.disabled = false;
        return;
    }
    
    try {
        const result = await likeCheckin(checkinId);
        
        if (result.success) {
            // 更新按钮状态
            button.classList.add('liked');
            button.querySelector('.like-icon').textContent = '❤️';
            button.querySelector('.like-count').textContent = result.love;
            
            // 保存到 localStorage
            likedIds.push(checkinId);
            saveLikedCheckinIds(likedIds);
            
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

// 暴露到全局，供 onclick 使用
window.handleLike = handleLike;
