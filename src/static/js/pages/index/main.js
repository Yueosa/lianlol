/**
 * Index 页面主入口
 * 打卡提交页面
 */

import '../../common/theme.js';
import { initAvatarPicker } from './avatar.js';
import { initUpload } from './upload.js';
import { initForm } from './form.js';

// DOM 元素
const elements = {
    form: document.getElementById('checkinForm'),
    contentInput: document.getElementById('content'),
    fileInput: document.getElementById('fileInput'),
    uploadArea: document.getElementById('uploadArea'),
    previewContainer: document.getElementById('previewContainer'),
    charCount: document.getElementById('charCount'),
    submitBtn: document.getElementById('submitBtn'),
    resetBtn: document.getElementById('resetBtn'),
    messageDiv: document.getElementById('message'),
    
    // 用户信息
    avatarInput: document.getElementById('avatar'),
    avatarTrigger: document.getElementById('avatarTrigger'),
    emojiDropdown: document.getElementById('emojiDropdown'),
    emojiGrid: document.getElementById('emojiGrid'),
    nicknameInput: document.getElementById('nickname'),
    emailInput: document.getElementById('email'),
    qqInput: document.getElementById('qq'),
    urlInput: document.getElementById('url')
};

// 消息显示
function showMessage(text, type = 'success') {
    elements.messageDiv.textContent = text;
    elements.messageDiv.className = `message show ${type}`;
}

function hideMessage() {
    elements.messageDiv.className = 'message';
}

// 初始化各模块
document.addEventListener('DOMContentLoaded', () => {
    // 头像选择器
    initAvatarPicker(
        elements.avatarTrigger,
        elements.emojiDropdown,
        elements.emojiGrid,
        elements.avatarInput
    );

    // 文件上传
    initUpload(
        elements.uploadArea,
        elements.fileInput,
        elements.previewContainer,
        (error) => showMessage(error, 'error')
    );

    // 表单处理
    initForm(elements, showMessage, hideMessage);
});
