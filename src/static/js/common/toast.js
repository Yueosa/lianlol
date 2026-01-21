/**
 * Toast 提示模块
 * 用于显示临时消息通知
 */

/**
 * 显示 Toast 提示
 * @param {string} message 消息内容
 * @param {number} duration 持续时间（毫秒）
 */
export function showToast(message, duration = 2000) {
    // 移除已有的 toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // 显示动画
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });
    
    // 自动隐藏
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * 显示成功提示
 * @param {string} message 
 */
export function showSuccess(message) {
    showToast(`✅ ${message}`);
}

/**
 * 显示错误提示
 * @param {string} message 
 */
export function showError(message) {
    showToast(`❌ ${message}`, 3000);
}

/**
 * 显示信息提示
 * @param {string} message 
 */
export function showInfo(message) {
    showToast(`ℹ️ ${message}`);
}
