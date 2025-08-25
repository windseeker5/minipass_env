/* ===================================================================
   MOBILE MENU SAFE - JavaScript simple pour mobile uniquement
   =================================================================== */

(function() {
    'use strict';
    
    // Vérifier si on est sur mobile
    function isMobile() {
        return window.innerWidth <= 991;
    }
    
    // Initialiser seulement sur mobile
    if (!isMobile()) return;
    
    let isMenuOpen = false;
    const menuTrigger = document.querySelector('.mobile-menu-trigger');
    const menuBlock = document.querySelector('.menu-block');
    const menuOverlay = document.querySelector('.menu-overlay');
    const body = document.body;
    
    // Vérifier que les éléments existent
    if (!menuTrigger || !menuBlock) return;
    
    // Créer l'overlay s'il n'existe pas
    if (!menuOverlay) {
        const overlay = document.createElement('div');
        overlay.className = 'menu-overlay';
        body.appendChild(overlay);
        menuOverlay = overlay;
    }
    
    // Fonction pour ouvrir le menu
    function openMenu() {
        isMenuOpen = true;
        menuTrigger.classList.add('is-active');
        menuBlock.classList.add('is-active');
        if (menuOverlay) menuOverlay.classList.add('is-active');
        
        // Bloquer le scroll
        body.style.overflow = 'hidden';
    }
    
    // Fonction pour fermer le menu
    function closeMenu() {
        isMenuOpen = false;
        menuTrigger.classList.remove('is-active');
        menuBlock.classList.remove('is-active');
        if (menuOverlay) menuOverlay.classList.remove('is-active');
        
        // Restaurer le scroll
        body.style.overflow = '';
    }
    
    // Toggle menu
    function toggleMenu() {
        if (isMenuOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }
    
    // Event listeners
    menuTrigger.addEventListener('click', toggleMenu);
    
    if (menuOverlay) {
        menuOverlay.addEventListener('click', closeMenu);
    }
    
    // Fermer le menu quand on clique sur un lien
    const menuLinks = document.querySelectorAll('.site-menu-main a');
    menuLinks.forEach(link => {
        link.addEventListener('click', function() {
            setTimeout(closeMenu, 100);
        });
    });
    
    // Fermer avec Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && isMenuOpen) {
            closeMenu();
        }
    });
    
    // Fermer le menu si on redimensionne vers desktop
    window.addEventListener('resize', function() {
        if (!isMobile() && isMenuOpen) {
            closeMenu();
        }
    });
    
    console.log('📱 Menu mobile safe initialisé');
    
})();