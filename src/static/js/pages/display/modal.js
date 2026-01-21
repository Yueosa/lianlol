/**
 * 图片模态框模块
 */

let modal = null;
let modalImage = null;

/**
 * 初始化模态框
 * @param {HTMLElement} modalElement 
 * @param {HTMLImageElement} imageElement 
 */
export function initModal(modalElement, imageElement) {
    modal = modalElement;
    modalImage = imageElement;

    // 点击关闭
    modal.addEventListener('click', (e) => {
        if (e.target === modal || e.target.classList.contains('modal-close')) {
            closeModal();
        }
    });

    // ESC 关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('show')) {
            closeModal();
        }
    });
}

/**
 * 打开图片模态框
 * @param {string} url 图片URL
 */
export function openImageModal(url) {
    if (!modal || !modalImage) return;
    
    modalImage.src = url;
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

/**
 * 关闭模态框
 */
export function closeModal() {
    if (!modal) return;
    
    modal.classList.remove('show');
    document.body.style.overflow = '';
}

// 暴露到全局，供 onclick 使用
window.openImageModal = openImageModal;
