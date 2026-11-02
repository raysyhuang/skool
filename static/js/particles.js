/* ================================================================
   Canvas Particle System
   Lightweight celebration/feedback effects
   ================================================================ */

class ParticleSystem {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.animationFrame = null;
        
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }
    
    resize() {
        this.canvas.width = this.canvas.offsetWidth * window.devicePixelRatio;
        this.canvas.height = this.canvas.offsetHeight * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }
    
    emit(config) {
        const {
            x = this.canvas.width / 2,
            y = this.canvas.height / 2,
            count = 20,
            colors = ['#FFD93D', '#FF6B6B', '#6BCF7F', '#4A90E2'],
            shape = 'circle', // circle, star, confetti
            velocity = { min: 2, max: 8 },
            size = { min: 4, max: 12 },
            life = 2000,
            gravity = 0.3
        } = config;
        
        for (let i = 0; i < count; i++) {
            const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.5;
            const speed = velocity.min + Math.random() * (velocity.max - velocity.min);
            
            this.particles.push({
                x: x / window.devicePixelRatio,
                y: y / window.devicePixelRatio,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed - 2,
                size: size.min + Math.random() * (size.max - size.min),
                color: colors[Math.floor(Math.random() * colors.length)],
                shape: shape,
                rotation: Math.random() * Math.PI * 2,
                rotationSpeed: (Math.random() - 0.5) * 0.2,
                life: life,
                maxLife: life,
                gravity: gravity
            });
        }
        
        if (!this.animationFrame) {
            this.animate();
        }
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particles = this.particles.filter(p => {
            p.x += p.vx;
            p.y += p.vy;
            p.vy += p.gravity;
            p.rotation += p.rotationSpeed;
            p.life -= 16; // ~60fps
            
            const alpha = Math.max(0, p.life / p.maxLife);
            this.ctx.save();
            this.ctx.globalAlpha = alpha;
            
            if (p.shape === 'circle') {
                this.ctx.fillStyle = p.color;
                this.ctx.beginPath();
                this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                this.ctx.fill();
            } else if (p.shape === 'star') {
                this.drawStar(p.x, p.y, p.size, p.rotation, p.color);
            } else if (p.shape === 'confetti') {
                this.drawConfetti(p.x, p.y, p.size, p.rotation, p.color);
            }
            
            this.ctx.restore();
            return p.life > 0;
        });
        
        if (this.particles.length > 0) {
            this.animationFrame = requestAnimationFrame(() => this.animate());
        } else {
            this.animationFrame = null;
        }
    }
    
    drawStar(cx, cy, size, rotation, color) {
        this.ctx.save();
        this.ctx.translate(cx, cy);
        this.ctx.rotate(rotation);
        this.ctx.fillStyle = color;
        this.ctx.beginPath();
        
        for (let i = 0; i < 10; i++) {
            const angle = (Math.PI * 2 * i) / 10;
            const radius = i % 2 === 0 ? size : size / 2;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            
            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }
        
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.restore();
    }
    
    drawConfetti(cx, cy, size, rotation, color) {
        this.ctx.save();
        this.ctx.translate(cx, cy);
        this.ctx.rotate(rotation);
        this.ctx.fillStyle = color;
        this.ctx.fillRect(-size / 2, -size / 4, size, size / 2);
        this.ctx.restore();
    }
    
    celebrateCorrect() {
        this.emit({
            x: this.canvas.width / 2,
            y: this.canvas.height / 2,
            count: 30,
            colors: ['#00D084', '#FFD93D', '#6BCF7F'],
            shape: 'star',
            velocity: { min: 3, max: 10 },
            size: { min: 6, max: 16 },
            life: 2500
        });
    }
    
    celebrateStreak(streak) {
        const count = Math.min(50, 20 + streak * 5);
        this.emit({
            x: this.canvas.width / 2,
            y: this.canvas.height / 3,
            count: count,
            colors: ['#FF6B6B', '#FFD93D', '#B8A4E8'],
            shape: 'confetti',
            velocity: { min: 4, max: 12 },
            size: { min: 8, max: 20 },
            life: 3000,
            gravity: 0.4
        });
    }
    
    celebrateVictory() {
        // Two bursts for extra celebration
        setTimeout(() => {
            this.emit({
                x: this.canvas.width * 0.3,
                y: this.canvas.height * 0.2,
                count: 40,
                colors: ['#FFD93D', '#FF6B6B', '#6BCF7F', '#4A90E2', '#B8A4E8'],
                shape: 'confetti',
                velocity: { min: 5, max: 15 },
                size: { min: 10, max: 24 },
                life: 4000,
                gravity: 0.5
            });
        }, 0);
        
        setTimeout(() => {
            this.emit({
                x: this.canvas.width * 0.7,
                y: this.canvas.height * 0.2,
                count: 40,
                colors: ['#FFD93D', '#FF6B6B', '#6BCF7F', '#4A90E2', '#B8A4E8'],
                shape: 'confetti',
                velocity: { min: 5, max: 15 },
                size: { min: 10, max: 24 },
                life: 4000,
                gravity: 0.5
            });
        }, 200);
    }
    
    destroy() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        this.particles = [];
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ParticleSystem;
}

// Classic script: top-level class/const are not window properties, so expose it
window.ParticleSystem = ParticleSystem;
