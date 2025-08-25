/* ===================================================================
   MOBILE SIMPLE JS - Gestion basique du menu mobile
   Script léger et fonctionnel
   =================================================================== */

(function() {
    'use strict';
    
    let menuOpen = false;
    
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initMobileMenu);
        } else {
            initMobileMenu();
        }
    }
    
    function initMobileMenu() {
        // Vérifier si on est sur mobile
        if (window.innerWidth > 768) return;
        
        const menuTrigger = document.querySelector('.mobile-menu-trigger');
        const menuBlock = document.querySelector('.menu-block');
        const menuClose = document.querySelector('.mobile-menu-close');
        let menuOverlay = document.querySelector('.menu-overlay');
        
        if (!menuTrigger || !menuBlock) return;
        
        // FORCER LA FERMETURE DU MENU AU CHARGEMENT
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
        
        // Event listeners
        menuTrigger.addEventListener('click', toggleMenu);
        
        if (menuOverlay) {
            menuOverlay.addEventListener('click', closeMenu);
        }
        
        if (menuClose) {
            menuClose.addEventListener('click', closeMenu);
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
            link.addEventListener('click', closeMenu);
        });
    }
    
    function toggleMenu() {
        if (menuOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }
    
    function openMenu() {
        const menuBlock = document.querySelector('.menu-block');
        const menuOverlay = document.querySelector('.menu-overlay');
        
        if (!menuBlock || !menuOverlay) return;
        
        menuOpen = true;
        menuBlock.classList.add('is-active');
        menuOverlay.classList.add('is-active');
        
        // Bloquer le scroll
        document.body.style.overflow = 'hidden';
        
        console.log('Menu opened');
    }
    
    function closeMenu() {
        const menuBlock = document.querySelector('.menu-block');
        const menuOverlay = document.querySelector('.menu-overlay');
        
        if (!menuBlock || !menuOverlay) return;
        
        menuOpen = false;
        menuBlock.classList.remove('is-active');
        menuOverlay.classList.remove('is-active');
        
        // Rétablir le scroll
        document.body.style.overflow = '';
        
        console.log('Menu closed');
    }
    
    // Gérer le resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && menuOpen) {
            closeMenu();
        }
    });
    
    // RÉINITIALISATION IMMÉDIATE - Fermer le menu s'il est ouvert
    const menuBlock = document.querySelector('.menu-block');
    const menuOverlay = document.querySelector('.menu-overlay');
    if (menuBlock) {
        menuBlock.classList.remove('is-active');
        menuBlock.style.right = '-100%';
        menuBlock.style.transform = 'translateX(100%)';
    }
    if (menuOverlay) {
        menuOverlay.classList.remove('is-active');
    }
    document.body.style.overflow = '';
    
    // Démarrer
    init();
    
    // Exposer pour debug
    window.MobileMenu = {
        toggle: toggleMenu,
        close: closeMenu,
        isOpen: () => menuOpen
    };
    
})();