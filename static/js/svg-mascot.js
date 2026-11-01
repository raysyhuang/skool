/* ================================================================
   SVG Animated Mascot System
   GSAP-powered character animations
   ================================================================ */

const SVGMascot = {
    container: null,
    svg: null,
    currentEmotion: 'happy',
    
    emotions: {
        happy: { color: '#FFD93D', expression: 'smile' },
        excited: { color: '#FF6B6B', expression: 'big-smile' },
        thinking: { color: '#B8A4E8', expression: 'curious' },
        encouraging: { color: '#6BCF7F', expression: 'determined' }
    },
    
    init(containerId = 'mascotContainer') {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = containerId;
            this.container.className = 'svg-mascot-container';
            this.container.style.cssText = 'position:fixed;bottom:80px;right:24px;z-index:300;';
            document.body.appendChild(this.container);
        }
        
        this.render();
        this.startIdleAnimation();
    },
    
    render() {
        // Create SVG mascot character (simplified friendly robot/creature)
        const svgNS = "http://www.w3.org/2000/svg";
        this.svg = document.createElementNS(svgNS, "svg");
        this.svg.setAttribute("width", "120");
        this.svg.setAttribute("height", "120");
        this.svg.setAttribute("viewBox", "0 0 120 120");
        
        // Body (circle)
        const body = document.createElementNS(svgNS, "circle");
        body.setAttribute("cx", "60");
        body.setAttribute("cy", "60");
        body.setAttribute("r", "45");
        body.setAttribute("fill", this.emotions[this.currentEmotion].color);
        body.setAttribute("id", "mascot-body");
        this.svg.appendChild(body);
        
        // Eyes
        const leftEye = document.createElementNS(svgNS, "circle");
        leftEye.setAttribute("cx", "45");
        leftEye.setAttribute("cy", "50");
        leftEye.setAttribute("r", "5");
        leftEye.setAttribute("fill", "#2d3436");
        leftEye.setAttribute("id", "left-eye");
        this.svg.appendChild(leftEye);
        
        const rightEye = document.createElementNS(svgNS, "circle");
        rightEye.setAttribute("cx", "75");
        rightEye.setAttribute("cy", "50");
        rightEye.setAttribute("r", "5");
        rightEye.setAttribute("fill", "#2d3436");
        rightEye.setAttribute("id", "right-eye");
        this.svg.appendChild(rightEye);
        
        // Mouth (smile path)
        const mouth = document.createElementNS(svgNS, "path");
        mouth.setAttribute("d", "M 45 70 Q 60 80 75 70");
        mouth.setAttribute("stroke", "#2d3436");
        mouth.setAttribute("stroke-width", "3");
        mouth.setAttribute("fill", "none");
        mouth.setAttribute("stroke-linecap", "round");
        mouth.setAttribute("id", "mascot-mouth");
        this.svg.appendChild(mouth);
        
        // Glow effect
        const glow = document.createElementNS(svgNS, "circle");
        glow.setAttribute("cx", "60");
        glow.setAttribute("cy", "60");
        glow.setAttribute("r", "50");
        glow.setAttribute("fill", "none");
        glow.setAttribute("stroke", this.emotions[this.currentEmotion].color);
        glow.setAttribute("stroke-width", "2");
        glow.setAttribute("opacity", "0.3");
        glow.setAttribute("id", "mascot-glow");
        this.svg.insertBefore(glow, body);
        
        this.container.innerHTML = '';
        this.container.appendChild(this.svg);
    },
    
    startIdleAnimation() {
        if (!window.gsap) return;
        
        // Floating animation
        gsap.to(this.svg, {
            y: -10,
            duration: 2,
            ease: "sine.inOut",
            repeat: -1,
            yoyo: true
        });
        
        // Glow pulse
        gsap.to("#mascot-glow", {
            opacity: 0.6,
            duration: 1.5,
            ease: "sine.inOut",
            repeat: -1,
            yoyo: true
        });
        
        // Blink eyes
        this.blinkLoop();
    },
    
    blinkLoop() {
        if (!window.gsap) return;
        
        const blink = () => {
            gsap.to("#left-eye, #right-eye", {
                scaleY: 0,
                duration: 0.1,
                yoyo: true,
                repeat: 1,
                onComplete: () => {
                    setTimeout(blink, Math.random() * 3000 + 2000);
                }
            });
        };
        
        setTimeout(blink, 2000);
    },
    
    setEmotion(emotion) {
        if (!this.emotions[emotion]) return;
        
        this.currentEmotion = emotion;
        const data = this.emotions[emotion];
        
        // Animate color change
        if (window.gsap) {
            gsap.to("#mascot-body", {
                fill: data.color,
                duration: 0.5,
                ease: "power2.inOut"
            });
            
            gsap.to("#mascot-glow", {
                stroke: data.color,
                duration: 0.5,
                ease: "power2.inOut"
            });
            
            // Bounce on emotion change
            gsap.fromTo(this.svg, 
                { scale: 1 },
                { scale: 1.2, duration: 0.3, ease: "back.out(2)", yoyo: true, repeat: 1 }
            );
        }
        
        // Update mouth expression
        const mouth = document.getElementById('mascot-mouth');
        if (mouth) {
            let mouthPath;
            switch (data.expression) {
                case 'big-smile':
                    mouthPath = "M 40 70 Q 60 90 80 70";
                    break;
                case 'curious':
                    mouthPath = "M 50 75 L 70 75";
                    break;
                case 'determined':
                    mouthPath = "M 45 72 Q 60 78 75 72";
                    break;
                default:
                    mouthPath = "M 45 70 Q 60 80 75 70";
            }
            
            if (window.gsap) {
                gsap.to(mouth, {
                    attr: { d: mouthPath },
                    duration: 0.3,
                    ease: "power2.inOut"
                });
            } else {
                mouth.setAttribute('d', mouthPath);
            }
        }
    },
    
    celebrate() {
        if (!window.gsap) return;
        
        // Jump animation
        gsap.to(this.svg, {
            y: -30,
            duration: 0.4,
            ease: "power2.out",
            onComplete: () => {
                gsap.to(this.svg, {
                    y: 0,
                    duration: 0.4,
                    ease: "bounce.out"
                });
            }
        });
        
        // Spin
        gsap.to(this.svg, {
            rotation: 360,
            duration: 0.8,
            ease: "power2.inOut"
        });
    },
    
    say(message, duration = 3000) {
        // Create speech bubble
        let bubble = document.getElementById('mascot-speech');
        if (!bubble) {
            bubble = document.createElement('div');
            bubble.id = 'mascot-speech';
            bubble.style.cssText = `
                position: absolute;
                bottom: 130px;
                right: 0;
                background: white;
                padding: 12px 16px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                max-width: 200px;
                font-size: 14px;
                font-weight: 600;
                opacity: 0;
                transform: translateY(10px);
                transition: opacity 0.3s, transform 0.3s;
            `;
            this.container.appendChild(bubble);
        }
        
        bubble.textContent = message;
        bubble.style.opacity = '1';
        bubble.style.transform = 'translateY(0)';
        
        setTimeout(() => {
            bubble.style.opacity = '0';
            bubble.style.transform = 'translateY(10px)';
        }, duration);
    }
};

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (document.querySelector('[data-mascot-enabled]')) {
            SVGMascot.init();
        }
    });
} else {
    if (document.querySelector('[data-mascot-enabled]')) {
        SVGMascot.init();
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SVGMascot;
}
