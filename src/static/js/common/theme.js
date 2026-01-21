/**
 * 主题切换模块
 * 负责管理明暗主题的切换和持久化
 */

const STORAGE_KEY = 'theme';

/**
 * 获取当前主题
 * @returns {'light'|'dark'}
 */
export function getCurrentTheme() {
    return localStorage.getItem(STORAGE_KEY) || 'light';
}

/**
 * 设置主题
 * @param {'light'|'dark'} theme 
 */
export function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
}

/**
 * 切换主题
 * @returns {'light'|'dark'} 新主题
 */
export function toggleTheme() {
    const currentTheme = getCurrentTheme();
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    return newTheme;
}

/**
 * 初始化主题系统
 * - 绑定切换按钮
 * - 监听系统主题变化
 */
export function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // 监听系统主题变化（如果用户没有手动设置）
    if (window.matchMedia && !localStorage.getItem(STORAGE_KEY)) {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        setTheme(mediaQuery.matches ? 'dark' : 'light');
        
        // 监听变化
        mediaQuery.addEventListener('change', (e) => {
            if (!localStorage.getItem(STORAGE_KEY)) {
                setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
}

// 自动初始化
document.addEventListener('DOMContentLoaded', initTheme);
