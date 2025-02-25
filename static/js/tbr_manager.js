// Constants
const ANIMATION_DURATION = 200; // ms
const DEBOUNCE_DELAY = 250; // ms

// State management
let isDragging = false;
let originalChainState = null;

// Utility Functions
const debounce = (fn, delay) => {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), delay);
    };
};

// DOM Elements
const bookCards = document.querySelectorAll('.book-card');
const readingChains = document.querySelectorAll('.reading-chain');
const searchInput = document.querySelector('#book-search');
const filterButtons = document.querySelectorAll('.filter-btn');
const sortSelect = document.querySelector('.sort-select');
const exportButton = document.querySelector('.export-btn');
const loadingOverlay = document.querySelector('.loading-overlay');

// Add initialization check
document.addEventListener('DOMContentLoaded', () => {
    console.log('TBR Manager initializing...');

    // Check if required elements exist
    const requiredElements = {
        bookCards: document.querySelectorAll('.book-card'),
        readingChains: document.querySelectorAll('.reading-chain'),
        searchInput: document.querySelector('#book-search'),
        loadingOverlay: document.querySelector('.loading-overlay')
    };

    // Log initialization status
    Object.entries(requiredElements).forEach(([name, element]) => {
        console.log(`${name} found:`, element ? 'Yes' : 'No');
    });

    // Initialize only if elements exist
    if (requiredElements.readingChains.length > 0) {
        initializeDragAndDrop();
        initializeSearch();
        // Initial chain refresh
        refreshChainDisplay().catch(error => {
            console.error('Failed to refresh chains:', error);
            showError('Failed to load reading chains');
        });
    } else {
        console.error('Required elements not found. Check HTML structure.');
    }
});

// Drag and Drop Event Handlers
function handleDragStart(e) {
    try {
        isDragging = true;
        originalChainState = captureChainState();

        const bookCard = e.currentTarget;
        const readingId = bookCard.dataset.readingId;

        console.log('Drag start - Card:', bookCard);
        console.log('Reading ID:', readingId);

        if (!readingId) {
            console.error('No reading ID found on book card');
            e.preventDefault();
            return;
        }

        e.dataTransfer.setData('text/plain', readingId);
        bookCard.classList.add('dragging');

        // For debugging
        console.log('Drag data set:', e.dataTransfer.getData('text/plain'));
    } catch (error) {
        console.error('Drag start error:', error);
        e.preventDefault();
    }
}

function handleDragEnd(e) {
    isDragging = false;
    e.target.classList.remove('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('drop-target');
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('drop-target');
}

async function handleDrop(e) {
    e.preventDefault();
    const chain = e.currentTarget;
    chain.classList.remove('drop-target');

    try {
        const readingId = e.dataTransfer.getData('text/plain');
        console.log('Drop - Retrieved reading ID:', readingId);

        const targetCard = e.target.closest('.book-card');
        const chainType = chain.dataset.chainType;  // Get the chain type (kindle, hardcover, audio)

        showLoading();

        const response = await fetch('/tbr/api/reorder_chain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                reading_id: readingId,
                chain_type: chainType,
                target_id: targetCard ? targetCard.dataset.readingId : null
            }),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        // If successful, refresh the chain display
        await refreshChainDisplay();
        console.log('Chain update completed successfully');
    } catch (error) {
        console.error('Drop error:', error);
        revertDragOperation();
        showError('Failed to update reading chain: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Initialize drag and drop functionality
function initializeDragAndDrop() {
    console.log('Initializing drag and drop');

    const readingChains = document.querySelectorAll('.reading-chain');
    console.log(`Found ${readingChains.length} chains`);

    readingChains.forEach(chain => {
        // Remove existing listeners to prevent duplicates
        chain.removeEventListener('dragover', handleDragOver);
        chain.removeEventListener('dragleave', handleDragLeave);
        chain.removeEventListener('drop', handleDrop);

        // Add new listeners
        chain.addEventListener('dragover', handleDragOver);
        chain.addEventListener('dragleave', handleDragLeave);
        chain.addEventListener('drop', handleDrop);

        console.log('Initialized chain:', chain.dataset.chainType);

        // Initialize books in this chain
        initializeDragAndDropForContainer(chain);
    });
}

function initializeSearch() {
    const searchInput = document.querySelector('#book-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce((e) => {
            try {
                const searchTerm = e.target.value.toLowerCase();
                filterBooks(searchTerm);
            } catch (error) {
                console.error('Search error:', error);
            }
        }, DEBOUNCE_DELAY));
    }
}

// Helper Functions
function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.book-card:not(.dragging)')];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;

        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function getTargetReadingId(element) {
    const card = element.closest('.book-card');
    return card ? card.dataset.readingId : null;
}

function captureChainState() {
    return Array.from(readingChains).map(chain => ({
        id: chain.dataset.chainType,
        books: Array.from(chain.querySelectorAll('.book-card')).map(card => card.dataset.readingId)
    }));
}

// Add this function to get CSRF token
function getCSRFToken() {
    // First try to get the token from the meta tag
    const tokenMeta = document.querySelector('meta[name="csrf-token"]');
    if (tokenMeta && tokenMeta.content) {
        console.log('Found CSRF token in meta tag');
        return tokenMeta.content;
    }

    // Fallback to getting it from the cookie
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrf_token') {
            console.log('Found CSRF token in cookie');
            return value;
        }
    }

    console.error('CSRF token not found in meta tag or cookie');
    return null;
}

// API Interactions
async function updateReadingChain(readingId, targetId) {
    try {
        const response = await fetch('/tbr/api/reorder_chain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                reading_id: readingId,
                target_id: targetId
            }),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Chain update failed:', error);
        throw error;
    }
}

async function refreshChainDisplay() {
    console.log('Starting chain refresh');
    showLoading();

    try {
        const response = await fetch('/tbr/api/chains', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        if (!data.chains) {
            throw new Error('No chains data received');
        }

        updateChainsDisplay(data.chains);
    } catch (error) {
        console.error('Error refreshing chains:', error);
        showError('Failed to refresh reading chains');
    } finally {
        hideLoading();
    }
}

// UI Updates
function updateChainsDisplay(chains) {
    console.log('Updating chains display with:', chains);

    chains.forEach(chain => {
        const chainType = chain.media.toLowerCase();
        const chainElement = document.querySelector(`.reading-chain[data-chain-type="${chainType}"]`);

        if (!chainElement) {
            console.error(`Chain element not found for type: ${chainType}`);
            return;
        }

        let bookList = chainElement.querySelector('.book-list');

        if (!bookList) {
            bookList = document.createElement('div');
            bookList.className = 'book-list';
            chainElement.appendChild(bookList);
        }

        // Clear existing content
        bookList.innerHTML = '';

        if (chain.books && chain.books.length > 0) {
            chain.books.forEach(book => {
                const bookCard = document.createElement('div');
                bookCard.innerHTML = createBookCard(book);
                const cardElement = bookCard.firstElementChild;
                bookList.appendChild(cardElement);

                // Initialize drag and drop for this card
                cardElement.setAttribute('draggable', true);
                cardElement.addEventListener('dragstart', handleDragStart);
                cardElement.addEventListener('dragend', handleDragEnd);
            });
        } else {
            bookList.innerHTML = '<p class="no-books">No books in this chain</p>';
        }
    });

    console.log('Chains display update completed');
}

function createBookCard(book) {
    console.log('Creating book card for:', book);

    if (!book || !book.title || !book.id) {
        console.error('Invalid book data:', book);
        return '';
    }

    return `
        <div class="book-card ${book.current ? 'current' : ''}"
             data-reading-id="${book.id}"
             draggable="true">
            <div class="book-header">
                <h3>${book.title}</h3>
                <p class="author">${book.author || 'Unknown Author'}</p>
                ${book.current ? '<span class="current-badge">Current</span>' : ''}
            </div>
            <div class="book-details">
                <div class="detail">
                    <span class="label">Progress:</span>
                    <span class="value">${book.progress || 0}%</span>
                </div>
                <div class="detail">
                    <span class="label">Started:</span>
                    <span class="value">${book.date_started ? new Date(book.date_started).toLocaleDateString() : 'Not started'}</span>
                </div>
            </div>
        </div>
    `;
}

// Loading State Management
function showLoading() {
    console.log('Showing loading overlay');
    const loadingOverlay = document.querySelector('.loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.hidden = false;
        console.log('Loading overlay visible');
    } else {
        console.error('Loading overlay element not found');
    }
}

function hideLoading() {
    console.log('Hiding loading overlay');
    const loadingOverlay = document.querySelector('.loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.hidden = true;
        console.log('Loading overlay hidden');
    } else {
        console.error('Loading overlay element not found');
    }
}

// Search and Filter Implementation
searchInput.addEventListener('input', debounce((e) => {
    const searchTerm = e.target.value.toLowerCase();
    filterBooks(searchTerm);
}, DEBOUNCE_DELAY));

function filterBooks(searchTerm) {
    bookCards.forEach(card => {
        const title = card.querySelector('h3').textContent.toLowerCase();
        const author = card.querySelector('p').textContent.toLowerCase();
        const isVisible = title.includes(searchTerm) || author.includes(searchTerm);
        card.style.display = isVisible ? 'block' : 'none';
    });
}

// Error Handling
function revertDragOperation() {
    if (originalChainState) {
        originalChainState.forEach(chainState => {
            const chain = document.querySelector(`.reading-chain[data-chain-type="${chainState.id}"]`);
            chainState.books.forEach(bookId => {
                const book = document.querySelector(`.book-card[data-reading-id="${bookId}"]`);
                if (book && chain) {
                    chain.appendChild(book);
                }
            });
        });
    }
}

// Add error display
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = 'background: #fee; color: #c00; padding: 10px; margin: 10px; border-radius: 4px;';
    errorDiv.textContent = message;
    document.querySelector('.reading-chains').prepend(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}

// Export functionality
exportButton.addEventListener('click', async () => {
    showLoading();
    try {
        const response = await fetch('/api/export_reading_list');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'reading_list.xlsx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Export failed:', error);
    } finally {
        hideLoading();
    }
});

// Initialize tooltips if using a tooltip library
if (typeof tippy !== 'undefined') {
    tippy('[data-tippy-content]');
}

// Add new function to initialize drag and drop for a specific container
function initializeDragAndDropForContainer(container) {
    const bookCards = container.querySelectorAll('.book-card');

    bookCards.forEach(card => {
        card.setAttribute('draggable', true);

        // Remove existing listeners to prevent duplicates
        card.removeEventListener('dragstart', handleDragStart);
        card.removeEventListener('dragend', handleDragEnd);

        // Add new listeners
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);

        console.log('Initialized drag and drop for card:', card.querySelector('h3').textContent);
    });
}
