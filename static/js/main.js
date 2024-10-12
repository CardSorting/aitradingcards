class CardManager {
    constructor() {
        this.cardGrid = document.getElementById('card-grid');
        this.generateCardButton = document.getElementById('generate-card');
        this.openPackButton = document.getElementById('open-pack');
        this.page = 1;
        this.cardsPerPage = 20;
        this.isLoading = false;
        this.loadingSpinner = this.createLoadingSpinner();

        this.verifyElements();
        this.initEvents();
        this.loadInitialCards();
    }

    // Verify all required elements exist
    verifyElements() {
        if (!this.cardGrid) throw new Error('Element with ID "card-grid" not found.');
        if (!this.generateCardButton) throw new Error('Element with ID "generate-card" not found.');
        if (!this.openPackButton) throw new Error('Element with ID "open-pack" not found.');
    }

    // Initialize all core events
    initEvents() {
        this.generateCardButton.addEventListener('click', () => this.handleGenerateCard());
        this.openPackButton.addEventListener('click', () => this.handleOpenPack());
        window.addEventListener('scroll', this.debounce(() => this.handleInfiniteScroll(), 200));
    }

    // Load initial set of cards
    async loadInitialCards() {
        this.loadCards();
    }

    // Creates the loading spinner element
    createLoadingSpinner() {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner hidden fixed inset-0 flex items-center justify-center z-50';
        spinner.innerHTML = '<div class="spinner border-t-4 border-blue-600 rounded-full w-16 h-16 animate-spin"></div>'; // Added Tailwind's animate-spin
        document.body.appendChild(spinner);
        return spinner;
    }

    // Handles generating a new card
    async handleGenerateCard() {
        this.toggleLoading(true);
        try {
            const newCard = await this.fetchCardFromAPI();
            this.cardGrid.prepend(this.createCardElement(newCard));
        } catch (error) {
            console.error('Error generating card:', error);
            alert(`Error generating card: ${error.message}`);
        } finally {
            this.toggleLoading(false);
        }
    }

    // Handles opening a new card pack
    async handleOpenPack() {
        this.toggleLoading(true);
        this.cardGrid.innerHTML = '';
        try {
            const packCards = await this.fetchPackFromAPI();
            packCards.forEach(card => this.cardGrid.appendChild(this.createCardElement(card)));
        } catch (error) {
            console.error('Error opening pack:', error);
            alert(`Error opening pack: ${error.message}`);
        } finally {
            this.toggleLoading(false);
        }
    }

    // Fetches a card from the API
    async fetchCardFromAPI() {
        const response = await fetch('/api/generate_card', { method: 'POST' });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch card from API');
        }
        return await response.json();
    }

    // Fetches a pack of cards from the API
    async fetchPackFromAPI() {
        const response = await fetch('/api/open_pack', { method: 'POST' });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch pack from API');
        }
        return await response.json();
    }

    // Load cards via API
    async loadCards(append = false) {
        if (this.isLoading) return;
        this.isLoading = true;
        this.toggleLoading(true);

        try {
            const cards = await this.fetchCardsFromAPI();
            if (!append) this.cardGrid.innerHTML = '';
            cards.forEach(card => this.cardGrid.appendChild(this.createCardElement(card)));
            this.page++;
        } catch (error) {
            console.error('Error loading cards:', error);
            alert(`Error loading cards: ${error.message}`);
        } finally {
            this.isLoading = false;
            this.toggleLoading(false);
        }
    }

    // Fetch cards from API with pagination
    async fetchCardsFromAPI() {
        const response = await fetch(`/api/cards?page=${this.page}&per_page=${this.cardsPerPage}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch cards');
        }
        const data = await response.json();
        return data.cards;
    }

    // Toggle the loading spinner visibility
    toggleLoading(isVisible) {
        this.loadingSpinner.classList.toggle('hidden', !isVisible);
    }

    // Utility: Debounce to limit function calls
    debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    createManaSymbols(manaCost) {
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

    determineCardColor(manaCost) {
        const colors = {
            'W': '#F8E7B9',
            'U': '#0E68AB',
            'B': '#150B00',
            'R': '#D3202A',
            'G': '#00733E'
        };
        const manaSymbols = manaCost.match(/\{([^}]+)\}/g) || [];
        for (const symbol of manaSymbols) {
            const color = colors[symbol.replace(/\{|\}/g, '')];
            if (color) return color;
        }
        return '#A9A9A9'; // Default gray
    }

    createCardElement(card) {
        console.log('Card Image Base URL:', cardImageBaseUrl); // Debugging
        console.log('Card Image URL:', card.image_url); // Debugging

        const cardElement = document.createElement('div');
        const cardColor = this.determineCardColor(card.mana_cost);
        cardElement.className = 'mtg-card w-[250px] h-[350px] relative text-black rounded-[12px] shadow-lg overflow-hidden transition-transform duration-300 hover:scale-105';
        cardElement.style.background = `linear-gradient(165deg, ${cardColor} 60%, #171314)`;

        cardElement.innerHTML = `
            <div class="card-frame h-full p-2 flex flex-col">
                <div class="card-header flex justify-between items-center bg-gradient-to-r from-gray-200 to-gray-100 p-1 rounded-t-md mb-1">
                    <h2 class="card-name text-sm font-bold text-shadow">${card.name}</h2>
                    <div class="mana-cost flex text-xs">${this.createManaSymbols(card.mana_cost)}</div>
                </div>
                <img src="${cardImageBaseUrl}${card.image_url || 'placeholder.png'}" alt="${card.name}" loading="lazy" class="w-full h-[140px] object-cover object-center rounded mb-1">
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
            new MTGCard3DTiltEffect(cardElement);
        }

        return cardElement;
    }

    async handleInfiniteScroll() {
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500 && !this.isLoading) {
            this.loadCards(true);
        }
    }
}

// Initialize CardManager when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        new CardManager();
    } catch (error) {
        console.error(error.message); // Improved error logging
    }
});