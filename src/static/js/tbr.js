document.addEventListener('DOMContentLoaded', function() {
    // Initialize drag and drop
    initializeDragAndDrop();

    // Initialize search
    initializeSearch();

    // Initialize theme toggle
    initializeThemeToggle();

    // Initialize export functionality
    initializeExport();
});

function initializeDragAndDrop() {
    const bookCards = document.querySelectorAll('.book-card');
    const chains = document.querySelectorAll('.chain');

    bookCards.forEach(card => {
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);
    });

    chains.forEach(chain => {
        chain.addEventListener('dragover', handleDragOver);
        chain.addEventListener('drop', handleDrop);
    });
}

function initializeSearch() {
    const searchInput = document.getElementById('searchBar');
    searchInput.addEventListener('input', debounce((e) => {
        const searchTerm = e.target.value.toLowerCase();
        const bookCards = document.querySelectorAll('.book-card');

        bookCards.forEach(card => {
            const title = card.querySelector('h4').textContent.toLowerCase();
            const author = card.querySelector('p').textContent.toLowerCase();

            if (title.includes(searchTerm) || author.includes(searchTerm)) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }, 250));
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function handleDragStart(e) {
    e.target.classList.add('dragging');
    e.dataTransfer.setData('text/plain', e.target.dataset.bookId);
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
}

async function handleDrop(e) {
    e.preventDefault();
    const bookId = e.dataTransfer.getData('text/plain');
    const targetChain = e.target.closest('.chain');
    const bookCard = document.querySelector(`[data-book-id="${bookId}"]`);

    if (targetChain && bookCard) {
        try {
            const response = await fetch('/api/reorder_chain', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    bookId: bookId,
                    targetChainId: targetChain.dataset.chainId
                })
            });

            if (response.ok) {
                targetChain.querySelector('.book-list').appendChild(bookCard);
            } else {
                throw new Error('Failed to update chain');
            }
        } catch (error) {
            console.error('Error updating chain:', error);
            // Revert the change
            bookCard.parentElement.appendChild(bookCard);
        }
    }
}

function initializeThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
    });
}

function initializeExport() {
    const exportBtn = document.getElementById('exportBtn');
    exportBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/export_reading_list');
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'reading_list.xlsx';
                a.click();
                window.URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error('Error exporting reading list:', error);
        }
    });
}