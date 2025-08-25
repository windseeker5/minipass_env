/* ===================================================================
   MOBILE HEADER CLEAN - JavaScript minimaliste pour navigation mobile
   =================================================================== */

(function() {
    'use strict';
    
    // Variables globales
    let isMenuOpen = false;
    let isMobile = false;
    
    // Éléments DOM
    let menuTrigger, menuBlock, menuOverlay, header, body;
    
    // Initialisation
    function init() {
        // Vérifier si on est sur mobile
        checkMobile();
        
        if (!isMobile) return;
        
        // Récupérer les éléments
        setupElements();
        
        // Créer l'overlay s'il n'existe pas
        createOverlay();
        
        // Attacher les événements
        bindEvents();
        
        // S'assurer que le menu est fermé au démarrage
        closeMenu();
        
        console.log('🍔 Header mobile clean initialisé');
    }
    
    function checkMobile() {
        isMobile = window.innerWidth <= 991;
    }
    
    function setupElements() {
        menuTrigger = document.querySelector('.mobile-menu-trigger');
        menuBlock = document.querySelector('.menu-block');
        menuOverlay = document.querySelector('.menu-overlay');
        header = document.querySelector('.site-header');
        body = document.body;
        
        // Ajouter les attributs ARIA au bouton
        if (menuTrigger) {
            menuTrigger.setAttribute('aria-label', 'Menu principal');
            menuTrigger.setAttribute('aria-expanded', 'false');
            menuTrigger.setAttribute('type', 'button');
        }
    }
    
    function createOverlay() {
        if (!menuOverlay && menuBlock) {
            menuOverlay = document.createElement('div');
            menuOverlay.className = 'menu-overlay';
            body.appendChild(menuOverlay);
        }
    }
    
    function bindEvents() {
        // Click sur hamburger
        if (menuTrigger) {
            menuTrigger.addEventListener('click', toggleMenu);
            menuTrigger.addEventListener('keydown', handleKeyDown);
        }
        
        // Click sur overlay
        if (menuOverlay) {
            menuOverlay.addEventListener('click', closeMenu);
        }
        
        // Liens du menu
        const menuLinks = document.querySelectorAll('.site-menu-main a');
        menuLinks.forEach(link => {
            link.addEventListener('click', handleMenuLinkClick);
        });
        
        // Scroll pour header
        window.addEventListener('scroll', handleScroll, { passive: true });
        
        // Resize
        window.addEventListener('resize', handleResize);
        
        // Escape key
        document.addEventListener('keydown', handleEscapeKey);
    }
    
    function toggleMenu() {
        if (isMenuOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }
    
    function openMenu() {
        if (!isMobile || isMenuOpen) return;
        
        isMenuOpen = true;
        
        // Ajouter les classes actives
        if (menuTrigger) menuTrigger.classList.add('is-active');
        if (menuBlock) menuBlock.classList.add('is-active');
        if (menuOverlay) menuOverlay.classList.add('is-active');
        
        // Bloquer le scroll
        body.style.overflow = 'hidden';
        body.style.position = 'fixed';
        body.style.width = '100%';
        body.style.top = `-${window.scrollY}px`;
        
        // ARIA
        if (menuTrigger) menuTrigger.setAttribute('aria-expanded', 'true');
        
        // Focus sur premier lien après animation
        setTimeout(() => {
            const firstLink = menuBlock?.querySelector('.site-menu-main a');
            if (firstLink) firstLink.focus();
        }, 300);
    }
    
    function closeMenu() {
        if (!isMenuOpen) return;
        
        isMenuOpen = false;
        
        // Retirer les classes actives
        if (menuTrigger) menuTrigger.classList.remove('is-active');
        if (menuBlock) menuBlock.classList.remove('is-active');
        if (menuOverlay) menuOverlay.classList.remove('is-active');
        
        // Restaurer le scroll
        const scrollY = body.style.top;
        body.style.overflow = '';
        body.style.position = '';
        body.style.width = '';
        body.style.top = '';
        if (scrollY) {
            window.scrollTo(0, parseInt(scrollY || '0') * -1);
        }
        
        // ARIA
        if (menuTrigger) menuTrigger.setAttribute('aria-expanded', 'false');
        
        // Remettre le focus sur hamburger
        if (menuTrigger) menuTrigger.focus();
    }
    
    function handleMenuLinkClick(event) {
        const link = event.currentTarget;
        const href = link.getAttribute('href');
        
        // Si c'est un lien interne (#), fermer le menu et faire smooth scroll
        if (href && href.startsWith('#')) {
            closeMenu();
            
            const target = document.querySelector(href);
            if (target) {
                event.preventDefault();
                const headerHeight = header?.offsetHeight || 56;
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        } else {
            // Pour les liens externes, fermer le menu avec un délai
            setTimeout(closeMenu, 100);
        }
    }
    
    function handleScroll() {
        if (!isMobile || !header) return;
        
        const scrollY = window.scrollY;
        
        // Effet scroll sur header
        if (scrollY > 20) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        
        // Fermer le menu si scroll important
        if (isMenuOpen && scrollY > 100) {
            closeMenu();
        }
    }
    
    function handleResize() {
        const wasMobile = isMobile;
        checkMobile();
        
        // Si on passe de mobile à desktop
        if (wasMobile && !isMobile) {
            closeMenu();
            // Nettoyer les styles body
            body.style.overflow = '';
            body.style.position = '';
            body.style.width = '';
            body.style.top = '';
        }
        
        // Si on passe de desktop à mobile, réinitialiser
        if (!wasMobile && isMobile) {
            init();
        }
    }
    
    function handleKeyDown(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            toggleMenu();
        }
    }
    
    function handleEscapeKey(event) {
        if (event.key === 'Escape' && isMenuOpen) {
            closeMenu();
        }
    }
    
    // Initialisation quand le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Réinitialiser au resize si nécessaire
    window.addEventListener('resize', function() {
        if (window.innerWidth <= 991 && !menuTrigger) {
            setTimeout(init, 100);
        }
    });
    
    // API publique pour debug
    window.mobileHeaderClean = {
        toggle: toggleMenu,
        close: closeMenu,
        isOpen: () => isMenuOpen,
        isMobile: () => isMobile
    };
    
})();