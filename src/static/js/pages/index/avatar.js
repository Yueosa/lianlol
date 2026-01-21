/**
 * Emoji 头像选择器模块
 */

/**
 * 初始化头像选择器
 * @param {HTMLElement} trigger 触发按钮
 * @param {HTMLElement} dropdown 下拉面板
 * @param {HTMLElement} grid emoji网格
 * @param {HTMLInputElement} input 隐藏输入框
 */
export function initAvatarPicker(trigger, dropdown, grid, input) {
    // 点击触发器显示/隐藏下拉框
    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');
    });

    // 点击其他地方关闭
    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && e.target !== trigger) {
            dropdown.classList.remove('show');
        }
    });

    // Emoji 选择
    grid.addEventListener('click', (e) => {
        if (e.target.classList.contains('emoji-btn')) {
            const emoji = e.target.dataset.emoji;
            selectEmoji(emoji, trigger, input, grid);
            dropdown.classList.remove('show');
        }
    });

    // 初始化选中默认 emoji
    const defaultEmoji = input.value || '🥰';
    const defaultBtn = grid.querySelector(`[data-emoji="${defaultEmoji}"]`);
    if (defaultBtn) {
        defaultBtn.classList.add('selected');
    }
}

/**
 * 选中一个 emoji
 */
function selectEmoji(emoji, trigger, input, grid) {
    input.value = emoji;
    trigger.textContent = emoji;
    
    // 更新选中状态
    grid.querySelectorAll('.emoji-btn').forEach(btn => {
        btn.classList.toggle('selected', btn.dataset.emoji === emoji);
    });
}

/**
 * 重置为默认头像
 */
export function resetAvatar(trigger, input, grid, defaultEmoji = '🥰') {
    selectEmoji(defaultEmoji, trigger, input, grid);
}
