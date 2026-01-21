/**
 * 文件上传模块
 */

const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB
const ALLOWED_TYPES = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'video/mp4', 'video/webm', 'video/quicktime'
];

/**
 * 已选择的文件列表
 */
let selectedFiles = [];

/**
 * 获取已选择的文件
 * @returns {File[]}
 */
export function getSelectedFiles() {
    return selectedFiles;
}

/**
 * 清空已选择的文件
 */
export function clearFiles() {
    selectedFiles = [];
}

/**
 * 初始化上传功能
 * @param {HTMLElement} uploadArea 上传区域
 * @param {HTMLInputElement} fileInput 文件输入框
 * @param {HTMLElement} previewContainer 预览容器
 * @param {Function} onError 错误回调
 */
export function initUpload(uploadArea, fileInput, previewContainer, onError) {
    // 点击上传区域
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // 文件选择
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files, previewContainer, onError);
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
        handleFiles(e.dataTransfer.files, previewContainer, onError);
    });
}

/**
 * 处理文件
 * @param {FileList} files 
 * @param {HTMLElement} previewContainer 
 * @param {Function} onError 
 */
function handleFiles(files, previewContainer, onError) {
    Array.from(files).forEach(file => {
        // 检查文件大小
        if (file.size > MAX_FILE_SIZE) {
            onError(`文件 ${file.name} 超过 20MB 限制`);
            return;
        }

        // 检查文件类型
        if (!ALLOWED_TYPES.includes(file.type)) {
            onError(`不支持的文件格式: ${file.name}`);
            return;
        }

        // 添加到列表
        selectedFiles.push(file);
        createPreview(file, previewContainer);
    });
}

/**
 * 创建预览
 * @param {File} file 
 * @param {HTMLElement} container 
 */
function createPreview(file, container) {
    const previewItem = document.createElement('div');
    previewItem.className = 'preview-item';

    const reader = new FileReader();
    reader.onload = (e) => {
        const isImage = file.type.startsWith('image/');
        const content = isImage
            ? `<img src="${e.target.result}" alt="${file.name}">`
            : `<video src="${e.target.result}" controls></video>`;

        previewItem.innerHTML = `
            ${content}
            <button type="button" class="preview-remove" data-filename="${file.name}">×</button>
        `;

        // 删除按钮
        previewItem.querySelector('.preview-remove').addEventListener('click', () => {
            removeFile(file.name);
            previewItem.remove();
        });

        container.appendChild(previewItem);
    };

    reader.readAsDataURL(file);
}

/**
 * 移除文件
 * @param {string} filename 
 */
function removeFile(filename) {
    selectedFiles = selectedFiles.filter(f => f.name !== filename);
}

/**
 * 清空预览
 * @param {HTMLElement} container 
 */
export function clearPreviews(container) {
    container.innerHTML = '';
    clearFiles();
}
