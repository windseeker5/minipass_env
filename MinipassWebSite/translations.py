# translations.py — All translatable text for minipass.me (FR + EN)
# Marie-France: edit English text here. Ken: update structure when pages change.

TRANSLATIONS = {
    'fr': {
        'lang_code': 'fr-CA',
        'og_locale': 'fr_CA',
        'alt_lang_label': 'EN',

        # ── Meta (defaults for base.html) ──
        'meta': {
            'title': 'minipass \u2014 Gestion de ligues et d\u2019activit\u00e9s avec Interac | Canada',
            'description': 'minipass automatise les inscriptions, paiements Interac, passeports num\u00e9riques et comptabilit\u00e9 pour vos ligues sportives et cours. Fait au Canada. D\u00e8s 10$/mois.',
            'og_title': 'minipass \u2014 Gestion de ligues avec Interac',
            'og_desc': 'Automatisez inscriptions, jumelage de virements Interac et passeports num\u00e9riques. Plateforme canadienne. D\u00e8s 10$/mois.',
        },

        # ── Navigation ──
        'nav': {
            'home': 'Accueil',
            'features': 'Fonctionnalit\u00e9s',
            'about': '\u00c0 propos de nous',
            'guides': 'Guides',
            'subscribe': 'Commencer',
        },

        # ── Footer ──
        'footer': {
            'tagline': 'Tu cr\u00e9es ton activit\u00e9. minipass s\u2019occupe du reste.',
            'contact': 'Contact',
            'quick_links': 'Quick Links',
            'copyright': '\u00a9 2025 minipass.me, fait avec \u2764\ufe0f au Canada',
        },

        # ── Home page ──
        'home': {
            'meta_title': 'minipass \u2014 Inscriptions, paiements Interac et boutique en ligne pour ligues et cours',
            'meta_desc': 'Tu cr\u00e9es ton activit\u00e9, minipass s\u2019occupe du reste : inscriptions en ligne, paiements Interac d\u00e9tect\u00e9s automatiquement, passeports num\u00e9riques, boutique et finances. D\u00e8s 10\u00a0$ par mois.',

            # Hero
            'hero_subtitle': 'Pour les ligues, les \u00e9coles, les cours et les organismes',
            'hero_title_prefix': 'Tu cr\u00e9es tes ',
            'hero_word1': 'cours',
            'hero_word2': 'ligues',
            'hero_word3': '\u00e9v\u00e9nements',
            'hero_and': 'et',
            'hero_title_end': '. minipass s\u2019occupe du reste.',
            'hero_desc': 'Inscriptions en ligne, paiements Interac d\u00e9tect\u00e9s automatiquement, passeports num\u00e9riques, boutique en ligne et finances toujours \u00e0 jour. D\u00e8s 10\u00a0$ par\u00a0mois.',
            'hero_video_url': 'https://www.youtube.com/watch?v=eftLJ7hTPPs',
            'hero_btn_discover': 'D\u00e9couvrir',
            'hero_btn_plans': 'Choisir mon forfait',
            'hero_btn_video': 'Voir minipass en 1 minute',

            # Social proof
            'social_proof_label': 'ILS NOUS FONT CONFIANCE',
            'testimonial1_name': 'Jean-Fran\u00e7ois Goulet',
            'testimonial1_role': 'Co-administrateur de la FLHGI',
            'testimonial1_text': 'Avec minipass, nous avons enfin une plateforme qui nous permet de nous concentrer sur nos r\u00e9sultats plut\u00f4t que sur la paperasse. Son intuitivit\u00e9 et ses tableaux de bord budg\u00e9taires ont simplifi\u00e9 nos suivis de <strong>75 %</strong>. C\u2019est devenu l\u2019alli\u00e9 indispensable pour la coordination rapide et simple de tous les programmes de financement de notre Fondation.',
            'testimonial1_short': 'Avec minipass, nous avons enfin une plateforme qui nous permet de nous concentrer sur nos r\u00e9sultats plut\u00f4t que sur la paperasse. Son intuitivit\u00e9 et ses tableaux de bord budg\u00e9taires ont simplifi\u00e9 nos suivis de <strong>75\u00a0%</strong>.',
            'testimonial2_name': 'Marc Tremblay',
            'testimonial2_role': 'Entra\u00eeneur hockey, Acad\u00e9mie Tremblay',
            'testimonial2_text': 'Avant minipass, je passais mes fins de semaine \u00e0 v\u00e9rifier les virements Interac un par un. Maintenant, tout est jumel\u00e9 automatiquement. Mes parents re\u00e7oivent leur passeport QR par courriel et je me concentre sur la glace, pas sur les chiffriers.',
            'testimonial3_name': 'Sophie Lavoie',
            'testimonial3_role': 'Instructrice yoga, Studio Lumi\u00e8re',
            'testimonial3_text': 'J\u2019avais essay\u00e9 trois autres plateformes avant minipass. Aucune comprenait Interac. Mes clientes s\u2019inscrivent en 2 minutes depuis leur t\u00e9l\u00e9phone et je re\u00e7ois la confirmation automatiquement. La gestion de mes cours n\u2019a jamais \u00e9t\u00e9 aussi simple.',

            # How it works
            'how_label': 'SIMPLE COMME BONJOUR',
            'how_title': 'Comment \u00e7a marche',
            'step1_title': 'Cr\u00e9e ton activit\u00e9',
            'step1_text': 'Ta ligue, ton cours ou ton \u00e9v\u00e9nement, en quelques minutes : le prix, les places et les dates.',
            'step2_title': 'Partage ton lien',
            'step2_text': 'Tes participants s\u2019inscrivent depuis leur t\u00e9l\u00e9phone et paient par Interac ou par carte.',
            'step3_title': 'Pilote automatique',
            'step3_text': 'Les paiements sont d\u00e9tect\u00e9s, les passeports envoy\u00e9s et tes finances mises \u00e0 jour. Tu n\u2019as rien \u00e0 faire.',

            # Features
            'features_label': 'FONCTIONNALIT\u00c9S',
            'features_title': 'Tout ce que minipass fait pour toi',
            'feat1_title': 'Paiements d\u00e9tect\u00e9s automatiquement',
            'feat1_text': 'Chaque virement Interac re\u00e7u est reconnu et associ\u00e9 \u00e0 la bonne personne. La carte de cr\u00e9dit est accept\u00e9e aussi.',
            'feat2_title': 'Inscriptions en ligne',
            'feat2_text': 'Partage un lien ou un code QR. Tes participants s\u2019inscrivent depuis leur t\u00e9l\u00e9phone, sans cr\u00e9er de compte.',
            'feat3_title': 'Passeport num\u00e9rique',
            'feat3_text': 'Chaque participant re\u00e7oit son passeport avec code QR. \u00c0 chaque pr\u00e9sence, il re\u00e7oit une confirmation et son passeport se met \u00e0 jour.',
            'feat4_title': 'Boutique en ligne',
            'feat4_text': 'Vends tes activit\u00e9s et tes produits, comme des chandails ou des billets, au m\u00eame endroit. Forfaits Club et Organisation.',
            'feat5_title': 'Finances \u00e0 jour',
            'feat5_text': 'Revenus, d\u00e9penses et re\u00e7us par activit\u00e9, mis \u00e0 jour \u00e0 chaque paiement. Export pour ton comptable.',
            'feat6_title': 'Aussi inclus',
            'feat6_text': 'R\u00e9servation de s\u00e9ances en ligne, courriels et rappels automatiques. Avec Club et Organisation : sondages et Wayne, ton assistant qui r\u00e9pond \u00e0 tes questions.',

            # Pricing
            'pricing_label': 'FORFAITS',
            'pricing_title': 'Un prix par mois. Sans surprise.',
            'pricing_monthly': 'Mensuel',
            'pricing_annual': 'Annuel',
            'pricing_save': '\u00c9CONOMISEZ 50%',
            'pricing_per_month': '/ mois',
            'pricing_annual_plan': 'Forfait annuel',
            'pricing_monthly_plan': 'Forfait mensuel',
            'pricing_no_contract': 'Aucuns frais cach\u00e9s. Sans contrat. Annule quand tu veux.',

            # Plan: Solo
            'solo_name': 'Solo',
            'solo_desc': 'Un coach ou un instructeur, une activit\u00e9',
            'solo_activity': '1',
            'solo_activity_label': 'activit\u00e9',

            # Plan: Club
            'club_name': 'Club',
            'club_desc': 'Une ligue avec divisions, une \u00e9cole avec plusieurs cours',
            'club_activity': '15',
            'club_activity_label': 'activit\u00e9s',

            # Plan: Organisation
            'org_name': 'Organisation',
            'org_desc': 'Un organisme ou une fondation avec plusieurs programmes',
            'org_activity': '100',
            'org_activity_label': 'activit\u00e9s',

            # Pricing features list
            'plan_activity_suffix': '(ligue, cours ou \u00e9v\u00e9nement)',
            'plan_tooltip': '1 activit\u00e9 = 1 ligue, cours ou \u00e9v\u00e9nement complet, s\u00e9ances illimit\u00e9es.',
            'plan_tooltip_example': 'Tu as un code d\u2019invitation? Choisis ton forfait et entre ton code \u00e0 l\u2019\u00e9tape suivante.',
            'plan_feat_participants': 'Participants et passeports illimit\u00e9s',
            'plan_feat_registrations': 'Inscriptions et paiements Interac ou carte',
            'plan_feat_attendance': 'R\u00e9servation de s\u00e9ances',
            'plan_feat_finance': 'Finances \u00e0 jour',
            'plan_feat_survey': 'Courriels automatiques',
            'plan_feat_ai': 'Support en fran\u00e7ais',
            'plan_plus': '+ Boutique en ligne, sondages et Wayne',
            'plan_btn': 'Choisir ce forfait',

            # Newsletter
            'newsletter_label': 'INFOLETTRE GRATUITE',
            'newsletter_title': 'Sois le premier inform\u00e9\u00a0!',
            'newsletter_placeholder': 'ton@courriel.com',
            'newsletter_btn': 'Je m\u2019abonne',
            'newsletter_success': 'Tu es maintenant inscrit! Tu recevras le prochain article bientot.',
            'newsletter_error': 'Une erreur est survenue. Essaie de nouveau.',

            # Blog section
            'blog_label': 'NOTRE BLOG',
            'blog_title': 'Nos derniers articles',
            'blog_see_all': 'Voir tous les articles',

            # Modal
            'modal_complete': 'Compl\u00e9tez votre abonnement',
            'modal_app_name_label': 'Saisissez le nom souhait\u00e9 pour votre application',
            'modal_app_name_placeholder': 'monprojet',
            'modal_app_name_desc': 'Votre nom souhait\u00e9:',
            'modal_app_name_available': 'est disponible',
            'modal_app_name_taken': 'Ce sous-domaine est d\u00e9j\u00e0 pris',
            'modal_app_name_invalid': 'Doit contenir au moins 3 caract\u00e8res (lettres et chiffres en minuscules) et aucun espace ou caract\u00e8res sp\u00e9ciaux',
            'modal_app_name_error': 'Erreur lors de la v\u00e9rification du sous-domaine',
            'modal_org_label': 'Saisissez le nom de votre organisation',
            'modal_org_placeholder': 'Mon Entreprise ex:Fondation XYZ',
            'modal_org_desc': 'Cette information appara\u00eetra dans votre application et les communications \u00e0 vos participants',
            'modal_email_label': 'Saisissez l\u2019adresse courriel \u00e0 utiliser pour administrer votre minipass.',
            'modal_email_placeholder': 'admin@monentreprise.com',
            'modal_email_desc': 'Cette adresse courriel est importante. Elle sera votre identifiant administrateur de votre minipass.',
            'modal_promo_toggle': 'Vous avez un code promotionnel ?',
            'modal_promo_placeholder': 'CODE PROMO',
            'modal_promo_apply': 'Appliquer',
            'modal_promo_checking': 'V\u00e9rification\u2026',
            'modal_promo_valid': 'Code valide ! Acc\u00e8s gratuit activ\u00e9.',
            'modal_promo_invalid': 'Code invalide',
            'modal_promo_error': 'Erreur de v\u00e9rification',
            'modal_submit': 'Proc\u00e9der au paiement',
            'modal_submit_promo': 'Activer mon code',
            'modal_billing_annual': 'Facturation annuelle',
            'modal_billing_monthly': 'Facturation mensuelle',
            'modal_billing_total': 'total',
            'modal_savings': '\u00c9conomisez 50%',
            'modal_policy': 'Consultez notre',
            'modal_policy_link': 'politique d\u2019abonnement',
            'modal_forfait_solo': 'Forfait Solo',
            'modal_forfait_club': 'Forfait Club',
            'modal_forfait_org': 'Forfait Organisation',
        },

        # ── About page ──
        'about': {
            'meta_title': '\u00c0 propos de minipass \u2014 Plateforme canadienne de gestion de ligues et cours',
            'meta_desc': 'D\u00e9couvrez l\u2019\u00e9quipe derri\u00e8re minipass, la plateforme canadienne qui automatise la gestion des ligues sportives, paiements Interac et inscriptions en ligne.',

            # Section 1
            's1_label': 'La petite histoire',
            's1_title': 'Le 20$ qui a tout d\u00e9clench\u00e9',
            's1_p1': 'Un dimanche matin, en comptant ses billets de rempla\u00e7ants au hockey, Ken r\u00e9alise qu\u2019il manque vingt dollars et que la petite caisse ne balance toujours pas. Entre les passes de saison, les paiements en cash et par Interac, la gestion financi\u00e8re \u00e9tait devenue chaotique. Convaincu qu\u2019une application simple devait exister pour r\u00e9gler ce probl\u00e8me, il d\u00e9couvre rapidement que les options disponibles sont soit trop complexes, soit trop co\u00fbteuses, soit mal con\u00e7ues... ou les trois \u00e0 la fois!',
            's1_p2': 'Le geek techno se r\u00e9veille alors en lui. Une \u00e9bauche prend forme. Int\u00e9ressant. Pourquoi ne pas voir plus grand?',

            # Section 2
            's2_label': 'Notre mission',
            's2_title': 'Un projet familial formateur',
            's2_p1': 'Au-del\u00e0 du produit, une opportunit\u00e9 encore plus pr\u00e9cieuse s\u2019est pr\u00e9sent\u00e9e: montrer \u00e0 nos jeunes futurs entrepreneurs comment \u00e7a marche pour vrai, un d\u00e9marrage d\u2019entreprise. Tous les processus, de la conception au code, du marketing aux ventes, de la gestion des clients aux finances, des m\u00e9dias sociaux au service apr\u00e8s-vente.',
            's2_p2': 'Pas dans un livre. Pas dans un cours th\u00e9orique. Dans le vrai monde, avec de vrais clients, de vraies factures, de vrais d\u00e9fis. <strong>C\u2019est \u00e7a, notre vraie mission familiale.</strong>',

            # Section 3
            's3_label': 'Notre engagement',
            's3_title': 'Encourager la pers\u00e9v\u00e9rance',
            's3_text': 'Cette valeur nous tient \u00e0 c\u0153ur. C\u2019est pourquoi minipass s\u2019engage \u00e0 remettre annuellement 2% de son chiffre d\u2019affaires \u00e0 la Fondation de la ligue de hockey Gagnon Image <strong>qui reconna\u00eet la pers\u00e9v\u00e9rance et l\u2019engagement des jeunes athl\u00e8tes faisant face \u00e0 l\u2019adversit\u00e9 avec courage.</strong>',

            # Team
            'team_label': 'L\u2019\u00c9QUIPE',
            'team_title': 'Rencontrez l\u2019\u00e9quipe',
            'team_subtitle': 'Une aventure familiale o\u00f9 chacun apporte sa passion',

            'ken_role': 'Co-fondateur, Chef du d\u00e9veloppement technologique',
            'ken_desc': 'Chef du d\u00e9veloppement technologique, amateur de kitesurf et innovateur passionn\u00e9.',
            'mf_role': 'Co-fondatrice, Directrice G\u00e9n\u00e9rale & Finances',
            'mf_desc': 'Responsable des op\u00e9rations et finances. Amoureuse de la nature et de voyages.',
            'eli_role': 'Co-fondatrice, M\u00e9dias Sociaux & D\u00e9veloppement',
            'eli_desc': '\u00c9tudiante \u00e0 l\u2019Universit\u00e9 Laval, responsable m\u00e9dias sociaux. Fait des vrilles et explore ses passions.',
            'phil_role': 'Co-fondateur, Marketing & D\u00e9veloppement',
            'phil_desc': '\u00c9tudiant \u00e0 l\u2019Universit\u00e9 Laval, entrepreneur dans l\u2019\u00e2me. Snowboarder, boxer, toujours en mouvement.',

            # CTA
            'cta_text': 'Envie de simplifier la gestion de vos activit\u00e9s comme on l\u2019a fait?',
            'cta_btn': 'S\u2019abonner',
        },

        # ── Blog page ──
        'blog': {
            'meta_title': 'Guides & Ressources \u2014 minipass',
            'meta_desc': 'Tutoriels vid\u00e9o, articles et guides pour ma\u00eetriser minipass et g\u00e9rer ta ligue sportive sans stress.',
            'hero_label': 'RESSOURCES',
            'hero_title': 'Apprenez en quelques minutes',
            'hero_desc': 'Tutoriels et guides pour ma\u00eetriser minipass et g\u00e9rer tes ligues, cours et \u00e9v\u00e9nements sans stress.',
            'search_placeholder': 'Rechercher un guide...',
            'filter_all': 'Tous',
            'no_results_title': 'Aucun r\u00e9sultat',
            'no_results_text': 'Essaie de modifier ta recherche',
            'no_content': 'Aucun contenu publi\u00e9 pour l\u2019instant.',
            'cta_label': 'SUPPORT',
            'cta_title': 'Besoin d\u2019aide?',
            'toast_copied': 'Lien copi\u00e9!',
            'prev_page': 'Page pr\u00e9c\u00e9dente',
            'next_page': 'Page suivante',
        },

        # ── Politiques page ──
        'policies': {
            'title': 'Politiques d\u2019abonnement',
            'meta_title': 'Politiques d\u2019abonnement \u2014 minipass',
            'meta_desc': 'Consultez les politiques d\u2019abonnement de minipass : conditions d\u2019utilisation, remboursements, annulations et confidentialit\u00e9 pour notre plateforme de gestion de ligues sportives.',
            'subtitle': 'Conditions g\u00e9n\u00e9rales de renouvellement et d\u2019annulation',
            'close': 'Fermer',

            'h_renewal': 'Abonnements et renouvellement automatique',
            'p_renewal': '<strong>Renouvellement:</strong> Tous les abonnements se renouvellent automatiquement \u00e0 la date d\u2019\u00e9ch\u00e9ance. Votre abonnement sera reconduit automatiquement pour une p\u00e9riode \u00e9quivalente \u00e0 celle initialement souscrite (mensuelle ou annuelle), sauf annulation de votre part avant la date de renouvellement.',
            'highlight_renewal': '<strong>Important:</strong> Vous serez factur\u00e9 automatiquement selon la m\u00eame fr\u00e9quence que votre abonnement initial (mensuel ou annuel) jusqu\u2019\u00e0 annulation.',

            'h_refund': 'Politique de Remboursement',
            'p_refund1': '<strong>Aucun remboursement:</strong> Les paiements d\u2019abonnement sont finaux et non remboursables. En souscrivant \u00e0 un abonnement minipass, vous reconnaissez que tous les paiements sont d\u00e9finitifs. Le client est enti\u00e8rement responsable d\u2019annuler son abonnement avant la date de renouvellement s\u2019il ne souhaite pas continuer le service.',
            'p_refund2': 'Aucune exception ne sera accord\u00e9e pour les remboursements, y compris en cas de non-utilisation du service ou d\u2019oubli d\u2019annulation avant le renouvellement.',

            'h_cancel': 'Processus d\u2019annulation',
            'p_cancel1': '<strong>Annulation:</strong> Pour annuler votre abonnement, veuillez contacter notre \u00e9quipe de support \u00e0 l\u2019adresse <a href="mailto:support@minipass.me">support@minipass.me</a>.',
            'p_cancel2': 'L\u2019annulation prend effet \u00e0 la fin de la p\u00e9riode pay\u00e9e en cours. Vous continuerez \u00e0 avoir acc\u00e8s \u00e0 votre application minipass jusqu\u2019\u00e0 la date d\u2019expiration de votre p\u00e9riode d\u2019abonnement actuelle. Aucun remboursement au prorata ne sera effectu\u00e9 pour la p\u00e9riode restante.',
            'highlight_cancel': '<strong>Rappel:</strong> Pensez \u00e0 annuler votre abonnement suffisamment \u00e0 l\u2019avance si vous ne souhaitez pas qu\u2019il se renouvelle automatiquement.',

            'h_accept': 'Acceptation des Conditions',
            'p_accept': 'En proc\u00e9dant au paiement d\u2019un abonnement minipass, le client confirme avoir lu, compris et accept\u00e9 l\u2019int\u00e9gralit\u00e9 de ces politiques sans r\u00e9serve. Le paiement constitue une acceptation explicite de ces termes et conditions.',

            'contact_title': 'Des questions?',
            'contact_text': 'Notre \u00e9quipe est disponible pour r\u00e9pondre \u00e0 vos questions:',
        },
    },

    # ═══════════════════════════════════════════
    # ENGLISH
    # ═══════════════════════════════════════════
    'en': {
        'lang_code': 'en-CA',
        'og_locale': 'en_CA',
        'alt_lang_label': 'FR',

        # ── Meta (defaults for base.html) ──
        'meta': {
            'title': 'minipass \u2014 Automatic Interac e-Transfer Matching for Leagues & Coaches | Canada',
            'description': 'minipass automates registrations, Interac e-transfer payments, digital passes and accounting for your sports leagues and courses. Canadian-built. Starting at $10/month.',
            'og_title': 'minipass \u2014 Automatic Interac e-Transfer Matching for Leagues',
            'og_desc': 'Automate registrations, Interac e-transfer matching and digital passes. Canadian-built platform. Starting at $10/month.',
        },

        # ── Navigation ──
        'nav': {
            'home': 'Home',
            'features': 'Features',
            'about': 'About Us',
            'guides': 'Guides',
            'subscribe': 'Get started',
        },

        # ── Footer ──
        'footer': {
            'tagline': 'You create your activity. minipass handles the rest.',
            'contact': 'Contact',
            'quick_links': 'Quick Links',
            'copyright': '\u00a9 2025 minipass.me, made with \u2764\ufe0f in Canada',
        },

        # ── Home page ──
        'home': {
            'meta_title': 'minipass \u2014 Registrations, Interac payments and an online store for leagues and classes',
            'meta_desc': 'You create your activity, minipass handles the rest: online registration, Interac e-Transfers detected automatically, digital passes, an online store and finances. From $10 a month.',

            # Hero
            'hero_subtitle': 'For leagues, schools, classes and organizations',
            'hero_title_prefix': 'You create your ',
            'hero_word1': 'courses',
            'hero_word2': 'leagues',
            'hero_word3': 'events',
            'hero_and': 'and',
            'hero_title_end': '. minipass handles the rest.',
            'hero_desc': 'Online registration, Interac e-Transfers detected automatically, digital passes, an online store and finances always up to date. From $10 a\u00a0month.',
            'hero_video_url': 'https://www.youtube.com/watch?v=eftLJ7hTPPs',
            'hero_btn_discover': 'Discover',
            'hero_btn_plans': 'Choose my plan',
            'hero_btn_video': 'See minipass in 1 minute',

            # Social proof
            'social_proof_label': 'THEY TRUST US',
            'testimonial1_name': 'Jean-Fran\u00e7ois Goulet',
            'testimonial1_role': 'Co-administrator of the FLHGI',
            'testimonial1_text': 'With minipass, we finally have a platform that lets us focus on our results rather than paperwork. Its intuitive design and budget dashboards have simplified our tracking by <strong>75%</strong>. It has become an indispensable ally for the fast and simple coordination of all our Foundation\u2019s fundraising programs.',
            'testimonial1_short': 'With minipass, we finally have a platform that lets us focus on our results rather than paperwork. Its intuitive design and budget dashboards have simplified our tracking by <strong>75%</strong>.',
            'testimonial2_name': 'Marc Tremblay',
            'testimonial2_role': 'Hockey Coach, Tremblay Academy',
            'testimonial2_text': 'Before minipass, I spent my weekends checking Interac e-transfers one by one. Now everything is matched automatically. Parents receive their QR pass by email and I focus on the ice, not on spreadsheets.',
            'testimonial3_name': 'Sophie Lavoie',
            'testimonial3_role': 'Yoga Instructor, Studio Lumi\u00e8re',
            'testimonial3_text': 'I tried three other platforms before minipass. None of them understood Interac. My clients register in 2 minutes from their phone and I get the confirmation automatically. Managing my classes has never been this easy.',

            # How it works
            'how_label': 'EASY AS 1-2-3',
            'how_title': 'How it works',
            'step1_title': 'Create your activity',
            'step1_text': 'Your league, class or event, in a few minutes: the price, the spots and the dates.',
            'step2_title': 'Share your link',
            'step2_text': 'Your participants register from their phone and pay by Interac e-Transfer or by card.',
            'step3_title': 'Autopilot',
            'step3_text': 'Payments are detected, passes are sent and your finances are updated. You have nothing to do.',

            # Features
            'features_label': 'FEATURES',
            'features_title': 'Everything minipass does for you',
            'feat1_title': 'Payments detected automatically',
            'feat1_text': 'Every Interac e-Transfer you receive is recognized and matched to the right person. Credit cards are accepted too.',
            'feat2_title': 'Online registration',
            'feat2_text': 'Share a link or a QR code. Your participants register from their phone, without creating an account.',
            'feat3_title': 'Digital pass',
            'feat3_text': 'Each participant gets a pass with a QR code. At every visit, they receive a confirmation and their pass updates.',
            'feat4_title': 'Online store',
            'feat4_text': 'Sell your activities and your products, like jerseys or tickets, in one place. Club and Organisation plans.',
            'feat5_title': 'Finances up to date',
            'feat5_text': 'Income, expenses and receipts per activity, updated with every payment. Export for your accountant.',
            'feat6_title': 'Also included',
            'feat6_text': 'Online session booking, automatic emails and reminders. With Club and Organisation: surveys and Wayne, your assistant who answers your questions.',

            # Pricing
            'pricing_label': 'PLANS',
            'pricing_title': 'One monthly price. No surprises.',
            'pricing_monthly': 'Monthly',
            'pricing_annual': 'Annual',
            'pricing_save': 'SAVE 50%',
            'pricing_per_month': '/ month',
            'pricing_annual_plan': 'Annual plan',
            'pricing_monthly_plan': 'Monthly plan',
            'pricing_no_contract': 'No hidden fees. No contract. Cancel anytime.',

            # Plan: Solo
            'solo_name': 'Solo',
            'solo_desc': 'A coach or an instructor, one activity',
            'solo_activity': '1',
            'solo_activity_label': 'activity',

            # Plan: Club
            'club_name': 'Club',
            'club_desc': 'A league with divisions, a school with several classes',
            'club_activity': '15',
            'club_activity_label': 'activities',

            # Plan: Organisation
            'org_name': 'Organisation',
            'org_desc': 'An organization or a foundation with several programs',
            'org_activity': '100',
            'org_activity_label': 'activities',

            # Pricing features list
            'plan_activity_suffix': '(league, class or event)',
            'plan_tooltip': '1 activity = 1 complete league, class or event, unlimited sessions.',
            'plan_tooltip_example': 'Got an invitation code? Choose your plan and enter your code at the next step.',
            'plan_feat_participants': 'Unlimited participants and passes',
            'plan_feat_registrations': 'Registration and Interac or card payments',
            'plan_feat_attendance': 'Session booking',
            'plan_feat_finance': 'Finances up to date',
            'plan_feat_survey': 'Automatic emails',
            'plan_feat_ai': 'Support in English and French',
            'plan_plus': '+ Online store, surveys and Wayne',
            'plan_btn': 'Choose this plan',

            # Newsletter
            'newsletter_label': 'FREE NEWSLETTER',
            'newsletter_title': 'Be the first to know!',
            'newsletter_placeholder': 'your@email.com',
            'newsletter_btn': 'Subscribe',
            'newsletter_success': 'You are now subscribed! You will receive the next article soon.',
            'newsletter_error': 'An error occurred. Please try again.',

            # Blog section
            'blog_label': 'OUR BLOG',
            'blog_title': 'Latest posts',
            'blog_see_all': 'See all posts',

            # Modal
            'modal_complete': 'Complete your subscription',
            'modal_app_name_label': 'Enter the desired name for your application',
            'modal_app_name_placeholder': 'myproject',
            'modal_app_name_desc': 'Your desired name:',
            'modal_app_name_available': 'is available',
            'modal_app_name_taken': 'This subdomain is already taken',
            'modal_app_name_invalid': 'Must be at least 3 characters (lowercase letters and numbers only), no spaces or special characters',
            'modal_app_name_error': 'Error checking subdomain',
            'modal_org_label': 'Enter your organization name',
            'modal_org_placeholder': 'My Organization e.g. XYZ Foundation',
            'modal_org_desc': 'This will appear in your application and communications to your participants',
            'modal_email_label': 'Enter the email address to use for administering your minipass.',
            'modal_email_placeholder': 'admin@mycompany.com',
            'modal_email_desc': 'This email address is important. It will be your administrator login for your minipass.',
            'modal_promo_toggle': 'Have a promo code?',
            'modal_promo_placeholder': 'PROMO CODE',
            'modal_promo_apply': 'Apply',
            'modal_promo_checking': 'Checking\u2026',
            'modal_promo_valid': 'Valid code! Free access activated.',
            'modal_promo_invalid': 'Invalid code',
            'modal_promo_error': 'Verification error',
            'modal_submit': 'Proceed to payment',
            'modal_submit_promo': 'Activate my code',
            'modal_billing_annual': 'Annual billing',
            'modal_billing_monthly': 'Monthly billing',
            'modal_billing_total': 'total',
            'modal_savings': 'Save 50%',
            'modal_policy': 'See our',
            'modal_policy_link': 'subscription policy',
            'modal_forfait_solo': 'Solo Plan',
            'modal_forfait_club': 'Club Plan',
            'modal_forfait_org': 'Organisation Plan',
        },

        # ── About page ──
        'about': {
            'meta_title': 'About minipass \u2014 Canadian League & Course Management Platform',
            'meta_desc': 'Meet the team behind minipass, the Canadian platform that automates sports league management, Interac payments and online registrations.',

            # Section 1
            's1_label': 'The backstory',
            's1_title': 'The $20 that started it all',
            's1_p1': 'One Sunday morning, while counting substitute player fees at hockey, Ken realized he was missing twenty dollars and the petty cash still didn\u2019t balance. Between season passes, cash payments and Interac e-transfers, financial management had become chaotic. Convinced that a simple platform should exist to fix this, he quickly discovered that available options were either too complex, too expensive, poorly designed... or all three at once!',
            's1_p2': 'The tech geek in him woke up. A prototype took shape. Interesting. Why not think bigger?',

            # Section 2
            's2_label': 'Our mission',
            's2_title': 'A family learning project',
            's2_p1': 'Beyond the product, an even more valuable opportunity presented itself: showing our young future entrepreneurs how a real business startup works. Every process, from design to code, marketing to sales, customer management to finances, social media to after-sales support.',
            's2_p2': 'Not in a book. Not in a theoretical class. In the real world, with real clients, real invoices, real challenges. <strong>That\u2019s our true family mission.</strong>',

            # Section 3
            's3_label': 'Our commitment',
            's3_title': 'Encouraging perseverance',
            's3_text': 'This value is close to our hearts. That\u2019s why minipass commits to donating 2% of its annual revenue to the Fondation de la ligue de hockey Gagnon Image, <strong>which recognizes the perseverance and commitment of young athletes facing adversity with courage.</strong>',

            # Team
            'team_label': 'THE TEAM',
            'team_title': 'Meet the team',
            'team_subtitle': 'A family adventure where everyone brings their passion',

            'ken_role': 'Co-founder, Chief Technology Officer',
            'ken_desc': 'Chief Technology Officer, kitesurfing enthusiast and passionate innovator.',
            'mf_role': 'Co-founder, General Manager & Finance',
            'mf_desc': 'Head of operations and finance. Lover of nature and travel.',
            'eli_role': 'Co-founder, Social Media & Development',
            'eli_desc': 'Student at Universit\u00e9 Laval, social media manager. Does flips and explores her passions.',
            'phil_role': 'Co-founder, Marketing & Development',
            'phil_desc': 'Student at Universit\u00e9 Laval, entrepreneur at heart. Snowboarder, boxer, always on the move.',

            # CTA
            'cta_text': 'Want to simplify your activity management like we did?',
            'cta_btn': 'Subscribe',
        },

        # ── Blog page ──
        'blog': {
            'meta_title': 'Guides & Resources \u2014 minipass',
            'meta_desc': 'Video tutorials, articles and guides to master minipass and manage your sports league stress-free.',
            'hero_label': 'RESOURCES',
            'hero_title': 'Learn in minutes',
            'hero_desc': 'Tutorials and guides to master minipass and manage your leagues, courses and events stress-free.',
            'search_placeholder': 'Search guides...',
            'filter_all': 'All',
            'no_results_title': 'No results',
            'no_results_text': 'Try modifying your search',
            'no_content': 'No content published yet.',
            'cta_label': 'SUPPORT',
            'cta_title': 'Need help?',
            'toast_copied': 'Link copied!',
            'prev_page': 'Previous page',
            'next_page': 'Next page',
        },

        # ── Politiques page ──
        'policies': {
            'title': 'Subscription Policies',
            'meta_title': 'Subscription Policies \u2014 minipass',
            'meta_desc': 'View minipass subscription policies: terms of use, refunds, cancellations and privacy for our sports league management software.',
            'subtitle': 'General renewal and cancellation terms',
            'close': 'Close',

            'h_renewal': 'Subscriptions and automatic renewal',
            'p_renewal': '<strong>Renewal:</strong> All subscriptions renew automatically on the due date. Your subscription will be automatically renewed for a period equivalent to the one initially subscribed to (monthly or annual), unless cancelled by you before the renewal date.',
            'highlight_renewal': '<strong>Important:</strong> You will be billed automatically at the same frequency as your initial subscription (monthly or annual) until cancellation.',

            'h_refund': 'Refund Policy',
            'p_refund1': '<strong>No refunds:</strong> Subscription payments are final and non-refundable. By subscribing to minipass, you acknowledge that all payments are final. The customer is entirely responsible for cancelling their subscription before the renewal date if they do not wish to continue the service.',
            'p_refund2': 'No exceptions will be granted for refunds, including in cases of non-use of the service or failure to cancel before renewal.',

            'h_cancel': 'Cancellation Process',
            'p_cancel1': '<strong>Cancellation:</strong> To cancel your subscription, please contact our support team at <a href="mailto:support@minipass.me">support@minipass.me</a>.',
            'p_cancel2': 'Cancellation takes effect at the end of the current paid period. You will continue to have access to your minipass application until the expiration date of your current subscription period. No prorated refund will be issued for the remaining period.',
            'highlight_cancel': '<strong>Reminder:</strong> Remember to cancel your subscription well in advance if you do not want it to renew automatically.',

            'h_accept': 'Acceptance of Terms',
            'p_accept': 'By proceeding with payment for a minipass subscription, the customer confirms having read, understood and accepted all of these policies without reservation. Payment constitutes explicit acceptance of these terms and conditions.',

            'contact_title': 'Questions?',
            'contact_text': 'Our team is available to answer your questions:',
        },
    },
}
