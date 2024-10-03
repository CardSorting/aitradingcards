document.addEventListener('DOMContentLoaded', () => {
    const cardGrid = document.getElementById('card-grid');
    const generateCardButton = document.getElementById('generate-card');
    const openPackButton = document.getElementById('open-pack');
    const loadingSpinner = createLoadingSpinner();

    let page = 1;
    const cardsPerPage = 20;
    let isLoading = false;

    // Initialize all core events
    initGenerateCardEvent();
    initOpenPackEvent();
    initInfiniteScroll();

    // Load initial set of cards
    loadCards();

    // Creates the loading spinner element
    function createLoadingSpinner() {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner hidden fixed inset-0 flex items-center justify-center z-50';
        spinner.innerHTML = '<div class="spinner border-t-4 border-blue-600 rounded-full w-16 h-16"></div>';
        document.body.appendChild(spinner);
        return spinner;
    }

    // Determines card color based on mana cost
    function determineCardColor(manaCost) {
        const colors = {
            'W': '#F8E7B9',  // White
            'U': '#0E68AB',  // Blue
            'B': '#150B00',  // Black
            'R': '#D3202A',  // Red
            'G': '#00733E'   // Green
        };
        return manaCost.split('').find(char => colors[char]) || '#A9A9A9'; // Default gray
    }

    // Creates mana symbols based on mana cost string
    function createManaSymbols(manaCost) {
        if (!manaCost) return '';
        const symbolMap = {
            'w': 'rgb(248, 231, 185)',
            'u': 'rgb(14, 104, 171)',
            'b': 'rgb(21, 11, 0)',
            'r': 'rgb(211, 32, 42)',
            'g': 'rgb(0, 115, 62)',
            'default': 'rgb(155, 155, 155)'
        };
        return manaCost.replace(/\{([^}]+)\}/g, (_, symbol) => {
            const bgColor = symbolMap[symbol.toLowerCase()] || symbolMap['default'];
            const textColor = ['w', 'default'].includes(symbol.toLowerCase()) ? 'black' : 'white';
            return `<div class="mana-symbol rounded-full flex justify-center items-center text-sm font-bold ml-0.5" style="background-color: ${bgColor}; color: ${textColor};">${symbol}</div>`;
        });
    }

    // Creates a card element dynamically based on card data
    function createCardElement(card) {
        const cardElement = document.createElement('div');
        const cardColor = determineCardColor(card.mana_cost);
        cardElement.className = 'mtg-card w-[250px] h-[350px] relative text-black rounded-[12px] shadow-lg overflow-hidden transition-transform duration-300 hover:scale-105';
        cardElement.style.background = `linear-gradient(165deg, ${cardColor} 60%, #171314)`;

        cardElement.innerHTML = `
            <div class="card-frame h-full p-2 flex flex-col">
                <div class="card-header flex justify-between items-center bg-gradient-to-r from-gray-200 to-gray-100 p-1 rounded-t-md mb-1">
                    <h2 class="card-name text-sm font-bold text-shadow">${card.name}</h2>
                    <div class="mana-cost flex text-xs">${createManaSymbols(card.mana_cost)}</div>
                </div>
                <img src="${card.image_url}" alt="${card.name}" loading="lazy" class="w-full h-[140px] object-cover object-center rounded mb-1">
                <div class="card-type bg-gradient-to-r from-gray-200 to-gray-100 p-1 text-xs border-b border-black border-opacity-20 mb-1">${card.card_type}</div>
                <div class="card-text bg-gray-100 bg-opacity-90 p-2 rounded flex-grow overflow-y-auto text-xs leading-tight">
                    <p>${card.abilities}</p>
                    <p class="mt-1 italic">${card.flavor_text}</p>
                </div>
                <div class="card-footer flex justify-between text-white text-xs mt-1">
                    <span>${card.rarity} (${card.set_name}-${card.card_number})</span>
                    <span>${card.power_toughness || ''}</span>
                </div>
            </div>
        `;

        cardElement.addEventListener('click', () => window.location.href = `/card/${card.id}`);

        if (card.rarity === 'Rare' || card.rarity === 'Mythic Rare') {
            new MTGCard3DTiltEffect(cardElement);  // Adding 3D tilt effect for rare cards
        }

        return cardElement;
    }

    // Loads cards via API and appends/prepends them to the card grid
    async function loadCards(append = false) {
        if (isLoading) return;
        isLoading = true;
        loadingSpinner.classList.remove('hidden');

        try {
            const response = await fetch(`/api/cards?page=${page}&per_page=${cardsPerPage}`);
            const data = await response.json();

            if (!append) cardGrid.innerHTML = '';  // Clear if not appending

            if (Array.isArray(data.cards)) {
                data.cards.forEach(card => cardGrid.appendChild(createCardElement(card)));
                page++;  // Increment page for infinite scroll
            } else {
                console.error('Received data is not in the expected format:', data);
            }
        } catch (error) {
            console.error('Error loading cards:', error);
        } finally {
            isLoading = false;
            loadingSpinner.classList.add('hidden');
        }
    }

    // Initialize event for generating a single card
    function initGenerateCardEvent() {
        generateCardButton.addEventListener('click', async () => {
            loadingSpinner.classList.remove('hidden');

            try {
                const response = await fetch('/api/generate_card', { method: 'POST' });
                const newCard = await response.json();
                cardGrid.prepend(createCardElement(newCard));  // Prepend new card at the top
            } catch (error) {
                console.error('Error generating card:', error);
            } finally {
                loadingSpinner.classList.add('hidden');
            }
        });
    }

    // Initialize event for opening a pack of cards
    function initOpenPackEvent() {
        openPackButton.addEventListener('click', async () => {
            loadingSpinner.classList.remove('hidden');
            cardGrid.innerHTML = '';  // Clear card grid for new pack

            try {
                const response = await fetch('/api/open_pack', { method: 'POST' });
                const data = await response.json();

                if (Array.isArray(data)) {
                    data.forEach(card => cardGrid.appendChild(createCardElement(card)));
                } else {
                    throw new Error('Received data is not in the expected format');
                }
            } catch (error) {
                console.error('Error opening pack:', error);
                alert(`An error occurred while opening the pack: ${error.message}`);
            } finally {
                loadingSpinner.classList.add('hidden');
            }
        });
    }

    // Initialize infinite scroll for loading more cards on scroll
    function initInfiniteScroll() {
        const debounce = (func, wait) => {
            let timeout;
            return (...args) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            };
        };

        window.addEventListener('scroll', debounce(() => {
            if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500 && !isLoading) {
                loadCards(true);  // Load next page when reaching bottom
            }
        }, 200));  // 200ms debounce for scroll event
    }
});