# Mise à jour Minipass - 30 mai 2026

lhgi@jfgoulet.com, hockeyestduquebec@gmail.com, kdresdell@gmail.com, mfdecoste@gmail.com

**Objet:** Mise à jour Minipass - 30 mai 2026

---

Bonjour!

Voici ce qui a changé depuis le 5 avril.

## Ce qui a été corrigé

- **Changement de plan (suite)** — La synchronisation entre Stripe, la base de données et le panneau administratif lors d'un changement de plan (mensuel ↔ annuel, annulation) a été corrigée en profondeur. Plusieurs points de sécurité ont également été renforcés.

- **Recherche de passeport** — Un bug empêchait la recherche et la lecture correcte d'un passeport dans certains cas. C'est maintenant réglé.

- **Paiements Interac simultanés** — Deux paiements Interac valides reçus en même temps n'étaient plus reconnus correctement. Le système valide maintenant par identifiant unique du courriel plutôt que par un délai de 5 minutes.

- **Envoi d'annonces à un grand groupe** — Un bug empêchait l'envoi d'une annonce ou d'une diffusion à un large groupe de participants. C'est maintenant réglé.

- **Fausses entrées dans la boîte de réception** — Des notifications Interac dupliquées créaient parfois de fausses entrées dans la boîte de réception. Ce comportement est corrigé.

---

Rien à faire de ta part. Si tu remarques quoi que ce soit d'anormal, fais-le moi savoir.

À bientôt,
Ken
