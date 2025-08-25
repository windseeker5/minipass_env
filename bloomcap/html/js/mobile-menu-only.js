/* ===================================================================
   MOBILE MENU ONLY - Gestion simple du menu mobile
   Ne touche que le mobile, laisse le desktop intact
   =================================================================== */

(function() {
    'use strict';
    
    let menuOpen = false;
    let isMobile = false;
    
    function init() {
        // Vérifier si on est sur mobile
        checkMobile();
        
        if (isMobile) {
            initMobileMenu();
        }
        
        // Écouter les changements de taille
        window.addEventListener('resize', function() {
            const wasMobile = isMobile;
            checkMobile();
            
            if (isMobile && !wasMobile) {
                initMobileMenu();
            } else if (!isMobile && wasMobile && menuOpen) {
                closeMenu();
            }
        });
    }
    
    function checkMobile() {
        isMobile = window.innerWidth <= 768;
    }
    
    function initMobileMenu() {
        const menuTrigger = document.querySelector('.mobile-menu-trigger');
        const menuBlock = document.querySelector('.menu-block');
        const menuClose = document.querySelector('.mobile-menu-close');
        let menuOverlay = document.querySelector('.menu-overlay');
        
        if (!menuTrigger || !menuBlock) return;
        
        // S'assurer que le menu est fermé au départ
        menuBlock.classList.remove('is-active');
        if (menuOverlay) {
            menuOverlay.classList.remove('is-active');
        }
        document.body.style.overflow = '';
        menuOpen = false;
        
        // Créer l'overlay s'il n'existe pas
        if (!menuOverlay) {
            menuOverlay = document.createElement('div');
            menuOverlay.className = 'menu-overlay';
            document.body.appendChild(menuOverlay);
        }
        
        // Nettoyer les anciens listeners
        menuTrigger.replaceWith(menuTrigger.cloneNode(true));
        const newMenuTrigger = document.querySelector('.mobile-menu-trigger');
        
        // Event listeners
        newMenuTrigger.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleMenu();
        });
        
        if (menuOverlay) {
            menuOverlay.addEventListener('click', function(e) {
                e.preventDefault();
                closeMenu();
            });
        }
        
        if (menuClose) {
            menuClose.addEventListener('click', function(e) {
                e.preventDefault();
                closeMenu();
            });
        }
        
        // Fermer avec Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && menuOpen) {
                closeMenu();
            }
        });
        
        // Fermer lors du clic sur un lien
        const menuLinks = menuBlock.querySelectorAll('.nav-link-item');
        menuLinks.forEach(link => {
            link.addEventListener('click', function() {
                setTimeout(closeMenu, 100); // Petit délai pour la transition
            });
        });
        
        console.log('Menu mobile initialisé');
    }
    
    function toggleMenu() {
        if (!isMobile) return;
        
        if (menuOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }
    
    function openMenu() {
        if (!isMobile) return;
        
        const menuBlock = document.querySelector('.menu-block');
        const menuOverlay = document.querySelector('.menu-overlay');
        
        if (!menuBlock) return;
        
        menuOpen = true;
        menuBlock.classList.add('is-active');
        
        if (menuOverlay) {
            menuOverlay.classList.add('is-active');
        }
        
        // Bloquer le scroll du body
        document.body.style.overflow = 'hidden';
        
        console.log('Menu ouvert');
    }
    
    function closeMenu() {
        const menuBlock = document.querySelector('.menu-block');
        const menuOverlay = document.querySelector('.menu-overlay');
        
        if (!menuBlock) return;
        
        menuOpen = false;
        menuBlock.classList.remove('is-active');
        
        if (menuOverlay) {
            menuOverlay.classList.remove('is-active');
        }
        
        // Rétablir le scroll
        document.body.style.overflow = '';
        
        console.log('Menu fermé');
    }
    
    // Initialiser quand le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Exposer pour debug
    window.MobileMenuOnly = {
        toggle: toggleMenu,
        close: closeMenu,
        open: openMenu,
        isOpen: () => menuOpen,
        isMobile: () => isMobile
    };
    
})();