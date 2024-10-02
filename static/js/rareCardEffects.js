class MTGCard3DTiltEffect {
    constructor(cardElement) {
        this.card = cardElement;
        if (!this.card) throw new Error('No card element provided');

        this.shine = this.createShineElement();
        this.rainbowShine = this.createRainbowShineElement();

        this.settings = {
            tiltEffectMaxRotation: 15,
            tiltEffectPerspective: 800,
            tiltEffectScale: 1.05,
            shineMovementRange: 100,
            rainbowShineMovementRange: 50
        };

        this.setupEventListeners();
        this.injectStyles();
    }

    createShineElement() {
        return this.createAndAppendElement('shine-effect');
    }

    createRainbowShineElement() {
        const container = this.createAndAppendElement('rainbow-shine-container');
        const effect = this.createAndAppendElement('rainbow-shine-effect');
        container.appendChild(effect);
        return effect;
    }

    createAndAppendElement(className) {
        const element = document.createElement('div');
        element.classList.add(className);
        this.card.appendChild(element);
        return element;
    }

    setupEventListeners() {
        this.card.addEventListener('mouseenter', () => this.setTransition(false));
        this.card.addEventListener('mousemove', (e) => this.handleTilt(e));
        this.card.addEventListener('mouseleave', () => this.resetTilt());
    }

    setTransition(active) {
        const transition = active ? 'all 0.5s ease-out' : 'none';
        this.card.style.transition = transition;
        this.shine.style.transition = transition;
        this.rainbowShine.style.transition = transition;
    }

    handleTilt(e) {
        const { left, top, width, height } = this.card.getBoundingClientRect();
        const angleX = (e.clientX - (left + width / 2)) / (width / 2);
        const angleY = (e.clientY - (top + height / 2)) / (height / 2);

        const rotateX = angleY * this.settings.tiltEffectMaxRotation;
        const rotateY = -angleX * this.settings.tiltEffectMaxRotation;

        this.card.style.transform = `
            perspective(${this.settings.tiltEffectPerspective}px)
            rotateX(${rotateX}deg)
            rotateY(${rotateY}deg)
            scale3d(${this.settings.tiltEffectScale}, ${this.settings.tiltEffectScale}, ${this.settings.tiltEffectScale})
        `;

        this.updateShineEffect(this.shine, angleX, angleY, this.settings.shineMovementRange);
        this.updateShineEffect(this.rainbowShine, angleX, angleY, this.settings.rainbowShineMovementRange);
    }

    updateShineEffect(element, angleX, angleY, range) {
        const x = -angleX * range;
        const y = -angleY * range;
        element.style.transform = `translate(${x}%, ${y}%)`;
        element.style.opacity = '1';
    }

    resetTilt() {
        this.setTransition(true);
        this.card.style.transform = `
            perspective(${this.settings.tiltEffectPerspective}px)
            rotateX(0deg)
            rotateY(0deg)
            scale3d(1, 1, 1)
        `;
        this.resetShineEffect(this.shine);
        this.resetShineEffect(this.rainbowShine);
    }

    resetShineEffect(element) {
        element.style.transform = 'translate(0%, 0%)';
        element.style.opacity = '0';
    }

    injectStyles() {
        if (!document.getElementById('mtg-card-3d-tilt-effect-styles')) {
            const style = document.createElement('style');
            style.id = 'mtg-card-3d-tilt-effect-styles';
            style.textContent = `
                .mtg-card {
                    transition: transform 0.1s ease-out;
                    transform-style: preserve-3d;
                    will-change: transform;
                    position: relative;
                    overflow: hidden;
                }
                .shine-effect {
                    position: absolute;
                    top: -50%;
                    left: -50%;
                    right: -50%;
                    bottom: -50%;
                    background: radial-gradient(
                        circle at 50% 50%,
                        rgba(255, 255, 255, 0.8) 0%,
                        rgba(255, 255, 255, 0.5) 25%,
                        rgba(255, 255, 255, 0.3) 50%,
                        rgba(255, 255, 255, 0.1) 75%,
                        rgba(255, 255, 255, 0) 100%
                    );
                    pointer-events: none;
                    opacity: 0;
                    transition: opacity 0.5s ease-out, transform 0.5s ease-out;
                    mix-blend-mode: soft-light;
                }
                .rainbow-shine-container {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    overflow: hidden;
                    pointer-events: none;
                }
                .rainbow-shine-effect {
                    position: absolute;
                    top: -50%;
                    left: -50%;
                    right: -50%;
                    bottom: -50%;
                    background: radial-gradient(
                        circle at 50% 50%,
                        rgba(255, 0, 0, 0.3),
                        rgba(255, 165, 0, 0.3),
                        rgba(255, 255, 0, 0.3),
                        rgba(0, 255, 0, 0.3),
                        rgba(0, 0, 255, 0.3),
                        rgba(75, 0, 130, 0.3),
                        rgba(238, 130, 238, 0.3)
                    );
                    opacity: 0;
                    transition: opacity 0.5s ease-out, transform 0.5s ease-out;
                    mix-blend-mode: color-dodge;
                    filter: blur(10px);
                }
            `;
            document.head.appendChild(style);
        }
    }
}