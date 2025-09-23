# Guide de résolution des conflits d'animations Scroll Reveal

## Problèmes identifiés

### 1. Fichier manquant
- `js/micro-animations.js` était référencé dans index.html mais n'existait pas
- **Résolu**: Fichier créé avec fonctionnalités unifiées

### 2. Conflits de classes CSS
- `mobile-scroll-animations.js` utilise la classe `visible`
- `scroll-reveal-mobile.js` utilise la classe `is-visible`
- **Résolu**: Le nouveau `micro-animations.js` supporte les deux classes

### 3. Duplication de scripts
Vous avez actuellement 3 scripts qui font la même chose:
- `mobile-scroll-animations.js` (mobile uniquement, classe `visible`)
- `scroll-reveal-mobile.js` (tous appareils, classe `is-visible`)
- `micro-animations.js` (nouveau, unifié, supporte les deux)

## Solution recommandée

### Option 1: Utiliser uniquement micro-animations.js (RECOMMANDÉ)

1. **Modifier index.html** - Remplacer les lignes 3255-3260:
```html
<!-- Supprimer ces lignes -->
<!-- <script src="js/mobile-scroll-animations.js"></script> -->
<!-- <script src="js/scroll-reveal-mobile.js"></script> -->

<!-- Garder uniquement -->
<script src="js/micro-animations.js"></script>
```

2. **Vérifier les classes CSS** dans index.html:
   - Les classes `reveal-*` fonctionnent maintenant avec `micro-animations.js`
   - Les anciennes classes continuent de fonctionner

### Option 2: Corriger les scripts existants

Si vous préférez garder les scripts séparés:

1. **Modifier mobile-scroll-animations.js** ligne 16:
```javascript
// Changer
animationClass: 'visible',
// En
animationClass: 'is-visible',
```

2. **Ajouter la compatibilité** dans scroll-reveal-mobile.js après ligne 79:
```javascript
// Ajouter après entry.target.classList.add('is-visible');
if (window.innerWidth <= 768) {
    entry.target.classList.add('visible');
}
```

## Test des animations

1. Ouvrir `test-animations.html` dans votre navigateur
2. Scroller pour voir les différentes animations
3. Vérifier la console pour les logs d'animation
4. Le panneau de debug affiche le nombre d'éléments animés

## Classes d'animation disponibles

### Classes de base
- `.reveal` - Animation par défaut (fade in)
- `.reveal-fade` - Fade in simple
- `.reveal-up` - Slide depuis le bas
- `.reveal-left` - Slide depuis la gauche
- `.reveal-right` - Slide depuis la droite
- `.reveal-scale` - Scale in
- `.reveal-title` - Spécial pour les titres

### Classes de délai
- `.reveal-delay-1` - Délai 100ms (50ms mobile)
- `.reveal-delay-2` - Délai 200ms (100ms mobile)
- `.reveal-delay-3` - Délai 300ms (150ms mobile)
- `.reveal-delay-4` - Délai 400ms (200ms mobile)

### Classes spéciales
- `.reveal-stagger` - Animation échelonnée pour les enfants
- `.animate-on-scroll` - Classe générique pour tout élément

## Optimisations mobile

- Animations plus rapides sur mobile (200ms vs 300ms)
- Distances de translation réduites (20px vs 30px)
- Délais plus courts
- Support du touch feedback
- Désactivation pendant le scroll rapide

## API JavaScript

Le nouveau `micro-animations.js` expose une API globale:

```javascript
// Révéler un élément manuellement
MicroAnimations.reveal(element);

// Cacher un élément
MicroAnimations.hide(element);

// Réinitialiser toutes les animations
MicroAnimations.reset();

// Configurer les options
MicroAnimations.configure({
    threshold: 0.2,
    animateOnce: false
});
```

## Recommandations

1. **Utilisez `micro-animations.js`** - Il unifie toutes les fonctionnalités
2. **Supprimez les scripts redondants** pour éviter les conflits
3. **Testez sur mobile et desktop** avec test-animations.html
4. **Utilisez les classes reveal-*** pour de nouvelles animations
5. **Gardez mobile-animations.css** si vous voulez des animations spécifiques mobile

## Dépannage

Si les animations ne fonctionnent pas:

1. Vérifier la console pour les erreurs
2. S'assurer que les classes CSS sont correctes
3. Vérifier que le script est bien chargé
4. Tester avec `test-animations.html`
5. Utiliser l'API pour forcer une animation: `MicroAnimations.reveal(element)`