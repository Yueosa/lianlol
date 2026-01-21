/**
 * 打卡列表渲染模块
 */

import { escapeHtml, parseUrls, formatRelativeTime, formatAbsoluteTime, copyToClipboard } from '../../common/utils.js';
import { showToast } from '../../common/toast.js';

/**
 * 渲染打卡列表
 * @param {HTMLElement} container 列表容器
 * @param {Array} checkins 打卡数据
 */
export function renderCheckins(container, checkins) {
    if (checkins.length === 0) {
        container.innerHTML = '<div class="loading">暂无打卡记录</div>';
        return;
    }

    container.innerHTML = checkins.map(renderCheckinCard).join('');
}

/**
 * 渲染单个打卡卡片
 * @param {Object} checkin 
 * @returns {string}
 */
function renderCheckinCard(checkin) {
    const content = parseUrls(escapeHtml(checkin.content));
    const mediaFiles = checkin.media_files || [];
    const time = formatRelativeTime(checkin.created_at);

    const avatar = checkin.avatar || '🥰';
    const nickname = checkin.nickname || '用户0721';
    const { email, qq, url } = checkin;
    const love = checkin.love || 0;
    const liked = checkin.liked || false;

    const contactsHtml = renderContacts(email, qq, url);
    const mediaHtml = renderMedia(mediaFiles);
    const likeHtml = renderLikeButton(checkin.id, love, liked);

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
}

/**
 * 渲染联系方式
 */
function renderContacts(email, qq, url) {
    if (!email && !qq && !url) return '';

    const items = [];
    
    if (email) {
        items.push(`
            <span class="contact-item contact-email" title="点击复制邮箱" onclick="copyContact('${escapeHtml(email)}', '邮箱')">
                <span class="contact-icon">📧</span>
                <span class="contact-text">${escapeHtml(email)}</span>
            </span>
        `);
    }
    
    if (qq) {
        items.push(`
            <span class="contact-item contact-qq" title="点击复制QQ号" onclick="copyContact('${escapeHtml(qq)}', 'QQ号')">
                <span class="contact-icon">🐧</span>
                <span class="contact-text">${escapeHtml(qq)}</span>
            </span>
        `);
    }
    
    if (url) {
        const displayUrl = url.length > 30 ? url.substring(0, 30) + '...' : url;
        items.push(`
            <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="contact-item contact-url" title="点击访问链接">
                <span class="contact-icon">🔗</span>
                <span class="contact-text">${escapeHtml(displayUrl)}</span>
            </a>
        `);
    }

    return `<div class="card-contacts">${items.join('')}</div>`;
}

/**
 * 渲染媒体文件
 */
function renderMedia(mediaFiles) {
    if (mediaFiles.length === 0) return '';

    const items = mediaFiles.map(url => {
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
    }).join('');

    return `<div class="card-media">${items}</div>`;
}

/**
 * 渲染点赞按钮
 */
function renderLikeButton(id, love, liked) {
    const likeClass = liked ? 'like-btn liked' : 'like-btn';
    return `
        <button class="${likeClass}" data-id="${id}" onclick="handleLike(${id}, this)">
            <span class="like-icon">${liked ? '❤️' : '🤍'}</span>
            <span class="like-count">${love}</span>
        </button>
    `;
}

/**
 * 复制联系方式
 */
function copyContact(text, label) {
    copyToClipboard(
        text, 
        label,
        () => showToast(`✅ ${label}已复制: ${text}`),
        () => showToast(`❌ 复制失败，请手动复制: ${text}`)
    );
}

// 暴露到全局
window.copyContact = copyContact;
