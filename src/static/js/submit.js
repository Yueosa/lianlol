// 打卡提交页面逻辑

const form = document.getElementById('checkinForm');
const contentInput = document.getElementById('content');
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const previewContainer = document.getElementById('previewContainer');
const charCount = document.getElementById('charCount');
const submitBtn = document.getElementById('submitBtn');
const resetBtn = document.getElementById('resetBtn');
const messageDiv = document.getElementById('message');

// 新增字段
const avatarInput = document.getElementById('avatar');
const avatarTrigger = document.getElementById('avatarTrigger');
const emojiDropdown = document.getElementById('emojiDropdown');
const emojiGrid = document.getElementById('emojiGrid');
const nicknameInput = document.getElementById('nickname');
const emailInput = document.getElementById('email');
const qqInput = document.getElementById('qq');
const urlInput = document.getElementById('url');

let selectedFiles = [];

// Telegram风格emoji选择器
avatarTrigger.addEventListener('click', (e) => {
    e.stopPropagation();
    emojiDropdown.classList.toggle('show');
});

// 点击其他地方关闭dropdown
document.addEventListener('click', (e) => {
    if (!emojiDropdown.contains(e.target) && e.target !== avatarTrigger) {
        emojiDropdown.classList.remove('show');
    }
});

// Emoji选择
emojiGrid.addEventListener('click', (e) => {
    if (e.target.classList.contains('emoji-btn')) {
        const emoji = e.target.dataset.emoji;
        avatarInput.value = emoji;
        avatarTrigger.textContent = emoji;
        emojiDropdown.classList.remove('show');
        
        // 移除其他选中状态
        document.querySelectorAll('.emoji-btn').forEach(btn => {
            btn.classList.remove('selected');
        });
        e.target.classList.add('selected');
    }
});

// 初始化：选中默认emoji
document.addEventListener('DOMContentLoaded', () => {
    const defaultEmoji = avatarInput.value;
    const defaultBtn = document.querySelector(`[data-emoji="${defaultEmoji}"]`);
    if (defaultBtn) {
        defaultBtn.classList.add('selected');
    }
});

// QQ号输入验证（只允许数字）
qqInput.addEventListener('input', (e) => {
    e.target.value = e.target.value.replace(/\D/g, '');
});

// 字符计数
contentInput.addEventListener('input', () => {
    charCount.textContent = contentInput.value.length;
});

// 文件上传区域点击
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// 文件选择
fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

// 拖拽上传
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

// 处理文件
function handleFiles(files) {
    const maxSize = 20 * 1024 * 1024; // 20MB
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'video/mp4', 'video/webm', 'video/quicktime'];

    Array.from(files).forEach(file => {
        // 检查文件大小
        if (file.size > maxSize) {
            showMessage(`文件 ${file.name} 超过 20MB 限制`, 'error');
            return;
        }

        // 检查文件类型
        if (!allowedTypes.includes(file.type)) {
            showMessage(`不支持的文件格式: ${file.name}`, 'error');
            return;
        }

        // 添加到选中文件列表
        selectedFiles.push(file);
        createPreview(file);
    });
}

// 创建预览
function createPreview(file) {
    const previewItem = document.createElement('div');
    previewItem.className = 'preview-item';

    const reader = new FileReader();
    reader.onload = (e) => {
        let content;
        if (file.type.startsWith('image/')) {
            content = `<img src="${e.target.result}" alt="${file.name}">`;
        } else if (file.type.startsWith('video/')) {
            content = `<video src="${e.target.result}" controls></video>`;
        }

        previewItem.innerHTML = `
            ${content}
            <button type="button" class="preview-remove" data-filename="${file.name}">×</button>
        `;

        // 删除按钮事件
        previewItem.querySelector('.preview-remove').addEventListener('click', () => {
            removeFile(file.name);
            previewItem.remove();
        });

        previewContainer.appendChild(previewItem);
    };

    reader.readAsDataURL(file);
}

// 移除文件
function removeFile(filename) {
    selectedFiles = selectedFiles.filter(f => f.name !== filename);
}

// 重置表单
resetBtn.addEventListener('click', () => {
    if (confirm('确定要重置表单吗？')) {
        form.reset();
        selectedFiles = [];
        previewContainer.innerHTML = '';
        charCount.textContent = '0';
        hideMessage();
    }
});

// 提交表单
form.addEventListener('submit', async (e) => {
    e.preventDefault();

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

    // 前端验证
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
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    // 禁用提交按钮
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="btn-text">⏳ 记录中...</span>';

    try {
        const response = await fetch('/api/checkin', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            showMessage(`✅ 记录成功！${result.media_count > 0 ? `已上传 ${result.media_count} 个文件` : ''}`, 'success');
            
            // 重置表单
            setTimeout(() => {
                form.reset();
                selectedFiles = [];
                previewContainer.innerHTML = '';
                charCount.textContent = '0';
                avatarInput.value = '🥰';
                avatarTrigger.textContent = '🥰';
                nicknameInput.value = '';
                
                // 重新选中默认 emoji
                document.querySelectorAll('.emoji-btn').forEach(btn => {
                    btn.classList.remove('selected');
                });
                const defaultBtn = document.querySelector('[data-emoji="🥰"]');
                if (defaultBtn) defaultBtn.classList.add('selected');
                
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
});

// 邮箱验证
function validateEmail(email) {
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(email);
}

// URL验证
function validateURL(url) {
    return url.startsWith('http://') || url.startsWith('https://');
}

// 显示消息
function showMessage(text, type = 'success') {
    messageDiv.textContent = text;
    messageDiv.className = `message show ${type}`;
}

// 隐藏消息
function hideMessage() {
    messageDiv.className = 'message';
}
