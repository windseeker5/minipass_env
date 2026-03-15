# Mise à jour Minipass - 8 mars 2026

lhgi@jfgoulet.com, hockeyestduquebec@gmail.com, kdresdell@gmail.com, mfdecoste@gmail.com


**Objet:** Mise à jour Minipass - 8 mars 2026

---

Bonjour!

Mise à jour courte cette semaine — pas de nouvelles fonctionnalités, mais une semaine chargée du côté de l'infrastructure. Je voulais quand même te tenir au courant.

## Nouvelle fonctionnalité

- **Surveillance des courriels échoués + renvoi en un clic** — L'application surveille maintenant chaque courriel envoyé à tes participants. Si un courriel échoue (ex. : problème de connexion au serveur de courriel), un badge rouge apparaît directement dans le menu de navigation pour t'alerter. En cliquant dessus, tu arrives sur la page du journal d'activité, filtrée sur les échecs, où tu peux renvoyer chaque courriel individuellement d'un seul clic — ou simplement le supprimer si ce n'est plus pertinent. Plus aucun courriel manqué sans que tu le saches.

## Travaux d'infrastructure (en coulisses)

- **Incident serveur (VPS)** — Le serveur principal a subi une interruption en début de semaine. Le service a été rétabli rapidement. Un guide de récupération en cas de désastre a été rédigé pour que ce type d'incident soit encore mieux géré à l'avenir.

- **Système de courriel** — Suite à l'incident, le serveur de courriel a nécessité des corrections. Des outils de diagnostic ont été ajoutés pour identifier et corriger les problèmes de connectivité plus rapidement. La livraison des courriels est maintenant de retour à la normale.

- **Déploiement de nouveaux clients** — Un problème de réseau affectant les nouveaux conteneurs clients a été identifié et corrigé. Les nouveaux déploiements sont maintenant validés automatiquement pour s'assurer que la communication entre services fonctionne correctement dès le départ.

- **Changements de plan Stripe** — La gestion des changements d'abonnement (ex. : passage d'un plan à un autre) est maintenant traitée automatiquement et de façon fiable côté serveur.

---

Rien à faire de ta part — tout est transparent. Mais si tu remarques quoi que ce soit d'anormal dans l'application, fais-le moi savoir.

La prochaine mise à jour devrait revenir sur des améliorations plus visibles pour toi.

À bientôt,
[Ton nom]
