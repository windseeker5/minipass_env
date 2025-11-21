# Guide Simple - Google Analytics 4 pour Minipass

## 🚀 Configuration Rapide (15 minutes max)

### Étape 1: Créer un compte GA4
1. Va sur [analytics.google.com](https://analytics.google.com)
2. Clique sur **"Commencer à mesurer"**
3. Entre les infos:
   - Nom du compte: `Minipass`
   - Nom de la propriété: `Minipass App`
   - Fuseau horaire: `(GMT-05:00) Heure de l'Est`
   - Devise: `CAD`
4. Sélectionne ton secteur et la taille (Petite entreprise)
5. Accepte les conditions

### Étape 2: Obtenir ton code de suivi
1. Dans GA4, va dans **Admin** (engrenage en bas)
2. Sous "Propriété", clique sur **"Flux de données"**
3. Clique sur **"Web"** → **"Ajouter un flux"**
4. Entre ton URL: `https://minipass.ca`
5. Nom du flux: `Minipass Website`
6. Clique **"Créer un flux"**

### Étape 3: Copier le code de suivi
Tu vas voir un code qui ressemble à ça:
```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-XXXXXXXXXX');
</script>
```

**⚠️ IMPORTANT**: Ton ID sera quelque chose comme `G-XXXXXXXXXX` - garde-le!

---

## 📝 Intégration avec Flask

### Option 1: Template de base (RECOMMANDÉ)
Dans ton fichier `templates/base.html` ou layout principal:

```html
<!DOCTYPE html>
<html>
<head>
    <!-- Google Analytics - METS ÇA EN PREMIER dans le <head> -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-XXXXXXXXXX');
    </script>
    
    <!-- Reste de ton head -->
    <title>{% block title %}Minipass{% endblock %}</title>
    <!-- autres meta tags, CSS, etc. -->
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

### Option 2: Avec variable d'environnement (PRODUCTION)
Dans ton `app.py`:
```python
import os
from flask import Flask, render_template

app = Flask(__name__)
app.config['GA_TRACKING_ID'] = os.environ.get('GA_TRACKING_ID', '')

@app.context_processor
def inject_ga():
    return {'GA_TRACKING_ID': app.config['GA_TRACKING_ID']}
```

Dans ton template:
```html
{% if GA_TRACKING_ID %}
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={{ GA_TRACKING_ID }}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', '{{ GA_TRACKING_ID }}');
</script>
{% endif %}
```

Dans ton `.env`:
```
GA_TRACKING_ID=G-XXXXXXXXXX
```

---

## 📊 Utilisation de Base - Les 3 trucs essentiels

### 1. Voir tes visiteurs en temps réel
- Va dans **Rapports** → **Temps réel**
- Tu vois instantanément qui est sur ton site MAINTENANT
- Utile pour tester que GA4 fonctionne!

### 2. Comprendre ton trafic (après 24h)
- Va dans **Rapports** → **Acquisition** → **Acquisition de trafic**
- Tu verras:
  - D'où viennent tes visiteurs (Google, direct, social, etc.)
  - Quelles pages ils visitent
  - Combien de temps ils restent

### 3. Tracker les conversions (inscriptions)
Pour tracker quand quelqu'un s'inscrit à Minipass:

Dans ton code Flask, après une inscription réussie:
```html
<!-- Sur la page de confirmation après inscription -->
<script>
  gtag('event', 'sign_up', {
    'method': 'email'
  });
</script>
```

Ou mieux, dans ton template de succès:
```html
{% if just_registered %}
<script>
  gtag('event', 'sign_up', {
    'value': 29.99,  // si tu veux tracker la valeur
    'currency': 'CAD'
  });
</script>
{% endif %}
```

---

## ✅ Vérifier que ça marche

1. **Test immédiat**:
   - Ouvre ton site
   - Va dans GA4 → **Temps réel**
   - Tu devrais te voir comme visiteur actif!

2. **Si ça marche pas**:
   - Vérifie que tu as bien mis le code dans `<head>`
   - Assure-toi que c'est le bon ID (G-XXXXXXXXXX)
   - Désactive ton ad blocker pour tester
   - Utilise Chrome DevTools → Network → filtre "collect" pour voir les requêtes

---

## 🎯 Métriques importantes pour un SaaS

Après quelques jours, regarde ces métriques:

1. **Utilisateurs** - Combien de personnes visitent
2. **Pages/Session** - Engagement (vise 2+)
3. **Taux de rebond** - % qui partent direct (vise <70%)
4. **Sources de trafic** - D'où viennent tes visiteurs
5. **Pages populaires** - Qu'est-ce qui intéresse les gens

---

## 💡 Tips Pro

1. **Exclure ton IP**:
   - Admin → Flux de données → Ton flux → Plus de paramètres
   - "Définir un filtre IP interne"
   - Ajoute ton IP pour ne pas fausser les stats

2. **Activer les signaux Google**:
   - Ça améliore tes données
   - Admin → Paramètres de la propriété → Collection de données

3. **Lier Search Console** (plus tard):
   - Pour voir quels mots-clés t'amènent du trafic Google

---

## 🚫 Erreurs à éviter

- ❌ Ne mets PAS le code dans le `<body>`
- ❌ N'oublie PAS le script async
- ❌ Ne track PAS de données personnelles (emails, noms)
- ❌ N'utilise PAS Universal Analytics (GA3) - c'est mort!

---

## 📱 Dashboard Mobile

Télécharge l'app "Google Analytics" sur ton phone pour checker tes stats n'importe où!

---

**C'est tout!** En 15 minutes tu as des analytics qui fonctionnent. Concentre-toi sur ton produit, et check tes stats une fois par semaine max au début. 

Questions? Les docs officielles sont ici: https://support.google.com/analytics/answer/9304153
