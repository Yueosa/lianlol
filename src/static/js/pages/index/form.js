/**
 * 表单处理模块
 */

import { validateEmail, validateURL } from '../../common/utils.js';
import { createCheckin } from '../../common/api.js';
import { getSelectedFiles, clearFiles, clearPreviews } from './upload.js';
import { resetAvatar } from './avatar.js';

/**
 * 初始化表单
 * @param {Object} elements DOM 元素集合
 * @param {Function} showMessage 显示消息函数
 * @param {Function} hideMessage 隐藏消息函数
 */
export function initForm(elements, showMessage, hideMessage) {
    const {
        form, contentInput, charCount, submitBtn, resetBtn,
        avatarTrigger, avatarInput, emojiGrid,
        nicknameInput, emailInput, qqInput, urlInput,
        previewContainer
    } = elements;

    // 字符计数
    contentInput.addEventListener('input', () => {
        charCount.textContent = contentInput.value.length;
    });

    // QQ号只允许数字
    qqInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/\D/g, '');
    });

    // 重置表单
    resetBtn.addEventListener('click', () => {
        if (confirm('确定要重置表单吗？')) {
            resetForm(elements, hideMessage);
        }
    });

    // 提交表单
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleSubmit(elements, showMessage, hideMessage);
    });
}

/**
 * 重置表单
 */
function resetForm(elements, hideMessage) {
    const {
        form, charCount, avatarTrigger, avatarInput, emojiGrid,
        nicknameInput, previewContainer
    } = elements;

    form.reset();
    clearPreviews(previewContainer);
    charCount.textContent = '0';
    resetAvatar(avatarTrigger, avatarInput, emojiGrid);
    nicknameInput.value = '';
    hideMessage();
}

/**
 * 处理表单提交
 */
async function handleSubmit(elements, showMessage, hideMessage) {
    const {
        form, contentInput, submitBtn,
        avatarInput, nicknameInput, emailInput, qqInput, urlInput,
        previewContainer, charCount, avatarTrigger, emojiGrid
    } = elements;

    const content = contentInput.value.trim();
    if (!content) {
        showMessage('请输入内容', 'error');
        return;
    }

    // 获取用户信息
    const nickname = nicknameInput.value.trim() || '用户0721';
    const email = emailInput.value.trim();
    const qq = qqInput.value.trim();
    const url = urlInput.value.trim();
    const avatar = avatarInput.value.trim() || '🥰';

    // 验证
    if (email && !validateEmail(email)) {
        showMessage('邮箱格式不正确', 'error');
        return;
    }

    if (qq && (qq.length < 5 || qq.length > 11 || !/^\d+$/.test(qq))) {
        showMessage('QQ号格式不正确（5-11位数字）', 'error');
        return;
    }

    if (url && !validateURL(url)) {
        showMessage('URL格式不正确（必须以 http:// 或 https:// 开头）', 'error');
        return;
    }

    if (nickname.length > 20) {
        showMessage('昵称长度不能超过20个字符', 'error');
        return;
    }

    // 创建 FormData
    const formData = new FormData();
    formData.append('content', content);
    formData.append('nickname', nickname);
    formData.append('avatar', avatar);
    
    if (email) formData.append('email', email);
    if (qq) formData.append('qq', qq);
    if (url) formData.append('url', url);

    // 添加文件
    const selectedFiles = getSelectedFiles();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    // 禁用提交按钮
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="btn-text">⏳ 记录中...</span>';

    try {
        const result = await createCheckin(formData);

        if (result.success) {
            const mediaMsg = result.media_count > 0 ? `已上传 ${result.media_count} 个文件` : '';
            showMessage(`✅ 记录成功！${mediaMsg}`, 'success');
            
            // 重置表单
            setTimeout(() => {
                form.reset();
                clearPreviews(previewContainer);
                charCount.textContent = '0';
                resetAvatar(avatarTrigger, avatarInput, emojiGrid);
                nicknameInput.value = '';
                hideMessage();
            }, 2000);
        } else {
            showMessage(`❌ ${result.message || '记录失败'}`, 'error');
        }
    } catch (error) {
        console.error('提交失败:', error);
        showMessage('❌ 网络错误，请稍后重试', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span class="btn-text">💦 记录这一发</span><span class="btn-icon">→</span>';
    }
}
