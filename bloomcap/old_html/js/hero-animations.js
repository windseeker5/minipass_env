/* ===================================================================
   ANIMATIONS HERO MOBILE - JavaScript optimisé
   Gère les animations d'entrée et micro-interactions
   =================================================================== */

(function() {
    'use strict';
    
    // Variables globales
    let isMobile = window.innerWidth <= 768;
    let animationsInitialized = false;
    
    // Initialisation
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initHeroAnimations);
        } else {
            initHeroAnimations();
        }
    }
    
    function initHeroAnimations() {
        // Vérifier si on est sur mobile
        isMobile = window.innerWidth <= 768;
        
        if (isMobile && !animationsInitialized) {
            setupMobileHeroAnimations();
            setupButtonInteractions();
            setupScrollAnimations();
            animationsInitialized = true;
        }
        
        // Écouter les changements de taille d'écran
        window.addEventListener('resize', debounce(handleResize, 250));
    }
    
    // ============================================================================
    // ANIMATIONS D'ENTRÉE HERO
    // ============================================================================
    
    function setupMobileHeroAnimations() {
        const heroContent = document.querySelector('.welcome-content--l3');
        const heroImage = document.querySelector('.welcome-area .col-lg-5');
        
        if (!heroContent) return;
        
        // Observer d'intersection pour déclencher les animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && entry.intersectionRatio > 0.3) {
                    triggerHeroAnimations();
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.3,
            rootMargin: '0px 0px -100px 0px'
        });
        
        observer.observe(heroContent);
    }
    
    function triggerHeroAnimations() {
        const heroElements = document.querySelectorAll('.welcome-content--l3 > *');
        const heroImage = document.querySelector('.welcome-area .col-lg-5');
        
        // Animation du contenu avec délais échelonnés
        heroElements.forEach((element, index) => {
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
                element.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            }, index * 100 + 100);
        });
        
        // Animation de l'image
        if (heroImage) {
            setTimeout(() => {
                heroImage.style.opacity = '1';
                heroImage.style.transform = 'translateY(0) scale(1)';
                heroImage.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
            }, 600);
        }
    }
    
    // ============================================================================
    // INTERACTIONS BOUTONS
    // ============================================================================
    
    function setupButtonInteractions() {
        const heroButtons = document.querySelectorAll('.welcome-area a[class*="btn"], .welcome-area .btn');
        
        heroButtons.forEach(button => {
            // Effet tactile au touch
            button.addEventListener('touchstart', function(e) {
                this.style.transform = 'scale(0.98)';
                this.style.transition = 'transform 0.1s ease';
            }, { passive: true });
            
            button.addEventListener('touchend', function(e) {
                setTimeout(() => {
                    this.style.transform = '';
                    this.style.transition = 'all 0.2s ease';
                }, 100);
            }, { passive: true });
            
            // Annuler l'effet si touch est annulé
            button.addEventListener('touchcancel', function(e) {
                this.style.transform = '';
                this.style.transition = 'all 0.2s ease';
            }, { passive: true });
            
            // Effet hover pour desktop (préservé)
            if (!isTouchDevice()) {
                button.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-2px)';
                });
                
                button.addEventListener('mouseleave', function() {
                    this.style.transform = '';
                });
            }
        });
    }
    
    // ============================================================================
    // ANIMATIONS AU SCROLL
    // ============================================================================
    
    function setupScrollAnimations() {
        let ticking = false;
        let lastScrollY = 0;
        
        function updateHeroOnScroll() {
            const currentScrollY = window.pageYOffset;
            const heroSection = document.querySelector('.welcome-area');
            
            if (!heroSection) return;
            
            // Effet parallaxe subtil sur le hero
            const scrollRatio = Math.min(currentScrollY / window.innerHeight, 1);
            const translateY = scrollRatio * 30; // 30px max
            
            if (isMobile) {
                // Parallaxe très subtile sur mobile pour performance
                heroSection.style.transform = `translateY(${translateY * 0.3}px)`;
            }
            
            lastScrollY = currentScrollY;
            ticking = false;
        }
        
        function requestScrollUpdate() {
            if (!ticking) {
                requestAnimationFrame(updateHeroOnScroll);
                ticking = true;
            }
        }
        
        // Seulement si pas de préférence pour mouvement réduit
        if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            window.addEventListener('scroll', requestScrollUpdate, { passive: true });
        }
    }
    
    // ============================================================================
    // MICRO-INTERACTIONS AVANCÉES
    // ============================================================================
    
    function setupAdvancedInteractions() {
        // Animation du badge au hover
        const badge = document.querySelector('.welcome-content--l3 .d-inline-flex');
        if (badge && !isTouchDevice()) {
            badge.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.05)';
                this.style.background = 'rgba(251, 191, 36, 0.25)';
            });
            
            badge.addEventListener('mouseleave', function() {
                this.style.transform = '';
                this.style.background = '';
            });
        }
        
        // Animation du titre avec effet de typing (optionnel)
        const title = document.querySelector('.welcome-content--l3 h1');
        if (title && isMobile) {
            // Animation subtile du span doré
            const goldSpan = title.querySelector('span[style*="color: #fbbf24"]');
            if (goldSpan) {
                goldSpan.style.animation = 'goldShimmer 3s ease-in-out infinite';
            }
        }
    }
    
    // ============================================================================
    // GESTION RESPONSIVE
    // ============================================================================
    
    function handleResize() {
        const wasMainobile = isMobile;
        isMobile = window.innerWidth <= 768;
        
        // Réinitialiser les animations si changement mobile/desktop
        if (wasMainobile !== isMobile) {
            if (isMobile && !animationsInitialized) {
                setupMobileHeroAnimations();
                setupButtonInteractions();
                animationsInitialized = true;
            } else if (!isMobile && animationsInitialized) {
                // Nettoyer les styles mobile
                const heroElements = document.querySelectorAll('.welcome-content--l3 > *');
                heroElements.forEach(element => {
                    element.style.opacity = '';
                    element.style.transform = '';
                    element.style.transition = '';
                });
                animationsInitialized = false;
            }
        }
        
        // Recalculer les dimensions pour les animations
        updateViewportDimensions();
    }
    
    function updateViewportDimensions() {
        // Dynamic viewport height pour mobile
        if (isMobile) {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        }
    }
    
    // ============================================================================
    // OPTIMISATIONS PERFORMANCE
    // ============================================================================
    
    function optimizeForPerformance() {
        // Désactiver les animations si préférence utilisateur
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            const style = document.createElement('style');
            style.textContent = `
                .welcome-content--l3 > * {
                    animation: none !important;
                    transition: none !important;
                }
            `;
            document.head.appendChild(style);
            return;
        }
        
        // Optimiser la performance sur les anciens appareils
        if (isMobile && isLowEndDevice()) {
            // Réduire les animations pour les appareils moins performants
            document.documentElement.style.setProperty('--animation-duration', '0.3s');
        }
    }
    
    function isLowEndDevice() {
        // Détection basique des appareils moins performants
        return navigator.hardwareConcurrency < 4 || 
               navigator.deviceMemory < 4 ||
               /Android.*[4-6]\./.test(navigator.userAgent);
    }
    
    // ============================================================================
    // UTILITAIRES
    // ============================================================================
    
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
    
    function isTouchDevice() {
        return 'ontouchstart' in window || 
               navigator.maxTouchPoints > 0 ||
               navigator.msMaxTouchPoints > 0;
    }
    
    // ============================================================================
    // AJOUT DES KEYFRAMES CSS DYNAMIQUES
    // ============================================================================
    
    function addDynamicStyles() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes goldShimmer {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.8; }
            }
            
            @keyframes mobileSlideUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes mobileImageFade {
                from {
                    opacity: 0;
                    transform: translateY(30px) scale(0.95);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }
            
            /* États initiaux pour les animations */
            @media screen and (max-width: 768px) {
                .welcome-content--l3 > * {
                    opacity: 0;
                    transform: translateY(20px);
                }
                
                .welcome-area .col-lg-5 {
                    opacity: 0;
                    transform: translateY(30px) scale(0.95);
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // ============================================================================
    // INITIALISATION GLOBALE
    // ============================================================================
    
    // Ajouter les styles dynamiques
    addDynamicStyles();
    
    // Optimiser pour les performances
    optimizeForPerformance();
    
    // Configurer les interactions avancées
    setupAdvancedInteractions();
    
    // Démarrer l'initialisation
    init();
    
    // Exposer pour debug
    window.HeroAnimations = {
        triggerHeroAnimations,
        isMobile: () => isMobile,
        animationsInitialized: () => animationsInitialized
    };
    
})();