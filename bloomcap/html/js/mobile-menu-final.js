/* ===================================================================
   MOBILE MENU FINAL - Solution définitive et simple
   =================================================================== */

(function() {
    'use strict';
    
    let menuOpen = false;
    
    // === FERMETURE IMMÉDIATE AU CHARGEMENT - MOBILE SEULEMENT ===
    function forceCloseMenu() {
        // NE PAS TOUCHER AU DESKTOP
        if (window.innerWidth > 768) {
            return;
        }
        
        const menuBlock = document.querySelector('.menu-block');
        const menuOverlay = document.querySelector('.menu-overlay');
        const menuTrigger = document.querySelector('.mobile-menu-trigger');
        
        // Réinitialiser burger (mobile seulement)
        if (menuTrigger) {
            menuTrigger.classList.remove('is-active');
        }
        
        if (menuBlock) {
            menuBlock.classList.remove('is-active');
            menuBlock.style.right = '-100%';
            menuBlock.style.transform = 'translateX(100%)';
            menuBlock.style.visibility = 'hidden';
        }
        
        if (menuOverlay) {
            menuOverlay.classList.remove('is-active');
            menuOverlay.style.opacity = '0';
            menuOverlay.style.visibility = 'hidden';
        }
        
        document.body.style.overflow = '';
        menuOpen = false;
    }
    
    // === INITIALISATION MOBILE UNIQUEMENT ===
    function initMobile() {
        // STRICTEMENT MOBILE SEULEMENT - Ne pas toucher au desktop
        if (window.innerWidth > 768) {
            console.log('🖥️ Desktop détecté - Aucune intervention');
            return;
        }
        
        const menuTrigger = document.querySelector('.mobile-menu-trigger');
        const menuBlock = document.querySelector('.menu-block');
        const menuClose = document.querySelector('.mobile-menu-close');
        let menuOverlay = document.querySelector('.menu-overlay');
        
        if (!menuTrigger || !menuBlock) return;
        
        // Créer overlay si besoin
        if (!menuOverlay) {
            menuOverlay = document.createElement('div');
            menuOverlay.className = 'menu-overlay';
            document.body.appendChild(menuOverlay);
        }
        
        // S'assurer que le menu est fermé
        forceCloseMenu();
        
        // === EVENT LISTENERS ===
        
        // Burger menu
        menuTrigger.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (menuOpen) {
                closeMenu();
            } else {
                openMenu();
            }
        });
        
        // Overlay
        if (menuOverlay) {
            menuOverlay.addEventListener('click', closeMenu);
        }
        
        // Bouton fermer
        if (menuClose) {
            menuClose.addEventListener('click', closeMenu);
        }
        
        // Échap
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && menuOpen) {
                closeMenu();
            }
        });
        
        // Liens menu
        const menuLinks = menuBlock.querySelectorAll('a');
        menuLinks.forEach(link => {
            link.addEventListener('click', function() {
                setTimeout(closeMenu, 100);
            });
        });
        
        console.log('✅ Menu mobile initialisé');
    }
    
    // === OUVRIR MENU ===
    function openMenu() {
        if (window.innerWidth > 768) return;
        
        const menuBlock = document.querySelector('.menu-block');
        const menuOverlay = document.querySelector('.menu-overlay');
        const menuTrigger = document.querySelector('.mobile-menu-trigger');
        
        if (!menuBlock) return;
        
        menuOpen = true;
        
        // Animer burger
        if (menuTrigger) {
            menuTrigger.classList.add('is-active');
        }
        
        // Afficher menu
        menuBlock.classList.add('is-active');
        menuBlock.style.right = '0';
        menuBlock.style.transform = 'translateX(0)';
        menuBlock.style.visibility = 'visible';
        
        // Afficher overlay
        if (menuOverlay) {
            menuOverlay.classList.add('is-active');
            menuOverlay.style.opacity = '1';
            menuOverlay.style.visibility = 'visible';
        }
        
        // Bloquer scroll
        document.body.style.overflow = 'hidden';
        
        console.log('📱 Menu ouvert');
    }
    
    // === FERMER MENU ===
    function closeMenu() {
        const menuBlock = document.querySelector('.menu-block');
        const menuOverlay = document.querySelector('.menu-overlay');
        const menuTrigger = document.querySelector('.mobile-menu-trigger');
        
        menuOpen = false;
        
        // Réinitialiser burger
        if (menuTrigger) {
            menuTrigger.classList.remove('is-active');
        }
        
        // Masquer menu
        if (menuBlock) {
            menuBlock.classList.remove('is-active');
            menuBlock.style.right = '-100%';
            menuBlock.style.transform = 'translateX(100%)';
            menuBlock.style.visibility = 'hidden';
        }
        
        // Masquer overlay
        if (menuOverlay) {
            menuOverlay.classList.remove('is-active');
            menuOverlay.style.opacity = '0';
            menuOverlay.style.visibility = 'hidden';
        }
        
        // Rétablir scroll
        document.body.style.overflow = '';
        
        console.log('❌ Menu fermé');
    }
    
    // === GESTION RESIZE ===
    function handleResize() {
        if (window.innerWidth > 768 && menuOpen) {
            closeMenu();
        }
    }
    
    // === DÉMARRAGE ===
    function start() {
        // Fermeture immédiate
        forceCloseMenu();
        
        // Initialisation
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initMobile);
        } else {
            initMobile();
        }
        
        // Resize
        window.addEventListener('resize', handleResize);
    }
    
    // === LANCEMENT ===
    start();
    
    // === PRÉSERVATION DES ANIMATIONS - TOUTES TAILLES D'ÉCRAN ===
    // S'assurer qu'AOS fonctionne (pas de réinitialisation forcée)
    if (typeof AOS !== 'undefined') {
        // Simple refresh pour préserver les animations existantes
        setTimeout(() => {
            AOS.refresh();
            console.log('🎬 AOS rafraîchi (préservation)');
        }, 100);
    }
    
    // === DEBUG GLOBAL ===
    window.MobileMenuFinal = {
        open: openMenu,
        close: closeMenu,
        forceClose: forceCloseMenu,
        isOpen: () => menuOpen,
        isMobile: () => window.innerWidth <= 768,
        refreshAnimations: () => {
            if (typeof AOS !== 'undefined') {
                AOS.refresh();
                console.log('🔄 Animations rafraîchies');
            }
        }
    };
    
})();