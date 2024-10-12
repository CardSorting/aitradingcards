// script.js

document.addEventListener('DOMContentLoaded', () => {
    // Data Model
    const cardData = {
        id: null, // Unique identifier for the card from the backend
        name: '',
        type: '',
        abilities: '',
        flavor: '',
        rarity: 'Common',
        powerToughness: '',
        artist: '',
        manaSymbols: [],
        frameColor: '#c0c0c0',
        cardBgColor: '#ffffff',
        headerBgColor: '#f0f0f0',
        footerBgColor: '#000000',
        textColor: '#000000',
        abilitiesTextColor: '#000000',
        flavorTextColor: '#555555',
        aiPrompt: '',
        aiImage: '',
        aiRequestId: null, // To track AI image generation
        darkMode: false
    };

    // Elements
    const toggleDarkModeBtn = document.getElementById('toggle-dark-mode');
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');
    const errorMessage = document.getElementById('error-message');
    const nameInput = document.getElementById('input-card-name');
    const nameLength = document.getElementById('name-length');
    const typeInput = document.getElementById('input-card-type');
    const typeLength = document.getElementById('type-length');
    const abilitiesInput = document.getElementById('input-abilities');
    const abilitiesLength = document.getElementById('abilities-length');
    const flavorInput = document.getElementById('input-flavor');
    const flavorLength = document.getElementById('flavor-length');
    const raritySelect = document.getElementById('input-rarity');
    const powerToughnessInput = document.getElementById('input-power-toughness');
    const artistInput = document.getElementById('input-artist');
    const artistLength = document.getElementById('artist-length');
    const frameColorInput = document.getElementById('input-frame-color');
    const cardBgColorInput = document.getElementById('input-card-bg-color');
    const headerBgColorInput = document.getElementById('input-header-bg-color');
    const footerBgColorInput = document.getElementById('input-footer-bg-color');
    const textColorInput = document.getElementById('input-text-color');
    const abilitiesTextColorInput = document.getElementById('input-abilities-text-color');
    const flavorTextColorInput = document.getElementById('input-flavor-text-color');
    const updateCardBtn = document.getElementById('update-card');
    const resetFormBtn = document.getElementById('reset-form');
    const exportCardBtn = document.getElementById('export-card');
    const dropzone = document.getElementById('dropzone');
    const imageInput = document.getElementById('input-card-image');
    const imagePreview = document.getElementById('image-preview');
    const uploadedImage = imagePreview.querySelector('img');
    const removeImageBtn = document.getElementById('remove-image');

    // AI Image Prompting Elements
    const aiSection = document.getElementById('ai-section');
    const aiPromptInput = document.getElementById('ai-prompt');
    const generateAIImageBtn = document.getElementById('generate-ai-image');
    const aiLoadingSpinner = document.getElementById('ai-loading-spinner');
    const aiImagePreview = document.getElementById('ai-image-preview');
    const aiGeneratedImage = aiImagePreview.querySelector('img');
    const setAIImageBtn = document.getElementById('set-ai-image');

    // Card Preview Elements
    const cardPreview = document.getElementById('card-preview');
    const cardName = document.getElementById('card-name');
    const manaCostDiv = document.getElementById('mana-cost');
    const cardImage = document.getElementById('card-image');
    const cardTypeDiv = document.getElementById('card-type');
    const abilitiesTextDiv = document.getElementById('abilities-text');
    const flavorTextDiv = document.getElementById('flavor-text');
    const artistDetailsSpan = document.getElementById('artist-details');
    const powerToughnessSpan = document.getElementById('power-toughness');
    const cardHeader = document.getElementById('card-header');
    const cardFooter = document.getElementById('card-footer');
    const cardTextDiv = document.getElementById('card-text');

    // Mana Colors and Classes
    const manaColors = {
        'W': '#F8E7B9', // White
        'U': '#A9DCDF', // Blue
        'B': '#BAB1AB', // Black
        'R': '#F9AA8F', // Red
        'G': '#9CD8B0', // Green
        'C': '#D5D5D5'  // Colorless
    };
    const manaTextColors = {
        'W': '#ffffff', // White
        'U': '#ffffff', // Blue
        'B': '#ffffff', // Black
        'R': '#ffffff', // Red
        'G': '#ffffff', // Green
        'C': '#000000'  // Colorless
    };
    const manaClasses = {
        'w': 'bg-yellow-200 text-black',
        'u': 'bg-blue-500 text-white',
        'b': 'bg-black text-white',
        'r': 'bg-red-500 text-white',
        'g': 'bg-green-500 text-white',
        'c': 'bg-gray-400 text-black'
    };

    // Initialize Application
    function init() {
        fetchInitialCard();
        generateManaButtons();
        attachEventListeners();
    }

    // Fetch Initial Card Data from Backend
    async function fetchInitialCard() {
        try {
            // Assuming you have an endpoint to fetch the latest card or a specific card.
            // Modify the URL as per your backend implementation.
            const response = await fetch('/api/cards/latest', { // Example endpoint
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                Object.assign(cardData, data);
                updateUI();
            } else if (response.status === 404) {
                // No existing card found. User can create a new card.
                console.log('No existing card found. Please create a new card.');
            } else {
                const errorData = await response.json();
                displayError(`Error fetching card: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error fetching initial card:', error);
            displayError('Failed to fetch card data from the server.');
        }
    }

    // Save New Card to Backend
    async function createCardOnBackend() {
        try {
            const payload = {
                name: cardData.name,
                mana_cost: cardData.mana_cost,
                card_type: cardData.card_type,
                color: cardData.color,
                rarity: cardData.rarity,
                artist: cardData.artist,
                abilities: cardData.abilities,
                power_toughness: cardData.powerToughness,
                flavor_text: cardData.flavor_text,
                image_url: cardData.image_url // If applicable
            };

            const response = await fetch('/api/cards', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const data = await response.json();
                cardData.id = data.id;
                updateUI();
                alert('Card created successfully!');
            } else {
                const errorData = await response.json();
                displayError(`Error creating card: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error creating card:', error);
            displayError('Failed to create card on the server.');
        }
    }

    // Update Existing Card on Backend
    async function updateCardOnBackend() {
        if (!cardData.id) {
            displayError('Cannot update card. Card ID is missing.');
            return;
        }

        try {
            const payload = {
                name: cardData.name,
                mana_cost: cardData.mana_cost,
                card_type: cardData.card_type,
                color: cardData.color,
                rarity: cardData.rarity,
                artist: cardData.artist,
                abilities: cardData.abilities,
                power_toughness: cardData.power_toughness,
                flavor_text: cardData.flavor_text,
                image_url: cardData.image_url // If applicable
            };

            const response = await fetch(`/api/cards/${cardData.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                alert('Card updated successfully!');
            } else {
                const errorData = await response.json();
                displayError(`Error updating card: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error updating card:', error);
            displayError('Failed to update card on the server.');
        }
    }

    // Update UI based on cardData
    function updateUI() {
        // Update form fields
        nameInput.value = cardData.name;
        typeInput.value = cardData.type;
        abilitiesInput.value = cardData.abilities;
        flavorInput.value = cardData.flavor;
        raritySelect.value = cardData.rarity;
        powerToughnessInput.value = cardData.powerToughness;
        artistInput.value = cardData.artist;
        frameColorInput.value = cardData.frameColor;
        cardBgColorInput.value = cardData.cardBgColor;
        headerBgColorInput.value = cardData.headerBgColor;
        footerBgColorInput.value = cardData.footerBgColor;
        textColorInput.value = cardData.textColor;
        abilitiesTextColorInput.value = cardData.abilitiesTextColor;
        flavorTextColorInput.value = cardData.flavorTextColor;
        aiPromptInput.value = cardData.aiPrompt;

        // Update lengths
        updateLengths();

        // Update dark mode
        if (cardData.darkMode) {
            document.documentElement.classList.add('dark');
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
        } else {
            document.documentElement.classList.remove('dark');
            sunIcon.classList.remove('hidden');
            moonIcon.classList.add('hidden');
        }

        // Update image preview
        if (cardData.image_url) {
            imagePreview.classList.remove('hidden');
            uploadedImage.src = `/uploads/${cardData.image_url}`; // Adjust the path as per your setup
        } else {
            imagePreview.classList.add('hidden');
        }

        // Update AI Image Preview
        if (cardData.ai_image_url) {
            aiImagePreview.classList.remove('hidden');
            aiGeneratedImage.src = `/uploads/${cardData.ai_image_url}`; // Adjust the path as per your setup
        } else {
            aiImagePreview.classList.add('hidden');
        }

        // Update Card Preview
        cardName.textContent = cardData.name || 'Unnamed Card';
        cardTypeDiv.textContent = cardData.type || 'Unknown Type';
        abilitiesTextDiv.textContent = cardData.abilities || 'No abilities';
        flavorTextDiv.textContent = cardData.flavor || 'No flavor text';
        artistDetailsSpan.textContent = cardData.artist ? `Artist: ${cardData.artist}` : 'Artist: Unknown';
        powerToughnessSpan.textContent = cardData.powerToughness ? `P/T: ${cardData.powerToughness}` : 'P/T: N/A';
        frameColorInput.value = cardData.frameColor;
        cardPreview.style.backgroundColor = cardData.cardBgColor;
        cardHeader.style.backgroundColor = cardData.headerBgColor;
        cardFooter.style.backgroundColor = cardData.footerBgColor;
        cardFooter.style.color = cardData.textColor;
        cardTextDiv.style.backgroundColor = cardData.darkMode ? '#4a5568' : '#f7fafc';
        cardTextDiv.style.color = cardData.textColor;

        // Update Mana Cost
        renderManaCost();

        // Update Colors
        cardFrameStyles();
    }

    // Update form field lengths
    function updateLengths() {
        nameLength.textContent = `${cardData.name.length}/30`;
        typeLength.textContent = `${cardData.type.length}/20`;
        abilitiesLength.textContent = `${cardData.abilities.length}/150`;
        flavorLength.textContent = `${cardData.flavor.length}/100`;
        artistLength.textContent = `${cardData.artist.length}/25`;
    }

    // Generate Mana Buttons
    function generateManaButtons() {
        const manaSelector = document.getElementById('mana-selector');
        manaSelector.innerHTML = ''; // Clear existing buttons

        for (const [symbol, color] of Object.entries(manaColors)) {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = `mana-symbol w-8 h-8 rounded-full flex justify-center items-center cursor-pointer transition-transform transform hover:scale-110 focus:outline-none`;
            button.style.backgroundColor = color;
            button.setAttribute('aria-pressed', cardData.manaSymbols.includes(symbol));
            button.setAttribute('aria-label', `${symbol} Mana`);
            button.dataset.symbol = symbol;

            const span = document.createElement('span');
            span.textContent = symbol;
            span.classList.add('font-bold');
            span.style.color = manaTextColors[symbol] || 'white';

            if (cardData.manaSymbols.includes(symbol)) {
                button.classList.add('ring-2', 'ring-indigo-500');
            }

            button.appendChild(span);
            manaSelector.appendChild(button);
        }
    }

    // Render Mana Cost in Card Preview
    function renderManaCost() {
        manaCostDiv.innerHTML = ''; // Clear existing mana symbols

        cardData.manaSymbols.forEach(symbol => {
            const manaDiv = document.createElement('div');
            manaDiv.className = `mana-symbol w-8 h-8 rounded-full flex justify-center items-center text-sm font-bold ${manaClasses[symbol.toLowerCase()]}`;
            manaDiv.style.color = manaTextColors[symbol] || 'white';

            const span = document.createElement('span');
            span.textContent = symbol;
            span.style.color = manaTextColors[symbol] || 'white';

            manaDiv.appendChild(span);
            manaCostDiv.appendChild(manaDiv);
        });
    }

    // Apply Styles Based on Colors
    function cardFrameStyles() {
        const cardFrame = document.querySelector('.card-frame'); // Ensure you have an element with class 'card-frame'
        if (cardFrame) {
            cardFrame.style.borderColor = cardData.frameColor;
            cardFrame.style.backgroundColor = cardData.darkMode ? '#2d2d2d' : cardData.cardBgColor;
        }
    }

    // Attach Event Listeners
    function attachEventListeners() {
        // Dark Mode Toggle
        toggleDarkModeBtn.addEventListener('click', () => {
            cardData.darkMode = !cardData.darkMode;
            updateUI();
        });

        // Form Inputs
        nameInput.addEventListener('input', (e) => {
            cardData.name = e.target.value;
            nameLength.textContent = `${cardData.name.length}/30`;
            updateUI();
        });

        typeInput.addEventListener('input', (e) => {
            cardData.type = e.target.value;
            typeLength.textContent = `${cardData.type.length}/20`;
            updateUI();
        });

        abilitiesInput.addEventListener('input', (e) => {
            cardData.abilities = e.target.value;
            abilitiesLength.textContent = `${cardData.abilities.length}/150`;
            updateUI();
        });

        flavorInput.addEventListener('input', (e) => {
            cardData.flavor = e.target.value;
            flavorLength.textContent = `${cardData.flavor.length}/100`;
            updateUI();
        });

        raritySelect.addEventListener('change', (e) => {
            cardData.rarity = e.target.value;
            updateUI();
        });

        powerToughnessInput.addEventListener('input', (e) => {
            cardData.powerToughness = e.target.value;
            updateUI();
        });

        artistInput.addEventListener('input', (e) => {
            cardData.artist = e.target.value;
            artistLength.textContent = `${cardData.artist.length}/25`;
            updateUI();
        });

        frameColorInput.addEventListener('input', (e) => {
            cardData.frameColor = e.target.value;
            updateUI();
        });

        cardBgColorInput.addEventListener('input', (e) => {
            cardData.cardBgColor = e.target.value;
            updateUI();
        });

        headerBgColorInput.addEventListener('input', (e) => {
            cardData.headerBgColor = e.target.value;
            updateUI();
        });

        footerBgColorInput.addEventListener('input', (e) => {
            cardData.footerBgColor = e.target.value;
            updateUI();
        });

        textColorInput.addEventListener('input', (e) => {
            cardData.textColor = e.target.value;
            updateUI();
        });

        abilitiesTextColorInput.addEventListener('input', (e) => {
            cardData.abilitiesTextColor = e.target.value;
            updateUI();
        });

        flavorTextColorInput.addEventListener('input', (e) => {
            cardData.flavorTextColor = e.target.value;
            updateUI();
        });

        // Mana Selector
        const manaSelector = document.getElementById('mana-selector');
        manaSelector.addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON' || e.target.parentElement.tagName === 'BUTTON') {
                const button = e.target.tagName === 'BUTTON' ? e.target : e.target.parentElement;
                const symbol = button.dataset.symbol;
                toggleMana(symbol);
            }
        });

        // Update Card Button
        updateCardBtn.addEventListener('click', () => {
            if (validateForm()) {
                if (cardData.id) {
                    // Update existing card
                    updateCardOnBackend();
                } else {
                    // Create new card
                    createCardOnBackend();
                }
            }
        });

        // Reset Form Button
        resetFormBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to reset the form? This will clear all current data.')) {
                resetForm();
            }
        });

        // Export Card Button
        exportCardBtn.addEventListener('click', () => {
            exportCardAsImage();
        });

        // Drag-and-Drop Image Upload
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) {
                handleImageUpload(file);
            }
        });

        // Click to upload image
        dropzone.addEventListener('click', () => {
            imageInput.click();
        });

        // Image Input Change
        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                handleImageUpload(file);
            }
        });

        // Remove Image Button
        removeImageBtn.addEventListener('click', () => {
            removeImage();
        });

        // AI Image Prompting
        generateAIImageBtn.addEventListener('click', () => {
            generateAIImage();
        });

        setAIImageBtn.addEventListener('click', () => {
            setAIImageAsCardImage();
        });

        // AI Prompt Input Change
        aiPromptInput.addEventListener('input', () => {
            cardData.aiPrompt = aiPromptInput.value;
            generateAIImageBtn.disabled = !cardData.aiPrompt.trim();
        });
    }

    // Validate Form Fields
    function validateForm() {
        if (!cardData.name.trim() || !cardData.type.trim() || !cardData.abilities.trim() || !cardData.rarity.trim() || !cardData.artist.trim()) {
            displayError('Please fill out all required fields.');
            return false;
        }
        displayError('');
        return true;
    }

    // Display Error Message
    function displayError(message) {
        if (message) {
            errorMessage.textContent = message;
            errorMessage.classList.remove('hidden');
        } else {
            errorMessage.textContent = '';
            errorMessage.classList.add('hidden');
        }
    }

    // Toggle Mana Symbol
    function toggleMana(symbol) {
        if (cardData.manaSymbols.includes(symbol)) {
            cardData.manaSymbols = cardData.manaSymbols.filter(s => s !== symbol);
        } else {
            cardData.manaSymbols.push(symbol);
        }
        updateUI();
    }

    // Handle Image Upload
    async function handleImageUpload(file) {
        // Validate file type (image)
        if (!file.type.startsWith('image/')) {
            displayError('Please upload a valid image file.');
            return;
        }

        // Validate file size (e.g., max 2MB)
        const maxSize = 2 * 1024 * 1024; // 2MB
        if (file.size > maxSize) {
            displayError('Image size should be less than 2MB.');
            return;
        }

        // Validate image dimensions
        const img = new Image();
        img.onload = () => {
            // Example: Ensure width is at least 300px
            if (img.width < 300) {
                displayError('Image width should be at least 300px.');
                return;
            }
            // If valid, proceed to upload
            displayError(''); // Clear any previous errors
            uploadImage(file);
        };
        img.onerror = () => {
            displayError('Failed to load image. Please try another file.');
        };
        img.src = URL.createObjectURL(file);
    }

    // Upload Image to Backend
    async function uploadImage(file) {
        try {
            const formData = new FormData();
            formData.append('image', file);

            const response = await fetch('/api/upload_image', { // Ensure this endpoint exists
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                cardData.image_url = data.filename; // Assuming backend returns the filename
                updateUI();
            } else {
                const errorData = await response.json();
                displayError(`Error uploading image: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error uploading image:', error);
            displayError('Failed to upload image to the server.');
        }
    }

    // Remove Uploaded Image
    async function removeImage() {
        if (!cardData.id || !cardData.image_url) {
            cardData.image_url = '';
            updateUI();
            return;
        }

        try {
            const response = await fetch(`/api/cards/${cardData.id}/remove_image`, { // Ensure this endpoint exists
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                cardData.image_url = '';
                updateUI();
                alert('Image removed successfully.');
            } else {
                const errorData = await response.json();
                displayError(`Error removing image: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error removing image:', error);
            displayError('Failed to remove image from the server.');
        }
    }

    // Reset Form
    function resetForm() {
        cardData.id = null; // Reset card_id as well
        cardData.name = '';
        cardData.type = '';
        cardData.abilities = '';
        cardData.flavor = '';
        cardData.rarity = 'Common';
        cardData.powerToughness = '';
        cardData.artist = '';
        cardData.manaSymbols = [];
        cardData.image_url = '';
        cardData.aiPrompt = '';
        cardData.aiImage = '';
        cardData.aiRequestId = null;
        cardData.darkMode = false;

        // Reset Form Fields
        nameInput.value = '';
        typeInput.value = '';
        abilitiesInput.value = '';
        flavorInput.value = '';
        raritySelect.value = 'Common';
        powerToughnessInput.value = '';
        artistInput.value = '';
        aiPromptInput.value = '';
        generateAIImageBtn.disabled = true;

        updateUI();
    }

    // Generate AI Image
    async function generateAIImage() {
        if (!cardData.aiPrompt.trim()) {
            displayError('Please enter a description for the AI image.');
            return;
        }

        // Ensure the card has been saved and has an ID
        if (!cardData.id) {
            if (!confirm('The card has not been saved yet. Would you like to save it now to generate an AI image?')) {
                return;
            }
            await createCardOnBackend();
            if (!cardData.id) {
                // If creation failed
                return;
            }
        }

        // Show loading spinner
        aiLoadingSpinner.classList.remove('hidden');
        displayError('');

        try {
            const payload = {
                prompt: cardData.aiPrompt,
                card_id: cardData.id
            };

            const response = await fetch('/api/image_gen/generate-image', { // Updated backend endpoint
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const data = await response.json();
                const requestId = data.request_id;
                const imageUrls = data.image_urls;

                if (imageUrls && imageUrls.length > 0) {
                    cardData.aiImage = imageUrls[0];
                    aiGeneratedImage.src = `/uploads/${cardData.aiImage}`; // Adjust the path as per your setup
                    aiImagePreview.classList.remove('hidden');
                    saveAIImageStatus(requestId);
                } else {
                    alert('No image URLs returned.');
                }
            } else {
                const errorData = await response.json();
                displayError(`Error generating image: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error:', error);
            displayError('An error occurred while generating the image.');
        } finally {
            // Hide loading spinner
            aiLoadingSpinner.classList.add('hidden');
            generateAIImageBtn.disabled = !cardData.aiPrompt.trim();
        }
    }

    // Poll AI Image Status
    function saveAIImageStatus(requestId) {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/image_gen/request-status/${requestId}`);
                const data = await response.json();

                if (data.status === 'COMPLETED') {
                    clearInterval(pollInterval);
                    if (data.image_urls && data.image_urls.length > 0) {
                        cardData.aiImage = data.image_urls[0];
                        aiGeneratedImage.src = `/uploads/${cardData.aiImage}`; // Adjust the path as per your setup
                        aiImagePreview.classList.remove('hidden');
                        saveAIImageStatus(null); // Stop polling
                        alert('AI Generated Image has been received.');
                    } else {
                        alert('No image URLs returned.');
                    }
                } else if (data.status === 'FAILED') {
                    clearInterval(pollInterval);
                    alert(`Image generation failed: ${data.error || 'Unknown error.'}`);
                }
                // If status is PENDING or IN_PROGRESS, continue polling
            } catch (error) {
                console.error('Error polling AI image status:', error);
                clearInterval(pollInterval);
                alert('An error occurred while checking the image generation status.');
            }
        }, 3000); // Poll every 3 seconds
    }

    // Set AI Generated Image as Card Image
    async function setAIImageAsCardImage() {
        if (cardData.aiImage) {
            cardData.image_url = cardData.aiImage;
            cardData.aiImage = '';
            cardData.aiPrompt = '';
            cardData.aiRequestId = null;
            aiImagePreview.classList.add('hidden');
            aiPromptInput.value = '';
            generateAIImageBtn.disabled = !cardData.aiPrompt.trim();
            updateUI();

            if (cardData.id) {
                await updateCardOnBackend();
                alert('AI Generated Image has been set as the card image.');
            }
        }
    }

    // Export Card as Image using HTML2Canvas
    async function exportCardAsImage() {
        if (typeof html2canvas === 'undefined') {
            displayError('Export functionality is unavailable because html2canvas failed to load.');
            console.error('html2canvas is not defined');
            return;
        }

        try {
            const card = document.getElementById('card-preview');
            const canvas = await html2canvas(card, { scale: 2 }); // Increased scale for better resolution
            const link = document.createElement('a');
            link.download = `${cardData.name || 'card'}.png`;
            link.href = canvas.toDataURL();
            link.click();
        } catch (err) {
            console.error('Error exporting card:', err);
            alert('Failed to export card. Please try again.');
        }
    }

    // Initialize Application
    init();
});