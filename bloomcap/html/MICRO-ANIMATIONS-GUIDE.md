# Guide d'intégration des Micro-animations

## 🚀 Installation rapide

1. **Ajouter les fichiers CSS et JS dans votre template HTML :**
```html
<!-- Dans le <head> -->
<link rel="stylesheet" href="css/micro-animations.css">

<!-- Avant la fermeture du </body> -->
<script src="js/micro-animations.js"></script>
```

## 📋 Classes disponibles

### Animations de base
- `.reveal-fade` - Apparition en fondu
- `.reveal-up` - Glissement vers le haut
- `.reveal-left` - Glissement depuis la gauche
- `.reveal-right` - Glissement depuis la droite
- `.reveal-scale` - Apparition avec zoom

### Classes modificateurs
- `.duration-200` - Animation de 200ms
- `.duration-250` - Animation de 250ms
- `.duration-300` - Animation de 300ms (par défaut)
- `.delay-100` - Délai de 100ms
- `.delay-200` - Délai de 200ms
- `.delay-300` - Délai de 300ms
- `.stagger-children` - Applique un délai progressif aux enfants

## 💡 Exemples d'utilisation

### Sections principales
```html
<!-- Hero section -->
<div class="hero-section reveal-fade">
  <h1 class="reveal-up delay-200">Titre principal</h1>
  <p class="reveal-up delay-300">Sous-titre</p>
</div>

<!-- Section avec contenu -->
<section class="container reveal-fade">
  <h2 class="text-center reveal-up">Nos services</h2>
</section>
```

### Cartes et grilles
```html
<!-- Grille de cartes avec stagger -->
<div class="row stagger-children">
  <div class="col-md-4 reveal-up">
    <div class="card">Carte 1</div>
  </div>
  <div class="col-md-4 reveal-up">
    <div class="card">Carte 2</div>
  </div>
  <div class="col-md-4 reveal-up">
    <div class="card">Carte 3</div>
  </div>
</div>
```

### Images et médias
```html
<!-- Image avec animation -->
<div class="image-wrapper reveal-scale">
  <img src="image.jpg" alt="Description">
</div>

<!-- Vidéo avec slide -->
<div class="video-container reveal-left">
  <video src="video.mp4"></video>
</div>
```

### Formulaires
```html
<!-- Formulaire avec animations -->
<form class="contact-form">
  <div class="form-group reveal-up">
    <input type="text" placeholder="Nom">
  </div>
  <div class="form-group reveal-up delay-100">
    <input type="email" placeholder="Email">
  </div>
  <button class="reveal-fade delay-200">Envoyer</button>
</form>
```

## 🎮 Contrôle par JavaScript

```javascript
// Désactiver toutes les animations
MicroAnimations.disable();

// Activer les animations
MicroAnimations.enable();

// Basculer on/off
MicroAnimations.toggle();

// Réinitialiser un élément spécifique
const element = document.querySelector('.my-element');
MicroAnimations.reset(element);

// Révéler immédiatement
MicroAnimations.reveal(element);
```

## ⚡ Bonnes pratiques

1. **Ne pas surcharger** - Utilisez les animations avec parcimonie
2. **Hiérarchie** - Animez d'abord les titres, puis le contenu
3. **Performance** - Évitez d'animer plus de 10-15 éléments simultanément
4. **Mobile** - Les animations sont automatiquement réduites sur mobile
5. **Accessibilité** - Respecte automatiquement `prefers-reduced-motion`

## 🔧 Personnalisation

Pour modifier les paramètres par défaut, éditez le fichier `micro-animations.js` :
```javascript
const CONFIG = {
  threshold: 0.2,      // Modifier le seuil de déclenchement (0-1)
  rootMargin: '0px',   // Ajouter une marge de déclenchement
  // ...
};
```

## ✅ Checklist d'intégration

- [ ] Ajouter les fichiers CSS/JS
- [ ] Ajouter les classes `.reveal-*` aux éléments souhaités
- [ ] Tester sur mobile et desktop
- [ ] Vérifier avec `prefers-reduced-motion` activé
- [ ] Ajuster les délais si nécessaire