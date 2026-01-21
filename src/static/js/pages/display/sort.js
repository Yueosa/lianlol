/**
 * 排序模块
 */

let currentSort = 'desc';
let currentSortBy = 'id';

/**
 * 获取当前排序状态
 * @returns {{sort: string, sortBy: string}}
 */
export function getSortState() {
    return { sort: currentSort, sortBy: currentSortBy };
}

/**
 * 初始化排序控件
 * @param {Object} buttons 排序按钮集合
 * @param {Function} onSort 排序变化回调
 */
export function initSort(buttons, onSort) {
    const { sortDescBtn, sortAscBtn, sortLoveBtn } = buttons;

    sortDescBtn.addEventListener('click', () => {
        if (currentSort !== 'desc' || currentSortBy !== 'id') {
            currentSort = 'desc';
            currentSortBy = 'id';
            updateSortButtons(buttons);
            onSort();
        }
    });

    sortAscBtn.addEventListener('click', () => {
        if (currentSort !== 'asc' || currentSortBy !== 'id') {
            currentSort = 'asc';
            currentSortBy = 'id';
            updateSortButtons(buttons);
            onSort();
        }
    });

    sortLoveBtn.addEventListener('click', () => {
        if (currentSortBy !== 'love') {
            currentSort = 'desc';
            currentSortBy = 'love';
            updateSortButtons(buttons);
            onSort();
        }
    });
}

/**
 * 更新排序按钮状态
 */
function updateSortButtons(buttons) {
    const { sortDescBtn, sortAscBtn, sortLoveBtn } = buttons;
    
    sortDescBtn.classList.remove('active');
    sortAscBtn.classList.remove('active');
    sortLoveBtn.classList.remove('active');
    
    if (currentSortBy === 'love') {
        sortLoveBtn.classList.add('active');
    } else if (currentSort === 'desc') {
        sortDescBtn.classList.add('active');
    } else {
        sortAscBtn.classList.add('active');
    }
}
