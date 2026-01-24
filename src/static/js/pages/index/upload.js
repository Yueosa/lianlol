/**
 * 文件上传模块
 */

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ALLOWED_TYPES = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'video/mp4', 'video/webm', 'video/quicktime',
    'application/zip', 'application/x-zip-compressed',
    'application/x-7z-compressed'
];

// 文件扩展名到 MIME 类型的映射
const EXTENSION_TYPES = {
    '.zip': 'application/zip',
    '.7z': 'application/x-7z-compressed'
};

/**
 * 已选择的文件列表
 */
let selectedFiles = [];

/**
 * 压缩包预览图选择数据
 */
let archivePreviewData = null;

/**
 * 压缩包内的图片列表（用于选择预览图）
 */
let archiveImageList = [];

/**
 * 获取已选择的文件
 * @returns {File[]}
 */
export function getSelectedFiles() {
    return selectedFiles;
}

/**
 * 获取压缩包预览图选择数据
 * @returns {object|null}
 */
export function getArchivePreviewData() {
    return archivePreviewData;
}

/**
 * 设置压缩包预览图选择数据
 * @param {string[]} images 
 */
export function setArchivePreviewData(images) {
    archivePreviewData = images;
}

/**
 * 清空已选择的文件
 */
export function clearFiles() {
    selectedFiles = [];
    archivePreviewData = null;
    archiveImageList = [];
}

/**
 * 上传区域元素引用
 */
let uploadAreaElement = null;
let uploadAreaOriginalHTML = '';

/**
 * 初始化上传功能
 * @param {HTMLElement} uploadArea 上传区域
 * @param {HTMLInputElement} fileInput 文件输入框
 * @param {HTMLElement} previewContainer 预览容器
 * @param {Function} onError 错误回调
 */
export function initUpload(uploadArea, fileInput, previewContainer, onError) {
    // 保存引用
    uploadAreaElement = uploadArea;
    uploadAreaOriginalHTML = uploadArea.innerHTML;
    
    // 点击上传区域
    uploadArea.addEventListener('click', (e) => {
        // 如果点击的是按钮，不触发文件选择
        if (e.target.closest('button')) return;
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
            onError(`文件 ${file.name} 超过 50MB 限制`);
            return;
        }

        // 检查文件类型（支持通过扩展名判断）
        const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        const isAllowedType = ALLOWED_TYPES.includes(file.type) || EXTENSION_TYPES[ext];
        
        if (!isAllowedType) {
            onError(`不支持的文件格式: ${file.name}`);
            return;
        }

        // 检查是否为压缩包
        const isArchive = file.type.includes('zip') || file.type.includes('7z') || 
                         ext === '.zip' || ext === '.7z';
        
        if (isArchive) {
            // 检查是否已有压缩包
            const hasArchive = selectedFiles.some(f => {
                const fExt = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
                return f.type.includes('zip') || f.type.includes('7z') || 
                       fExt === '.zip' || fExt === '.7z';
            });
            
            if (hasArchive) {
                onError('一次只能上传一个压缩包');
                return;
            }
            
            // 如果上传压缩包，清空之前选择的所有文件
            if (selectedFiles.length > 0) {
                onError('上传压缩包时不能同时上传其他文件，已清空之前的选择');
                selectedFiles = [];
                previewContainer.innerHTML = '';
                archivePreviewData = null;
                archiveImageList = [];
            }
        } else {
            // 如果已有压缩包，不允许上传其他文件
            const hasArchive = selectedFiles.some(f => {
                const fExt = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
                return f.type.includes('zip') || f.type.includes('7z') || 
                       fExt === '.zip' || fExt === '.7z';
            });
            
            if (hasArchive) {
                onError('已选择压缩包，不能同时上传其他文件');
                return;
            }
        }

        // 添加到列表
        selectedFiles.push(file);
        createPreview(file, previewContainer, onError);
    });
}

/**
 * 创建预览
 * @param {File} file 
 * @param {HTMLElement} container 
 * @param {Function} onError
 */
function createPreview(file, container, onError) {
    const isImage = file.type.startsWith('image/');
    const isVideo = file.type.startsWith('video/');
    const isArchive = file.type.includes('zip') || file.type.includes('7z') || 
                     file.name.endsWith('.zip') || file.name.endsWith('.7z');

    if (isArchive) {
        // 压缩包直接显示在 upload-area 中
        showArchiveInUploadArea(file, onError);
    } else {
        // 图片和视频预览仍然显示在 preview-container 中
        const previewItem = document.createElement('div');
        previewItem.className = 'preview-item';
        
        const reader = new FileReader();
        reader.onload = (e) => {
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
}

/**
 * 在 upload-area 中显示压缩包
 * @param {File} file 
 * @param {Function} onError
 */
function showArchiveInUploadArea(file, onError) {
    if (!uploadAreaElement) return;
    
    uploadAreaElement.classList.add('has-archive');
    uploadAreaElement.innerHTML = `
        <div class="archive-upload-display">
            <div class="archive-header">
                <div class="archive-icon-large">📦</div>
                <button type="button" class="archive-remove" title="移除">×</button>
            </div>
            <div class="archive-info">
                <div class="archive-filename">${file.name}</div>
                <div class="archive-filesize">${formatFileSize(file.size)}</div>
            </div>
            <div class="archive-status-area">
                <div class="archive-loading">
                    <div class="spinner-small"></div>
                    <span>正在解析压缩包...</span>
                </div>
            </div>
            <div class="archive-actions" style="display: none;">
                <button type="button" class="btn btn-select-preview">📷 选择预览图</button>
            </div>
        </div>
    `;
    
    // 移除按钮事件
    uploadAreaElement.querySelector('.archive-remove').addEventListener('click', (e) => {
        e.stopPropagation();
        removeArchiveFromUploadArea();
    });
    
    // 解析压缩包
    preUploadArchiveNew(file, onError);
}

/**
 * 从 upload-area 移除压缩包
 */
function removeArchiveFromUploadArea() {
    if (!uploadAreaElement) return;
    
    // 清除压缩包文件
    selectedFiles = selectedFiles.filter(f => {
        const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
        return !(f.type.includes('zip') || f.type.includes('7z') || ext === '.zip' || ext === '.7z');
    });
    archivePreviewData = null;
    archiveImageList = [];
    
    // 恢复原始内容
    uploadAreaElement.classList.remove('has-archive');
    uploadAreaElement.innerHTML = uploadAreaOriginalHTML;
}

// 图片扩展名
const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'];

/**
 * 客户端解压 ZIP 并生成预览（无需上传）
 * @param {File} file 
 * @param {Function} onError
 */
async function preUploadArchiveNew(file, onError) {
    const statusArea = uploadAreaElement.querySelector('.archive-status-area');
    const actionsArea = uploadAreaElement.querySelector('.archive-actions');
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    // 7z 格式回退到服务器处理（浏览器不支持）
    if (ext === '.7z') {
        statusArea.innerHTML = `<div class="archive-loading">⏳ 解析 7z 文件中（需上传到服务器）...</div>`;
        return preUploadArchiveServer(file, onError, statusArea, actionsArea);
    }
    
    // ZIP 格式：客户端解压
    statusArea.innerHTML = `<div class="archive-loading">⏳ 解析中...</div>`;
    
    try {
        const zip = await JSZip.loadAsync(file);
        
        // 列出所有图片文件
        const imageFiles = [];
        let totalFiles = 0;
        
        zip.forEach((relativePath, zipEntry) => {
            if (!zipEntry.dir) {
                totalFiles++;
                const extLower = relativePath.substring(relativePath.lastIndexOf('.')).toLowerCase();
                if (IMAGE_EXTENSIONS.includes(extLower)) {
                    imageFiles.push(relativePath);
                }
            }
        });
        
        // 排序（按文件名）
        imageFiles.sort();
        
        // 生成缩略图（最多50张，并行处理加速）
        const maxThumbnails = 50;
        const imagesToProcess = imageFiles.slice(0, maxThumbnails);
        
        statusArea.innerHTML = `<div class="archive-loading">⏳ 生成预览图 0/${imagesToProcess.length}...</div>`;
        
        // 并行生成缩略图（每批10张）
        const batchSize = 10;
        const results = [];
        
        for (let i = 0; i < imagesToProcess.length; i += batchSize) {
            const batch = imagesToProcess.slice(i, i + batchSize);
            const batchResults = await Promise.all(
                batch.map(async (path) => {
                    try {
                        const blob = await zip.file(path).async('blob');
                        const thumbnail = await generateThumbnailClient(blob);
                        return { path, name: path.split('/').pop(), thumbnail };
                    } catch (e) {
                        return { path, name: path.split('/').pop(), thumbnail: null };
                    }
                })
            );
            results.push(...batchResults);
            statusArea.innerHTML = `<div class="archive-loading">⏳ 生成预览图 ${results.length}/${imagesToProcess.length}...</div>`;
        }
        
        archiveImageList = results;
        
        // 更新状态区域
        statusArea.innerHTML = `
            <div class="archive-stats">
                <span class="stat-item">📷 ${imageFiles.length} 张图片</span>
                <span class="stat-item">📁 ${totalFiles} 个文件</span>
            </div>
        `;
        
        if (imageFiles.length > 0) {
            actionsArea.style.display = 'flex';
            actionsArea.querySelector('.btn-select-preview').addEventListener('click', (e) => {
                e.stopPropagation();
                showPreviewSelector(archiveImageList);
            });
        }
        
    } catch (error) {
        console.warn('客户端解压失败，回退到服务器处理:', error.message);
        statusArea.innerHTML = `<div class="archive-loading">⏳ 本地解析失败，使用服务器解析...</div>`;
        // 回退到服务器方案
        return preUploadArchiveServer(file, onError, statusArea, actionsArea);
    }
}

/**
 * 在客户端生成缩略图
 * @param {Blob} blob - 图片 Blob
 * @param {number} maxSize - 最大尺寸
 * @returns {Promise<string>} - Base64 Data URI
 */
async function generateThumbnailClient(blob, maxSize = 150) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        const url = URL.createObjectURL(blob);
        
        // 设置超时，防止图片加载卡住
        const timeout = setTimeout(() => {
            URL.revokeObjectURL(url);
            reject(new Error('图片加载超时'));
        }, 10000);
        
        img.onload = () => {
            clearTimeout(timeout);
            URL.revokeObjectURL(url);
            
            try {
                // 计算缩放尺寸
                let width = img.width;
                let height = img.height;
                
                if (width > maxSize || height > maxSize) {
                    if (width > height) {
                        height = Math.round(height * maxSize / width);
                        width = maxSize;
                    } else {
                        width = Math.round(width * maxSize / height);
                        height = maxSize;
                    }
                }
                
                // 绘制到 Canvas（不会产生文件，仅内存操作）
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                // 导出为 JPEG Data URL（内存中，无文件残留）
                const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
                
                // 清理 canvas 引用
                canvas.width = 0;
                canvas.height = 0;
                
                resolve(dataUrl);
            } catch (e) {
                reject(e);
            }
        };
        
        img.onerror = () => {
            clearTimeout(timeout);
            URL.revokeObjectURL(url);
            reject(new Error('图片加载失败'));
        };
        
        img.src = url;
    });
}

/**
 * 7z 格式回退到服务器处理
 */
async function preUploadArchiveServer(file, onError, statusArea, actionsArea) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/archive/preview', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success && result.archive_info) {
            archiveImageList = result.archive_info.images || [];
            const imageCount = result.archive_info.image_count || 0;
            const totalFiles = result.archive_info.total_files || 0;
            
            statusArea.innerHTML = `
                <div class="archive-stats">
                    <span class="stat-item">📷 ${imageCount} 张图片</span>
                    <span class="stat-item">📁 ${totalFiles} 个文件</span>
                </div>
            `;
            
            if (imageCount > 0) {
                actionsArea.style.display = 'flex';
                actionsArea.querySelector('.btn-select-preview').addEventListener('click', (e) => {
                    e.stopPropagation();
                    showPreviewSelector(archiveImageList);
                });
            }
        } else {
            statusArea.innerHTML = `<div class="archive-error">⚠️ ${result.message || '解析失败'}</div>`;
            onError(result.message || '压缩包解析失败');
        }
    } catch (error) {
        console.error('服务器解析失败:', error);
        statusArea.innerHTML = `<div class="archive-error">⚠️ 解析失败</div>`;
    }
}

/**
 * 显示大图预览（客户端版本）
 * @param {string} imagePath - 压缩包内的图片路径
 */
async function showFullImage(imagePath) {
    // 获取当前选中的压缩包文件
    const archiveFile = selectedFiles.find(f => {
        const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
        return f.type.includes('zip') || f.type.includes('7z') || 
               ext === '.zip' || ext === '.7z';
    });
    
    if (!archiveFile) return;
    
    const ext = archiveFile.name.substring(archiveFile.name.lastIndexOf('.')).toLowerCase();
    
    // 创建加载提示
    const loadingModal = document.createElement('div');
    loadingModal.className = 'fullimage-modal';
    loadingModal.innerHTML = `
        <div class="fullimage-content">
            <div class="fullimage-loading">
                <div class="spinner"></div>
                <p>加载中...</p>
            </div>
        </div>
    `;
    document.body.appendChild(loadingModal);
    
    try {
        let imageDataUrl;
        
        // ZIP 格式：优先客户端直接解压
        if (ext === '.zip') {
            try {
                const zip = await JSZip.loadAsync(archiveFile);
                const zipFile = zip.file(imagePath);
                
                if (zipFile) {
                    const blob = await zipFile.async('blob');
                    imageDataUrl = await blobToDataUrl(blob);
                } else {
                    throw new Error('文件不存在');
                }
            } catch (clientError) {
                // 客户端解压失败，回退到服务器
                console.warn('客户端提取图片失败，回退到服务器:', clientError.message);
                imageDataUrl = await fetchFullImageFromServer(archiveFile, imagePath);
            }
        } else {
            // 7z 格式：服务器处理
            imageDataUrl = await fetchFullImageFromServer(archiveFile, imagePath);
        }
        
        loadingModal.innerHTML = `
            <div class="fullimage-content">
                <button type="button" class="fullimage-close">×</button>
                <img src="${imageDataUrl}" alt="${getFileName(imagePath)}">
                <div class="fullimage-name">${getFileName(imagePath)}</div>
            </div>
        `;
        
        loadingModal.querySelector('.fullimage-close').addEventListener('click', () => {
            loadingModal.remove();
        });
        
        loadingModal.addEventListener('click', (e) => {
            if (e.target === loadingModal) {
                loadingModal.remove();
            }
        });
        
    } catch (error) {
        console.error('获取大图出错:', error);
        loadingModal.innerHTML = `
            <div class="fullimage-content">
                <button type="button" class="fullimage-close">×</button>
                <div class="fullimage-error">加载失败: ${error.message}</div>
            </div>
        `;
        loadingModal.querySelector('.fullimage-close').addEventListener('click', () => {
            loadingModal.remove();
        });
    }
}

/**
 * Blob 转 DataURL（内存操作，无文件残留）
 */
function blobToDataUrl(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('读取失败'));
        reader.readAsDataURL(blob);
    });
}

/**
 * 从服务器获取压缩包内的完整图片
 * @param {File} archiveFile - 压缩包文件
 * @param {string} imagePath - 压缩包内的图片路径
 * @returns {Promise<string>} - 图片 Data URL
 */
async function fetchFullImageFromServer(archiveFile, imagePath) {
    const formData = new FormData();
    formData.append('file', archiveFile);
    formData.append('path', imagePath);
    
    const response = await fetch('/api/archive/fullimage', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    
    if (result.success && result.image) {
        return result.image;
    } else {
        throw new Error(result.message || '服务器获取图片失败');
    }
}

/**
 * 显示预览图选择器
 * @param {Array} images - 图片对象数组，包含 path, name, thumbnail
 */
function showPreviewSelector(images) {
    // 创建模态框
    const modal = document.createElement('div');
    modal.className = 'preview-selector-modal';
    modal.innerHTML = `
        <div class="preview-selector-content">
            <div class="preview-selector-header">
                <h3>选择预览图片（最多3张）</h3>
                <button type="button" class="preview-selector-close">×</button>
            </div>
            <div class="preview-selector-body">
                <div class="preview-selector-grid">
                    ${images.map((img, idx) => `
                        <div class="preview-selector-item" data-image="${img.path}">
                            <div class="preview-thumb-wrapper">
                                <div class="preview-thumb">
                                    ${img.thumbnail 
                                        ? `<img src="${img.thumbnail}" alt="${img.name}">`
                                        : `<div class="preview-thumb-placeholder">📷</div>`
                                    }
                                </div>
                                <button type="button" class="zoom-btn" data-path="${img.path}" title="放大查看">🔍</button>
                            </div>
                            <label class="preview-label" for="preview-img-${idx}">
                                <input type="checkbox" id="preview-img-${idx}" value="${img.path}">
                                <span class="checkmark"></span>
                                <span class="preview-name">${img.name}</span>
                            </label>
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="preview-selector-footer">
                <span class="selected-count">已选择: 0/3</span>
                <div class="preview-selector-actions">
                    <button type="button" class="btn btn-secondary btn-cancel">取消</button>
                    <button type="button" class="btn btn-primary btn-confirm">确定</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 点击放大按钮查看大图
    modal.querySelectorAll('.zoom-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const path = btn.dataset.path;
            await showFullImage(path);
        });
    });
    
    // 选择计数
    const countEl = modal.querySelector('.selected-count');
    const checkboxes = modal.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            const checked = modal.querySelectorAll('input[type="checkbox"]:checked');
            countEl.textContent = `已选择: ${checked.length}/3`;
            
            // 超过3个时禁用未选中的
            if (checked.length >= 3) {
                checkboxes.forEach(c => {
                    if (!c.checked) c.disabled = true;
                });
            } else {
                checkboxes.forEach(c => c.disabled = false);
            }
        });
    });
    
    // 关闭按钮
    modal.querySelector('.preview-selector-close').addEventListener('click', () => {
        modal.remove();
    });
    
    modal.querySelector('.btn-cancel').addEventListener('click', () => {
        modal.remove();
    });
    
    // 确定按钮
    modal.querySelector('.btn-confirm').addEventListener('click', () => {
        const checked = modal.querySelectorAll('input[type="checkbox"]:checked');
        const selected = Array.from(checked).map(cb => cb.value);
        
        if (selected.length > 0) {
            archivePreviewData = selected;
        } else {
            archivePreviewData = null;  // 不选择则使用自动选择
        }
        
        modal.remove();
    });
    
    // 点击背景关闭
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

/**
 * 从路径中获取文件名
 * @param {string} path 
 * @returns {string}
 */
function getFileName(path) {
    return path.split('/').pop();
}

/**
 * 格式化文件大小
 * @param {number} bytes 
 * @returns {string}
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
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
    
    // 恢复 upload-area
    if (uploadAreaElement && uploadAreaElement.classList.contains('has-archive')) {
        uploadAreaElement.classList.remove('has-archive');
        uploadAreaElement.innerHTML = uploadAreaOriginalHTML;
    }
}
