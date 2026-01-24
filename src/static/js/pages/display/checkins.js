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
    const { email, qq, url, file_type, archive_metadata } = checkin;
    const love = checkin.love || 0;
    const liked = checkin.liked || false;

    const contactsHtml = renderContacts(email, qq, url);
    const mediaHtml = renderMedia(mediaFiles, file_type, archive_metadata, checkin.id);
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
function renderMedia(mediaFiles, fileType, archiveMetadata, checkinId) {
    if (mediaFiles.length === 0) return '';

    // 如果是压缩包类型，显示预览图和下载按钮
    if (fileType === 'archive') {
        // 过滤出预览图（preview）和压缩包文件
        const previewImages = mediaFiles.filter(url => url.includes('/previews/'));
        const archiveFile = mediaFiles.find(url => url.includes('/archives/'));
        
        let metadata = null;
        if (archiveMetadata) {
            try {
                metadata = typeof archiveMetadata === 'string' ? JSON.parse(archiveMetadata) : archiveMetadata;
            } catch (e) {
                console.error('解析压缩包元数据失败:', e);
            }
        }

        // 渲染预览图
        const previewHtml = previewImages.length > 0 ? previewImages.map(url => `
            <div class="media-item" onclick="openImageModal('${url}')">
                <img src="${url}" alt="压缩包预览">
            </div>
        `).join('') : '';

        // 渲染压缩包信息和下载按钮
        const archiveInfo = metadata ? `
            <div class="archive-info">
                <div class="archive-icon">📦</div>
                <div class="archive-details">
                    <div class="archive-filename">${escapeHtml(metadata.filename || '压缩包')}</div>
                    <div class="archive-stats">
                        ${metadata.image_count ? `📷 ${metadata.image_count} 张图片` : ''}
                        ${metadata.total_files ? ` · 📄 ${metadata.total_files} 个文件` : ''}
                    </div>
                </div>
                <a href="/api/download/${checkinId}" class="archive-download-btn" download>
                    <span>📥 下载</span>
                </a>
            </div>
        ` : archiveFile ? `
            <div class="archive-info">
                <div class="archive-icon">📦</div>
                <div class="archive-details">
                    <div class="archive-filename">压缩包文件</div>
                </div>
                <a href="/api/download/${checkinId}" class="archive-download-btn" download>
                    <span>📥 下载</span>
                </a>
            </div>
        ` : '';

        return `
            <div class="card-media">
                ${previewHtml}
            </div>
            ${archiveInfo}
        `;
    }

    // 普通媒体文件（图片/视频）
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
