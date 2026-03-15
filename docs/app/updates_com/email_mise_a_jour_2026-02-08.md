# Mise à jour Minipass - 8 février 2026

  lhgi@jfgoulet.com, hockeyestduquebec@gmail.com, kdresdell@gmail.com, kdresdell@gmail.com, mfdecoste@gmail.com


**Objet:** Mise à jour Minipass - 8 février 2026

---

Bonjour!

Je viens de faire une mise à jour importante de ton application Minipass. Beaucoup de nouveautés et d'améliorations cette fois-ci!

## Nouvelles fonctionnalités

- **Paiement par carte de crédit via Stripe** - Tu peux maintenant accepter les paiements par carte de crédit directement dans Minipass! Il suffit de créer un compte Stripe et d'entrer tes deux clés API dans les paramètres de l'application. Le guide complet de configuration est disponible ici : https://minipass.me/guides

- **Nouveau workflow d'inscription** - Le processus d'inscription a été complètement revu. Deux modes sont maintenant disponibles : **paiement d'abord** (le participant paie avant d'être inscrit) et **approbation d'abord** (tu approuves l'inscription avant le paiement). Le système gère aussi mieux les gros volumes (ex: 5 000 participants) incluant les cas de noms identiques.

- **Rapport financier intégré à la page d'activité** - Les données financières de chaque activité sont maintenant basées directement sur nos vues SQL comptables. Une seule source de vérité pour toutes les finances, que ce soit sur la page d'activité ou dans les rapports officiels.

## Améliorations

- **Page d'inscription redesignée** - Le formulaire d'inscription a été modernisé pour offrir une meilleure expérience autant sur ordinateur que sur mobile. Le logo Interac est maintenant affiché avec de meilleures indications de paiement.

- **Page d'activité améliorée** - L'interface de la page d'activité a été entièrement revue pour être plus conviviale et intuitive. Tout a été standardisé et validé, incluant les informations financières.

- **Tableau de bord - Cartes d'activités cliquables** - Les cartes d'activités sur le tableau de bord sont maintenant cliquables directement. Le bouton "Gérer" a été retiré pour simplifier la navigation.

- **Navigation améliorée** - Après avoir sauvegardé une activité, tu es maintenant redirigé vers le tableau de bord au lieu de rester sur la même page.

- **Gestion du mot de passe** - Tu peux maintenant réinitialiser et changer ton mot de passe directement dans la section Paramètres.

- **Photos et logos par défaut** - L'application affiche maintenant un visuel propre et professionnel même lorsqu'aucune photo de couverture ou logo d'organisation n'a été ajouté.

- **Localisation simplifiée** - Le processus pour trouver, sélectionner et modifier un emplacement a été grandement simplifié.

- **Système de courriels amélioré** - Les gabarits de courriels ont été nettoyés et simplifiés pour être plus clairs et faciles à maintenir. Nous avons maintenant 7 gabarits de courriels.

## Corrections

- **Courriel legacy sur la page d'inscription** - Correction d'un bug d'affichage du courriel legacy lorsque le mode "paiement d'abord" est activé.

- **Logo d'organisation par activité** - Correction d'un bug qui empêchait l'affichage correct du logo d'organisation selon l'activité.

- **Fonctionnalité de changement de mot de passe** - Correction de bugs liés au changement et à la réinitialisation du mot de passe.

- **Création de passeport depuis un paiement reçu** - Correction d'un bug qui empêchait la création d'un passeport à partir d'un paiement non-associé lorsque le champ téléphone ou courriel était laissé vide.

---

**Prochaine fonctionnalité**

Nous travaillons actuellement sur un module multilingue pour offrir l'application en français et en anglais. Restez à l'affût!

---

Si tu as des questions ou si tu remarques quoi que ce soit, fais-moi signe!

À bientôt,
[Ton nom]
