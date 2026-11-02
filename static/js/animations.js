/* ================================================================
   Animation Utilities
   Lightweight motion library using Web Animations API
   ================================================================ */

const Animations = {
    // Duration presets
    duration: {
        fast: 200,
        base: 300,
        slow: 500,
        verySlow: 800
    },
    
    // Easing presets
    easing: {
        standard: 'cubic-bezier(0.4, 0, 0.2, 1)',
        decelerate: 'cubic-bezier(0, 0, 0.2, 1)',
        accelerate: 'cubic-bezier(0.4, 0, 1, 1)',
        spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
    },
    
    // Fade in element
    fadeIn(element, duration = this.duration.base) {
        return element.animate([
            { opacity: 0 },
            { opacity: 1 }
        ], {
            duration: duration,
            easing: this.easing.standard,
            fill: 'both'
        });
    },
    
    // Fade out element
    fadeOut(element, duration = this.duration.base) {
        return element.animate([
            { opacity: 1 },
            { opacity: 0 }
        ], {
            duration: duration,
            easing: this.easing.standard,
            fill: 'both'
        });
    },
    
    // Slide up element
    slideUp(element, distance = 20, duration = this.duration.base) {
        return element.animate([
            { opacity: 0, transform: `translateY(${distance}px)` },
            { opacity: 1, transform: 'translateY(0)' }
        ], {
            duration: duration,
            easing: this.easing.decelerate,
            fill: 'both'
        });
    },
    
    // Scale in element (pop effect)
    scaleIn(element, duration = this.duration.base) {
        return element.animate([
            { opacity: 0, transform: 'scale(0.8)' },
            { opacity: 1, transform: 'scale(1)' }
        ], {
            duration: duration,
            easing: this.easing.spring,
            fill: 'both'
        });
    },
    
    // Bounce element
    bounce(element) {
        return element.animate([
            { transform: 'scale(1)' },
            { transform: 'scale(1.1)', offset: 0.3 },
            { transform: 'scale(0.95)', offset: 0.6 },
            { transform: 'scale(1)' }
        ], {
            duration: this.duration.slow,
            easing: this.easing.standard
        });
    },
    
    // Shake element (error feedback)
    shake(element) {
        return element.animate([
            { transform: 'translateX(0)' },
            { transform: 'translateX(-10px)', offset: 0.25 },
            { transform: 'translateX(10px)', offset: 0.5 },
            { transform: 'translateX(-10px)', offset: 0.75 },
            { transform: 'translateX(0)' }
        ], {
            duration: this.duration.slow,
            easing: this.easing.standard
        });
    },
    
    // Pulse element (attention grabber)
    pulse(element, times = 2) {
        const keyframes = [];
        for (let i = 0; i <= times * 2; i++) {
            keyframes.push({
                transform: i % 2 === 0 ? 'scale(1)' : 'scale(1.05)',
                offset: i / (times * 2)
            });
        }
        
        return element.animate(keyframes, {
            duration: this.duration.verySlow,
            easing: this.easing.standard
        });
    },
    
    // Stagger animations for multiple elements
    stagger(elements, animationFn, delayBetween = 50) {
        return Array.from(elements).map((el, i) => {
            return new Promise(resolve => {
                setTimeout(() => {
                    const anim = animationFn(el);
                    anim.onfinish = resolve;
                }, i * delayBetween);
            });
        });
    },
    
    // Confetti burst (using CSS classes + potential particle system)
    confetti(element) {
        element.classList.add('confetti-burst');
        setTimeout(() => element.classList.remove('confetti-burst'), 1000);
    },
    
    // Combo meter flash
    comboFlash(element) {
        return element.animate([
            { boxShadow: '0 0 0 rgba(255, 215, 61, 0)', transform: 'scale(1)' },
            { boxShadow: '0 0 20px rgba(255, 215, 61, 0.8)', transform: 'scale(1.1)', offset: 0.5 },
            { boxShadow: '0 0 0 rgba(255, 215, 61, 0)', transform: 'scale(1)' }
        ], {
            duration: this.duration.slow,
            easing: this.easing.standard
        });
    },
    
    // Respects prefers-reduced-motion
    shouldAnimate() {
        return !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    },
    
    // Safe animate: skips animation if reduced motion is preferred
    safeAnimate(element, animationFn, ...args) {
        if (this.shouldAnimate()) {
            return animationFn.call(this, element, ...args);
        } else {
            // Return a fake animation that completes immediately
            return {
                finished: Promise.resolve(),
                cancel: () => {},
                onfinish: null
            };
        }
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Animations;
}

// Classic script: top-level const is not a window property, so expose it
window.Animations = Animations;
