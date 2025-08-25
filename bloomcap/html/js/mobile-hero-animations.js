/* ===================================================================
   MOBILE HERO ANIMATIONS - Animations fluides et optimisées
   =================================================================== */

(function() {
    'use strict';
    
    const isMobile = () => window.innerWidth <= 768;
    
    function initMobileHeroAnimations() {
        if (!isMobile()) return;
        
        // 1. Optimiser AOS pour mobile
        optimizeAOSForMobile();
        
        // 2. Ajouter animations personnalisées
        addCustomAnimations();
        
        // 3. Gérer l'intersection observer pour performance
        setupIntersectionObserver();
        
        console.log('🎬 Animations hero mobile activées');
    }
    
    function optimizeAOSForMobile() {
        if (typeof AOS === 'undefined') return;
        
        // Configuration AOS optimisée pour mobile
        AOS.init({
            duration: 500,
            easing: 'ease-out',
            once: true,
            offset: 30,
            delay: 0,
            disable: false,
            startEvent: 'DOMContentLoaded',
            initClassName: 'aos-init',
            animatedClassName: 'aos-animate',
            useClassNames: false,
            disableMutationObserver: false,
            debounceDelay: 50,
            throttleDelay: 99,
        });
        
        // Ajuster les éléments existants
        const heroElements = document.querySelectorAll('.welcome-content--l3 [data-aos]');
        heroElements.forEach((element, index) => {
            element.setAttribute('data-aos-duration', '400');
            element.setAttribute('data-aos-delay', index * 80);
            element.setAttribute('data-aos-easing', 'ease-out');
        });
        
        // Réduire les animations trop lourdes
        const heavyAnimations = document.querySelectorAll('[data-aos="zoom-in"], [data-aos="flip-up"]');
        heavyAnimations.forEach(element => {
            element.setAttribute('data-aos', 'fade-up');
            element.setAttribute('data-aos-duration', '400');
        });
    }
    
    function addCustomAnimations() {
        // Animation spéciale pour l'image
        const heroImage = document.querySelector('.welcome-area .col-lg-5');
        if (heroImage) {
            heroImage.style.opacity = '0';
            heroImage.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                heroImage.style.transition = 'all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
                heroImage.style.opacity = '1';
                heroImage.style.transform = 'translateY(0)';
            }, 500);
        }
        
        // Animation pour les boutons CTA
        const ctaButtons = document.querySelectorAll('.welcome-content--l3 a');
        ctaButtons.forEach((button, index) => {
            button.style.opacity = '0';
            button.style.transform = 'translateY(10px)';
            
            setTimeout(() => {
                button.style.transition = 'all 0.4s ease-out';
                button.style.opacity = '1';
                button.style.transform = 'translateY(0)';
            }, 400 + (index * 100));
        });
    }
    
    function setupIntersectionObserver() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                }
            });
        }, {
            rootMargin: '-20px 0px -50px 0px',
            threshold: 0.1
        });
        
        // Observer les éléments du hero
        const heroElements = document.querySelectorAll('.welcome-content--l3 > *');
        heroElements.forEach(element => {
            observer.observe(element);
        });
    }
    
    // Gestion du header scroll
    function handleHeaderScroll() {
        if (!isMobile()) return;
        
        const header = document.querySelector('.site-header');
        if (!header) return;
        
        let lastScrollY = window.scrollY;
        
        function updateHeader() {
            const currentScrollY = window.scrollY;
            
            if (currentScrollY > 50) {
                header.style.background = 'rgba(255, 255, 255, 0.98)';
                header.style.backdropFilter = 'blur(25px)';
                header.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
            } else {
                header.style.background = 'rgba(255, 255, 255, 0.95)';
                header.style.backdropFilter = 'blur(20px)';
                header.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
            }
            
            lastScrollY = currentScrollY;
        }
        
        window.addEventListener('scroll', updateHeader, { passive: true });
    }
    
    // Touch feedback amélioré
    function enhanceTouchFeedback() {
        const touchElements = document.querySelectorAll('.welcome-content--l3 a, .mobile-menu-trigger, .header-btn');
        
        touchElements.forEach(element => {
            element.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
                this.style.transition = 'transform 0.1s ease';
            }, { passive: true });
            
            element.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.style.transform = '';
                    this.style.transition = '';
                }, 100);
            }, { passive: true });
            
            element.addEventListener('touchcancel', function() {
                this.style.transform = '';
                this.style.transition = '';
            }, { passive: true });
        });
    }
    
    // Ajustement dynamique de la hauteur hero
    function adjustHeroHeight() {
        if (!isMobile()) return;
        
        const heroSection = document.querySelector('.welcome-area');
        if (!heroSection) return;
        
        const viewportHeight = window.innerHeight;
        const headerHeight = 64;
        const minHeight = Math.max(viewportHeight * 0.75, 500);
        
        heroSection.style.minHeight = `${minHeight}px`;
        heroSection.style.paddingTop = `${headerHeight + 16}px`;
    }
    
    // Gestion orientation
    function handleOrientationChange() {
        setTimeout(() => {
            adjustHeroHeight();
            if (typeof AOS !== 'undefined') {
                AOS.refresh();
            }
        }, 200);
    }
    
    // Smooth scroll pour les CTA
    function setupSmoothScroll() {
        const ctaButtons = document.querySelectorAll('a[href="#formulaire"]');
        
        ctaButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                const target = document.querySelector('#formulaire');
                if (target) {
                    const headerOffset = 80;
                    const elementPosition = target.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                    
                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }
    
    // Initialisation
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(initMobileHeroAnimations, 100);
            });
        } else {
            setTimeout(initMobileHeroAnimations, 100);
        }
        
        // Setup additional features
        handleHeaderScroll();
        enhanceTouchFeedback();
        adjustHeroHeight();
        setupSmoothScroll();
        
        // Event listeners
        window.addEventListener('resize', adjustHeroHeight);
        window.addEventListener('orientationchange', handleOrientationChange);
    }
    
    // Démarrer
    init();
    
    // Debug pour mobile
    if (isMobile()) {
        window.mobileHeroDebug = {
            reinit: initMobileHeroAnimations,
            adjustHeight: adjustHeroHeight,
            isMobile: isMobile
        };
    }
    
})();