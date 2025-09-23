/* ===================================================================
   MOBILE AOS OPTIMIZER - Améliore les animations AOS pour mobile
   =================================================================== */

(function() {
    'use strict';
    
    const isMobile = () => window.innerWidth <= 768;
    
    function optimizeAOSForMobile() {
        if (!isMobile() || typeof AOS === 'undefined') return;
        
        // Configuration AOS optimisée pour mobile
        AOS.init({
            duration: 600,        // Plus rapide sur mobile
            easing: 'ease-out',   // Plus naturel
            once: true,          // Une seule fois pour performance
            offset: 50,          // Déclenche plus tôt
            delay: 0,            // Pas de délai global
            disable: false,      // Toujours actif sur mobile
            startEvent: 'DOMContentLoaded',
            initClassName: 'aos-init',
            animatedClassName: 'aos-animate',
            useClassNames: false,
            disableMutationObserver: false,
            debounceDelay: 50,
            throttleDelay: 99,
        });
        
        // Ajustements spécifiques pour le hero
        optimizeHeroAnimations();
        
        // Réduire les animations trop lourdes
        reduceBulkyAnimations();
        
        console.log('📱 AOS optimisé pour mobile');
    }
    
    function optimizeHeroAnimations() {
        // Éléments du hero à animer différemment
        const heroElements = document.querySelectorAll('.welcome-content--l3 [data-aos]');
        
        heroElements.forEach((element, index) => {
            // Modifier les animations trop brusques
            if (element.getAttribute('data-aos') === 'fade-up') {
                element.setAttribute('data-aos-duration', '500');
                element.setAttribute('data-aos-delay', index * 100);
                element.setAttribute('data-aos-easing', 'ease-out');
            }
        });
        
        // Animation spéciale pour l'image hero
        const heroImage = document.querySelector('.welcome-area .col-lg-5 [data-aos]');
        if (heroImage) {
            heroImage.setAttribute('data-aos', 'fade-up');
            heroImage.setAttribute('data-aos-duration', '700');
            heroImage.setAttribute('data-aos-delay', '400');
        }
    }
    
    function reduceBulkyAnimations() {
        // Remplacer les animations trop lourdes par des plus légères
        const bulkyAnimations = document.querySelectorAll('[data-aos="zoom-in"], [data-aos="flip-up"], [data-aos="flip-down"]');
        
        bulkyAnimations.forEach(element => {
            element.setAttribute('data-aos', 'fade-up');
            element.setAttribute('data-aos-duration', '500');
        });
        
        // Réduire les délais trop longs
        const delayedElements = document.querySelectorAll('[data-aos-delay]');
        delayedElements.forEach(element => {
            const currentDelay = parseInt(element.getAttribute('data-aos-delay'));
            if (currentDelay > 600) {
                element.setAttribute('data-aos-delay', '600');
            }
        });
    }
    
    // Gestion du resize pour réinitialiser AOS si nécessaire
    function handleResize() {
        if (typeof AOS !== 'undefined') {
            setTimeout(() => {
                AOS.refresh();
            }, 150);
        }
    }
    
    // Observer les changements d'orientation
    function handleOrientationChange() {
        setTimeout(() => {
            if (typeof AOS !== 'undefined') {
                AOS.refresh();
            }
        }, 300);
    }
    
    // Initialisation
    function init() {
        // Attendre que AOS soit disponible
        if (typeof AOS !== 'undefined') {
            optimizeAOSForMobile();
        } else {
            // Réessayer après un court délai
            setTimeout(() => {
                if (typeof AOS !== 'undefined') {
                    optimizeAOSForMobile();
                }
            }, 100);
        }
        
        // Écouter les événements
        window.addEventListener('resize', handleResize);
        window.addEventListener('orientationchange', handleOrientationChange);
    }
    
    // Démarrer après le DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Exposer pour debug
    if (isMobile()) {
        window.mobileAOSDebug = {
            reInit: optimizeAOSForMobile,
            isMobile: isMobile
        };
    }
    
})();