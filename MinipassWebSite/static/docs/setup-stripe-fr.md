# Configurer Stripe dans Minipass pour accepter les cartes de credit

*Dernière mise à jour: 8 février 2026*

## Table des matières

- [Prerequis](#prerequis)
- [Etape 1 : Creer un compte Stripe](#etape-1-creer-un-compte-stripe)
- [Etape 2 : Obtenir votre cle secrete](#etape-2-obtenir-votre-cle-secrete-secret-key)
- [Etape 3 : Configurer le Webhook](#etape-3-configurer-le-webhook)
- [Etape 4 : Entrer les cles dans Minipass](#etape-4-entrer-les-cles-dans-minipass)
- [Etape 5 : Activer la carte de credit sur une activite](#etape-5-activer-la-carte-de-credit-sur-une-activite)
- [Resultat : Ce que vos clients verront](#resultat-ce-que-vos-clients-verront)
- [Verification et test](#verification-et-test)
- [FAQ / Depannage](#faq-depannage)
- [Besoin d'aide?](#besoin-daide)

---

Minipass vous permet d'accepter les paiements par **carte de credit** via Stripe, en plus des virements Interac. Ce guide vous accompagne etape par etape pour configurer Stripe dans votre compte Minipass.

---

## Prerequis

- Un compte Minipass actif avec acces administrateur
- Une adresse courriel valide pour creer votre compte Stripe
- Votre sous-domaine Minipass (ex: `myorg_app.minipass.me`)

---

## Etape 1 : Creer un compte Stripe

1. Rendez-vous sur **[https://dashboard.stripe.com/register](https://dashboard.stripe.com/register)**

   ![Page d'inscription Stripe](/static/docs/images/stripe-signup-page.png)

2. Remplissez le formulaire :
   - **Email** : Votre adresse courriel professionnelle
   - **Full name** : Votre nom complet
   - **Password** : Un mot de passe securitaire
   - **Country** : Selectionnez **Canada**

3. Cliquez sur **Create account**

4. **Verifiez votre courriel** : Stripe vous enverra un lien de confirmation. Cliquez dessus pour activer votre compte.

5. **Completez la verification** : Stripe vous demandera des informations supplementaires sur votre organisation (type d'entreprise, adresse, informations bancaires pour recevoir les paiements). Suivez les instructions a l'ecran.

> **Note** : La verification complete de votre compte peut prendre 1 a 2 jours ouvrables. En attendant, vous pouvez utiliser le **mode test** pour configurer et tester l'integration.

---

## Etape 2 : Obtenir votre cle secrete (Secret Key)

Une fois connecte a votre tableau de bord Stripe :

1. Connectez-vous a **[https://dashboard.stripe.com](https://dashboard.stripe.com)**

   ![Page de connexion Stripe](/static/docs/images/stripe-login-page.png)

2. Dans le menu de gauche, cliquez sur **Developers** (Developpeurs)

3. Cliquez sur **API keys** (Cles API)

4. Vous verrez deux types de cles :
   - **Publishable key** (`pk_live_...`) — Vous n'avez **pas besoin** de cette cle
   - **Secret key** (`sk_live_...`) — C'est **cette cle** qu'il vous faut

5. Cliquez sur **Reveal live key** (ou **Reveal test key** si vous etes en mode test) pour afficher la cle secrete

6. **Copiez la cle secrete** qui commence par `sk_live_...` (ou `sk_test_...` en mode test)

> **Important** : Ne partagez jamais votre cle secrete. Elle donne acces a votre compte Stripe.

### Mode test vs Mode live

- **Mode test** (`sk_test_...`) : Pour tester sans vrais paiements. Les cartes de credit ne sont pas debitees.
- **Mode live** (`sk_live_...`) : Pour les vrais paiements. Les cartes sont debitees pour de vrai.

Vous pouvez basculer entre les deux modes avec le bouton **Test mode** en haut a droite du tableau de bord Stripe.

---

## Etape 3 : Configurer le Webhook

Le webhook permet a Stripe de notifier Minipass automatiquement lorsqu'un paiement est complete. C'est une etape essentielle.

1. Dans votre tableau de bord Stripe, allez dans **Developers** > **Webhooks**

   Ou rendez-vous directement sur : **[https://dashboard.stripe.com/webhooks](https://dashboard.stripe.com/webhooks)**

2. Cliquez sur **Add endpoint** (Ajouter un point de terminaison)

3. Remplissez les informations suivantes :

   | Champ | Valeur |
   |-------|--------|
   | **Endpoint URL** | `https://VOTRE-SOUS-DOMAINE_app.minipass.me/stripe/webhook` |
   | **Events to send** | `checkout.session.completed` |

   Par exemple, si votre sous-domaine est `myorg`, l'URL sera :
   ```
   https://myorg_app.minipass.me/stripe/webhook
   ```

4. Dans la section **Select events to listen to** :
   - Cliquez sur **+ Select events**
   - Recherchez `checkout.session.completed`
   - Cochez cet evenement
   - Cliquez sur **Add events**

5. Cliquez sur **Add endpoint** pour sauvegarder

6. Vous serez redirige vers la page du webhook. Cherchez la section **Signing secret** et cliquez sur **Reveal** pour afficher le secret

7. **Copiez le signing secret** qui commence par `whsec_...`

> **Astuce** : Si vous etes en mode test, assurez-vous de creer le webhook dans le mode test egalement (bouton **Test mode** active en haut a droite).

---

## Etape 4 : Entrer les cles dans Minipass

Maintenant que vous avez vos deux cles, il est temps de les entrer dans Minipass.

1. Connectez-vous a votre panneau d'administration Minipass

2. Allez dans **Settings** (Parametres)

3. Faites defiler jusqu'a la section **Credit Card Settings (Stripe)** et cliquez dessus pour l'ouvrir

   ![Section Stripe dans les parametres Minipass](/static/docs/images/minipass-stripe-settings.png)

4. Remplissez les deux champs :
   - **Secret Key** : Collez votre cle secrete (`sk_live_...` ou `sk_test_...`)
   - **Webhook Secret** : Collez votre secret de webhook (`whsec_...`)

5. Cliquez sur **Save Settings** en haut ou en bas de la page

---

## Etape 5 : Activer la carte de credit sur une activite

La configuration Stripe est maintenant terminee. Il reste a activer le paiement par carte de credit pour chaque activite ou vous souhaitez l'offrir.

1. Allez dans **Activities** et selectionnez l'activite a modifier (ou creez-en une nouvelle)

2. Dans la section **Signup Settings**, vous verrez maintenant l'option :

   **Accept credit card payments (Stripe)**

   ![Option carte de credit dans le formulaire d'activite](/static/docs/images/minipass-activity-credit-card.png)

3. **Activez** cette option (le bouton devient bleu)

4. Cliquez sur **Save** pour sauvegarder

> **Note** : Cette option n'apparait que si les cles Stripe sont configurees dans les parametres. Si vous ne voyez pas cette option, verifiez que l'etape 4 est completee.

---

## Resultat : Ce que vos clients verront

Lorsqu'un client s'inscrit a une activite avec le paiement par carte de credit active, il verra un choix entre deux methodes de paiement :

![Choix de methode de paiement lors de l'inscription](/static/docs/images/minipass-signup-payment-methods.png)

- **Interac** : Le client recevra les instructions de paiement par courriel
- **Carte de credit** : Le client sera redirige vers une page de paiement securisee Stripe (Stripe Checkout)

Apres un paiement par carte de credit reussi, le passeport du client est cree **automatiquement** — aucune action manuelle n'est requise de votre part.

---

## Verification et test

### Tester avec le mode test de Stripe

Avant de passer en mode live, nous vous recommandons de tester l'integration :

1. Assurez-vous d'utiliser les cles de **test** dans Minipass (`sk_test_...` et le webhook secret du mode test)

2. Creez une activite de test avec la carte de credit activee

3. Inscrivez-vous a l'activite comme si vous etiez un client

4. Selectionnez **Carte de credit** comme methode de paiement

5. Sur la page de paiement Stripe, utilisez cette carte de test :

   | Champ | Valeur |
   |-------|--------|
   | Numero de carte | `4242 4242 4242 4242` |
   | Date d'expiration | N'importe quelle date future (ex: `12/30`) |
   | CVC | N'importe quel code a 3 chiffres (ex: `123`) |

6. Confirmez le paiement

7. Verifiez que le passeport a ete cree automatiquement dans Minipass

### Passer en mode live

Une fois les tests reussis :

1. Dans Stripe, desactivez le **Test mode** pour passer en mode live
2. Copiez vos cles **live** (`sk_live_...`) depuis **Developers > API keys**
3. Creez un nouveau webhook en mode live avec la meme URL et le meme evenement
4. Copiez le nouveau **Webhook signing secret** (`whsec_...`)
5. Mettez a jour les cles dans les parametres Minipass
6. Cliquez sur **Save Settings**

---

## FAQ / Depannage

### Je ne vois pas l'option "Accept credit card payments" dans mon activite

Verifiez que vous avez entre les cles Stripe dans **Settings > Credit Card Settings (Stripe)** et que vous avez clique sur **Save Settings**.

### Le paiement par carte fonctionne en test mais pas en live

- Assurez-vous d'avoir remplace les cles de test par les cles live
- Verifiez que votre compte Stripe est entierement verifie
- Assurez-vous que le webhook en mode live est configure avec la bonne URL

### Le passeport n'est pas cree apres le paiement

- Verifiez que le webhook est correctement configure dans Stripe
- Verifiez que l'URL du webhook est exacte : `https://VOTRE-SOUS-DOMAINE_app.minipass.me/stripe/webhook`
- Verifiez que l'evenement `checkout.session.completed` est selectionne
- Consultez la page **Developers > Webhooks** dans Stripe pour voir s'il y a des erreurs de livraison

### Quels sont les frais Stripe?

Stripe facture des frais par transaction. Au Canada, les frais standards sont :
- **2.9% + 0.30$ CAD** par transaction reussie par carte de credit
- Aucuns frais mensuels ou frais de configuration

Consultez [https://stripe.com/ca/pricing](https://stripe.com/ca/pricing) pour les tarifs actuels.

### Puis-je utiliser Stripe et Interac en meme temps?

Oui! Lorsque la carte de credit est activee pour une activite, vos clients auront le choix entre les deux methodes de paiement. Vous n'avez pas a choisir l'une ou l'autre.

### Comment voir mes paiements Stripe?

Tous les paiements par carte de credit apparaissent dans :
- **Votre tableau de bord Stripe** : [https://dashboard.stripe.com/payments](https://dashboard.stripe.com/payments)
- **Minipass** : Les paiements par carte sont automatiquement enregistres et visibles dans les rapports financiers

---

## Besoin d'aide?

Si vous rencontrez des difficultes avec la configuration de Stripe, contactez le support Minipass a l'adresse **support@minipass.me**.
