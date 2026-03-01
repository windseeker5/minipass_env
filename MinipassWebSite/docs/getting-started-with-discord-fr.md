# Débuter avec Discord pour les gestionnaires d'activités Minipass

Ce guide vous accompagne pas à pas dans la configuration de Discord pour votre activité Minipass — de la création d'un compte gratuit jusqu'à l'envoi d'annonces directement dans votre canal communautaire.

---

## Qu'est-ce que Discord et pourquoi l'utiliser ?

Discord est une plateforme de communication gratuite qui vous permet de créer un espace communautaire privé (appelé un **serveur**) pour les participants à votre activité. Une fois connecté à Minipass, chaque annonce que vous envoyez sera diffusée simultanément à deux endroits :

- **Par courriel** — à chaque participant inscrit
- **Dans votre canal Discord** — sous forme d'un message formaté visible par tous les membres du serveur

C'est particulièrement utile pour les ligues sportives, les cours de fitness et les activités récurrentes où les participants souhaitent rester en contact entre les séances.

---

## Étape 1 — Créer un compte Discord

Si vous n'avez pas encore de compte Discord, rendez-vous sur [discord.com](https://discord.com) et cliquez sur **Ouvrir Discord dans votre navigateur** ou téléchargez l'application.

![Page d'accueil Discord](images/discord/01-discord-homepage.png)

Vous serez redirigé vers la page de création de compte. Remplissez les champs suivants :
- **Adresse courriel**
- **Nom d'affichage** (visible par les autres membres)
- **Nom d'utilisateur** (votre identifiant unique)
- **Mot de passe**
- **Date de naissance**

Cliquez ensuite sur **Créer un compte**.

![Créer un compte Discord](images/discord/02-discord-create-account.png)

> **Conseil :** Utilisez l'adresse courriel de votre organisation pour faciliter la gestion. Les comptes Discord sont gratuits — aucune carte de crédit requise.

---

## Étape 2 — Créer un serveur pour votre activité

Un **serveur** est votre espace communautaire privé. Pensez-y comme à un vestiaire virtuel — vous décidez qui y entre et quels canaux y existent.

1. Dans la barre latérale gauche de Discord, cliquez sur l'icône **+** (Ajouter un serveur)
2. Choisissez **Créer le mien**
3. Sélectionnez **Pour un club ou une communauté** (ou ignorez la question)
4. Donnez un nom à votre serveur — par ex. `Hockey Fondation LHGI` ou `Club de surf du dimanche`
5. Cliquez sur **Créer**

Votre serveur dispose maintenant d'un canal `#général` par défaut. Vous pourrez ajouter d'autres canaux plus tard.

> **Bonne pratique :** Créez un canal dédié `#annonces` et configurez-le pour que seuls les administrateurs puissent y publier. Cela garde vos annonces claires et faciles à retrouver.

---

## Étape 3 — Obtenir l'URL du webhook depuis Discord

Un **webhook** est une URL spéciale qui permet à Minipass de publier des messages directement dans votre canal — sans compte robot requis.

**Pour créer un webhook :**

1. Dans votre serveur Discord, faites un clic droit sur le canal souhaité (p. ex. `#annonces`)
2. Cliquez sur **Modifier le canal**
3. Allez dans **Intégrations** → **Webhooks**
4. Cliquez sur **Nouveau webhook**
5. Donnez-lui un nom (p. ex. `Minipass`)
6. Cliquez sur **Copier l'URL du webhook**

Gardez cette URL à portée de main — vous la collerez dans Minipass à l'étape suivante.

> **Important :** Traitez l'URL de votre webhook comme un mot de passe. Toute personne possédant cette URL peut publier dans votre canal. Ne la partagez pas publiquement.

---

## Étape 4 — Ajouter l'URL du webhook à votre activité Minipass

Connectez-vous à votre panneau d'administration Minipass et accédez à **Modifier l'activité** pour l'activité que vous souhaitez connecter.

![Connexion Minipass](images/discord/03-minipass-login.png)

Depuis votre tableau de bord, cliquez sur la carte de l'activité ou naviguez vers **Activités** dans la barre latérale.

![Tableau de bord Minipass](images/discord/04-minipass-dashboard.png)

Faites défiler jusqu'à la section **Paramètres d'inscription**. Vous y trouverez le paramètre d'intégration Discord :

1. **Activez** le bouton bascule *« Cette activité a un serveur Discord »*
2. Collez votre **URL de webhook** dans le champ prévu
3. Collez facultativement votre **lien d'invitation Discord** afin que les participants puissent rejoindre votre serveur directement depuis leur courriel de confirmation
4. Cliquez sur le bouton **Test** pour envoyer un message de test dans votre canal et vérifier que tout fonctionne
5. Cliquez sur **Enregistrer**

![Paramètres Discord dans le formulaire d'activité Minipass](images/discord/05-minipass-activity-discord-section.png)

> **Où trouver votre lien d'invitation :**
> Dans Discord → clic droit sur le nom de votre serveur → **Inviter des personnes** → **Copier le lien**.
> Réglez l'invitation sur **N'expire jamais** et **Utilisations illimitées** pour la partager une seule fois sans jamais avoir à la renouveler.

---

## Étape 5 — Envoyer une annonce par courriel et sur Discord

Une fois votre webhook configuré, chaque annonce envoyée depuis Minipass sera publiée en option sur Discord au même moment.

Depuis le **Tableau de bord de l'activité**, cliquez sur **Actions** → **Envoyer une annonce**.

![Tableau de bord de l'activité Minipass](images/discord/06-minipass-activity-dashboard.png)

Dans la fenêtre d'annonce, vous verrez :

- **Destinataires** — choisissez qui reçoit le courriel (Tous, Payés seulement, Non payés seulement ou par type de passeport)
- **Publier aussi dans le canal Discord** — ce bouton est activé par défaut lorsqu'un webhook est configuré ; désactivez-le si vous souhaitez envoyer uniquement par courriel
- **Sujet** — le titre de votre message
- **Message** — le corps de votre annonce (supporte le gras, l'italique, les listes à puces et les liens)

Cliquez sur **Envoyer** et votre message est transmis à tous les participants sélectionnés par courriel ET apparaît dans votre canal Discord sous forme d'un encart formaté.

![Fenêtre d'annonce avec le bouton Discord](images/discord/07-minipass-announcement-modal.png)

---

## Ce que vos participants verront sur Discord

Lorsque vous envoyez une annonce, Discord l'affiche sous forme de carte dans votre canal :

- **Titre** — l'objet de votre annonce
- **Corps** — le texte de votre message (le formatage HTML est converti en markdown Discord)
- **Pied de page** — le nom de votre activité

Tous les membres de votre serveur Discord qui suivent le canal seront notifiés instantanément — aucun courriel requis de leur côté.

---

## Bonnes pratiques

| À faire | Pourquoi |
|---------|----------|
| Créer un canal `#annonces` | Sépare les mises à jour de l'activité des échanges informels |
| Configurer `#annonces` en lecture seule pour les membres | Évite le bruit ; seul votre webhook (Minipass) peut y publier |
| Utiliser un lien d'invitation permanent et illimité | À partager une seule fois dans le courriel de confirmation — les participants peuvent rejoindre à tout moment |
| Tester le webhook après l'enregistrement | Confirme que l'URL est valide avant d'envoyer une vraie annonce |
| Garder l'URL du webhook confidentielle | Traitez-la comme un mot de passe — ne la collez pas dans des canaux publics ou des courriels |
| Retirer le webhook avant d'archiver une activité | Évite l'accumulation de webhooks inutilisés dans votre serveur Discord |

---

## Dépannage

**Mon message de test n'apparaît pas dans Discord**
- Vérifiez que vous avez collé l'URL complète du webhook (elle commence par `https://discord.com/api/webhooks/...`)
- Assurez-vous que le webhook est activé dans Discord : Canal → Modifier → Intégrations → Webhooks
- Le webhook doit pointer vers le bon serveur et le bon canal

**Le bouton Discord n'apparaît pas dans ma fenêtre d'annonce**
- Le bouton n'apparaît que lorsqu'une URL de webhook est enregistrée sur l'activité. Allez dans **Modifier l'activité** et ajoutez d'abord l'URL du webhook.

**Les participants ne peuvent pas rejoindre mon serveur Discord**
- Vérifiez que le lien d'invitation n'a pas expiré. Dans Discord, allez dans **Paramètres du serveur → Invitations** et confirmez que le lien est toujours actif.
- Réglez l'expiration sur **Jamais** pour éviter ce problème à l'avenir.

---

## Résumé

| Étape | Ce que vous faites |
|-------|-------------------|
| 1 | Créer un compte Discord gratuit sur discord.com |
| 2 | Créer un serveur Discord pour votre activité |
| 3 | Copier l'URL du webhook depuis les paramètres d'intégration de votre canal |
| 4 | Coller l'URL du webhook dans votre activité Minipass et cliquer sur Test |
| 5 | Envoyer des annonces — elles partent par courriel ET sur Discord simultanément |

C'est tout. Votre communauté dispose maintenant d'un canal en temps réel où les annonces apparaissent dès que vous les envoyez depuis Minipass.
