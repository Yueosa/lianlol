// 主题切换逻辑

(function() {
    const themeToggle = document.getElementById('themeToggle');
    
    if (!themeToggle) return;
    
    // 获取当前主题
    function getCurrentTheme() {
        return localStorage.getItem('theme') || 'light';
    }
    
    // 设置主题
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }
    
    // 切换主题
    function toggleTheme() {
        const currentTheme = getCurrentTheme();
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
    }
    
    // 绑定点击事件
    themeToggle.addEventListener('click', toggleTheme);
    
    // 监听系统主题变化（可选）
    if (window.matchMedia) {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        // 如果用户没有手动设置过主题，则跟随系统
        if (!localStorage.getItem('theme')) {
            setTheme(mediaQuery.matches ? 'dark' : 'light');
        }
    }
})();
