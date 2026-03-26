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
            'og_desc': 'Automatisez inscriptions, paiements Interac et passeports num\u00e9riques. Logiciel canadien. D\u00e8s 10$/mois.',
        },

        # ── Navigation ──
        'nav': {
            'home': 'Accueil',
            'features': 'Fonctionnalit\u00e9s',
            'about': '\u00c0 propos de nous',
            'guides': 'Guides',
            'subscribe': 'S\u2019abonner',
        },

        # ── Footer ──
        'footer': {
            'tagline': 'La gestion d\u2019activit\u00e9s repens\u00e9e. Simple. Automatis\u00e9. S\u00e9curis\u00e9.',
            'contact': 'Contact',
            'quick_links': 'Quick Links',
            'copyright': '\u00a9 2025 minipass.me, fait avec \u2764\ufe0f au Canada',
        },

        # ── Home page ──
        'home': {
            'meta_title': 'minipass \u2014 Jumelage automatique des virements Interac pour ligues et coachs',
            'meta_desc': 'La seule plateforme canadienne qui jum\u00e8le automatiquement tes virements Interac aux inscriptions. Cours, ligues, \u00e9v\u00e9nements. \u00c0 partir de 10$/mois. Sans contrat.',

            # Hero
            'hero_subtitle': 'Tu cr\u00e9es. Tout s\u2019automatise.',
            'hero_title_prefix': 'Automatise la gestion de tes ',
            'hero_word1': 'cours',
            'hero_word2': 'ligues',
            'hero_word3': '\u00e9v\u00e9nements',
            'hero_and': 'et',
            'hero_desc': 'Inscriptions. Paiements Interac automatiques. Passeports num\u00e9riques. Courriels. Finances. Tout en un.',
            'hero_video_url': 'https://www.youtube.com/watch?v=eftLJ7hTPPs',
            'hero_btn_discover': 'D\u00e9couvrir',
            'hero_btn_plans': 'Voir les forfaits',

            # Social proof
            'social_proof_label': 'ILS NOUS FONT CONFIANCE',
            'testimonial1_name': 'Jean-Fran\u00e7ois Goulet',
            'testimonial1_role': 'Co-administrateur de la FLHGI',
            'testimonial1_text': 'Avec minipass, nous avons enfin un outil qui nous permet de nous concentrer sur nos r\u00e9sultats plut\u00f4t que sur la paperasse. Son intuitivit\u00e9 et ses tableaux de bord budg\u00e9taires ont simplifi\u00e9 nos suivis de <strong>75 %</strong>. C\u2019est devenu l\u2019alli\u00e9 indispensable pour la coordination rapide et simple de toutes les activit\u00e9s de financement de notre Fondation.',
            'testimonial2_name': 'Marc Tremblay',
            'testimonial2_role': 'Entra\u00eeneur hockey, Acad\u00e9mie Tremblay',
            'testimonial2_text': 'Avant minipass, je passais mes fins de semaine \u00e0 v\u00e9rifier les virements Interac un par un. Maintenant, tout est jumel\u00e9 automatiquement. Mes parents re\u00e7oivent leur passeport QR par courriel et je me concentre sur la glace, pas sur les chiffriers.',
            'testimonial3_name': 'Sophie Lavoie',
            'testimonial3_role': 'Instructrice yoga, Studio Lumi\u00e8re',
            'testimonial3_text': 'J\u2019avais essay\u00e9 trois autres outils avant minipass. Aucun comprenait Interac. Mes clientes s\u2019inscrivent en 2 minutes depuis leur t\u00e9l\u00e9phone et je re\u00e7ois la confirmation automatiquement. La gestion de mes cours n\u2019a jamais \u00e9t\u00e9 aussi simple.',

            # How it works
            'how_label': 'SIMPLE COMME BONJOUR',
            'how_title': 'Comment \u00e7a marche',
            'step1_title': 'Cr\u00e9e ton activit\u00e9',
            'step1_text': 'Configure ta ligue, ton cours ou ton service en 4 minutes. Tu d\u00e9finis les s\u00e9ances, le prix et les limites de capacit\u00e9. Ton formulaire d\u2019inscription est g\u00e9n\u00e9r\u00e9 automatiquement \u2014 en ligne, pr\u00eat \u00e0 recevoir tes paiements.',
            'step2_title': 'Partage ton lien',
            'step2_text': 'Tes participants s\u2019inscrivent depuis leur t\u00e9l\u00e9phone ou ordinateur. Ils paient par virement Interac ou par carte de cr\u00e9dit \u2014 au choix.',
            'step3_title': 'Pilote automatique',
            'step3_text': 'Chaque paiement re\u00e7u est jumel\u00e9 au bon participant. Confirmation de paiement, participations et passeport num\u00e9rique sont envoy\u00e9s automatiquement par courriel. Ta comptabilit\u00e9 est toujours \u00e0 jour \u2014 sans que tu touches \u00e0 rien.',

            # Features
            'features_label': 'FONCTIONNALIT\u00c9S CL\u00c9S',
            'features_title': 'Tout ce dont tu as besoin pour g\u00e9rer ta saison',
            'feat1_title': 'Jumelage automatique de paiement',
            'feat1_text': 'Tes participants font leur virement comme d\u2019habitude \u2014 pas d\u2019application \u00e0 t\u00e9l\u00e9charger. minipass jum\u00e8le chaque paiement automatiquement. Fini les heures par semaine \u00e0 v\u00e9rifier manuellement.',
            'feat2_title': 'Courriels et rappels automatiques',
            'feat2_text': 'Confirmation d\u2019inscription, rappel de paiement, r\u00e9demption de passeport \u2014 tout est automatis\u00e9. Tes participants re\u00e7oivent les bonnes informations au bon moment, sans effort de ta part.',
            'feat3_title': 'Inscriptions en ligne simplifi\u00e9es',
            'feat3_text': 'Cr\u00e9e ton activit\u00e9, partage le lien, et minipass g\u00e8re les inscriptions et les paiements \u00e0 ta place. Tes participants s\u2019inscrivent en quelques clics.',
            'feat4_title': 'Gestion financi\u00e8re int\u00e9gr\u00e9e',
            'feat4_text': 'Tableaux financiers complets : revenus, d\u00e9penses, soldes en attente. Export direct vers QuickBooks, Wave et Xero. Fini les fins de mois \u00e0 rattraper.',
            'feat5_title': 'Passeports num\u00e9riques QR',
            'feat5_text': 'Chaque participant re\u00e7oit son passeport num\u00e9rique avec code QR par courriel. Tu scannes \u00e0 l\u2019entr\u00e9e, le solde se met \u00e0 jour automatiquement.',
            'feat6_title': 'Con\u00e7u au Canada, pour Interac',
            'feat6_text': 'Aucun outil am\u00e9ricain ne comprend Interac natif. minipass oui. Support en fran\u00e7ais. Donn\u00e9es h\u00e9berg\u00e9es au Canada.',

            # Pricing
            'pricing_label': 'NOS FORFAITS',
            'pricing_title': 'Simples, clairs, sans surprise',
            'pricing_monthly': 'Mensuel',
            'pricing_annual': 'Annuel',
            'pricing_save': '\u00c9CONOMISEZ 50%',
            'pricing_per_month': '/ mois',
            'pricing_annual_plan': 'Forfait annuel',
            'pricing_monthly_plan': 'Forfait mensuel',
            'pricing_no_contract': 'Pas de contrat. Annule en tout temps.',

            # Plan: Solo
            'solo_name': 'Solo',
            'solo_desc': 'Coach hockey, instructeur yoga, 1 programme actif',
            'solo_activity': '1',
            'solo_activity_label': 'activit\u00e9',

            # Plan: Club
            'club_name': 'Club',
            'club_desc': 'Ligue avec divisions, \u00e9cole de danse, multi-cours',
            'club_activity': '15',
            'club_activity_label': 'activit\u00e9s',

            # Plan: Organisation
            'org_name': 'Organisation',
            'org_desc': 'Fondation, organisme, r\u00e9seau de programmes',
            'org_activity': '100',
            'org_activity_label': 'activit\u00e9s',

            # Pricing features list
            'plan_activity_suffix': '(ligue, cours ou service)',
            'plan_tooltip': '1 activit\u00e9 = 1 ligue, cours ou service complet, sessions illimit\u00e9es incluses.',
            'plan_tooltip_example': 'Ex : ligue de hockey 20 semaines, 2 parties/semaine = 1 activit\u00e9.',
            'plan_feat_participants': 'Participants & passeports QR illimit\u00e9s',
            'plan_feat_registrations': 'Inscriptions et paiements',
            'plan_feat_attendance': 'Pr\u00e9sences et rappels automatiques',
            'plan_feat_finance': 'Rapports suivis financiers',
            'plan_feat_survey': 'Sondage d\u2019exp\u00e9rience participants',
            'plan_feat_ai': 'Co-pilot & Intelligence artificielle de vos donn\u00e9es',
            'plan_btn': 'M\u2019abonner',

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
            'meta_title': '\u00c0 propos de minipass \u2014 Logiciel canadien de gestion d\u2019activit\u00e9s',
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
            'meta_desc': 'Consultez les politiques d\u2019abonnement de minipass : conditions d\u2019utilisation, remboursements, annulations et confidentialit\u00e9 pour notre logiciel de gestion de ligues sportives.',
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
            'og_desc': 'Automate registrations, Interac payments and digital passes. Canadian-built software. Starting at $10/month.',
        },

        # ── Navigation ──
        'nav': {
            'home': 'Home',
            'features': 'Features',
            'about': 'About Us',
            'guides': 'Guides',
            'subscribe': 'Subscribe',
        },

        # ── Footer ──
        'footer': {
            'tagline': 'Activity management reimagined. Simple. Automated. Secure.',
            'contact': 'Contact',
            'quick_links': 'Quick Links',
            'copyright': '\u00a9 2025 minipass.me, made with \u2764\ufe0f in Canada',
        },

        # ── Home page ──
        'home': {
            'meta_title': 'minipass \u2014 Automatic Interac e-Transfer Matching for Leagues & Coaches',
            'meta_desc': 'The only Canadian platform that automatically matches your Interac e-transfers to registrations. Courses, leagues, events. Starting at $10/month. No contract.',

            # Hero
            'hero_subtitle': 'You create. Everything automates.',
            'hero_title_prefix': 'Automate the management of your ',
            'hero_word1': 'courses',
            'hero_word2': 'leagues',
            'hero_word3': 'events',
            'hero_and': 'and',
            'hero_desc': 'Registrations. Automatic Interac payments. Digital passes. Emails. Finances. All in one.',
            'hero_video_url': 'https://www.youtube.com/watch?v=eftLJ7hTPPs',
            'hero_btn_discover': 'Discover',
            'hero_btn_plans': 'See plans',

            # Social proof
            'social_proof_label': 'THEY TRUST US',
            'testimonial1_name': 'Jean-Fran\u00e7ois Goulet',
            'testimonial1_role': 'Co-administrator of the FLHGI',
            'testimonial1_text': 'With minipass, we finally have a tool that lets us focus on our results rather than paperwork. Its intuitive design and budget dashboards have simplified our tracking by <strong>75%</strong>. It has become an indispensable ally for the fast and simple coordination of all our Foundation\u2019s fundraising activities.',
            'testimonial2_name': 'Marc Tremblay',
            'testimonial2_role': 'Hockey Coach, Tremblay Academy',
            'testimonial2_text': 'Before minipass, I spent my weekends checking Interac e-transfers one by one. Now everything is matched automatically. Parents receive their QR pass by email and I focus on the ice, not on spreadsheets.',
            'testimonial3_name': 'Sophie Lavoie',
            'testimonial3_role': 'Yoga Instructor, Studio Lumi\u00e8re',
            'testimonial3_text': 'I tried three other tools before minipass. None of them understood Interac. My clients register in 2 minutes from their phone and I get the confirmation automatically. Managing my classes has never been this easy.',

            # How it works
            'how_label': 'EASY AS 1-2-3',
            'how_title': 'How it works',
            'step1_title': 'Create your activity',
            'step1_text': 'Set up your league, course or service in 4 minutes. Define sessions, pricing and capacity limits. Your registration form is generated automatically \u2014 online, ready to receive payments.',
            'step2_title': 'Share your link',
            'step2_text': 'Your participants register from their phone or computer. They pay by Interac e-transfer or credit card \u2014 their choice.',
            'step3_title': 'Autopilot',
            'step3_text': 'Every payment received is matched to the right participant. Payment confirmation, attendance and digital pass are sent automatically by email. Your accounting is always up to date \u2014 without lifting a finger.',

            # Features
            'features_label': 'KEY FEATURES',
            'features_title': 'Everything you need to manage your season',
            'feat1_title': 'Automatic payment matching',
            'feat1_text': 'Your participants send their e-transfer as usual \u2014 no app to download. minipass matches each payment automatically. No more hours per week checking manually.',
            'feat2_title': 'Automatic emails and reminders',
            'feat2_text': 'Registration confirmation, payment reminder, pass redemption \u2014 everything is automated. Your participants get the right information at the right time, with no effort on your part.',
            'feat3_title': 'Simplified online registrations',
            'feat3_text': 'Create your activity, share the link, and minipass handles registrations and payments for you. Your participants register in a few clicks.',
            'feat4_title': 'Integrated financial management',
            'feat4_text': 'Complete financial dashboards: revenue, expenses, pending balances. Direct export to QuickBooks, Wave and Xero. No more month-end catch-up.',
            'feat5_title': 'Digital QR passes',
            'feat5_text': 'Each participant receives their digital pass with QR code by email. You scan at the door, the balance updates automatically.',
            'feat6_title': 'Built in Canada, for Interac',
            'feat6_text': 'No American tool supports native Interac. minipass does. French support. Data hosted in Canada.',

            # Pricing
            'pricing_label': 'OUR PLANS',
            'pricing_title': 'Simple, clear, no surprises',
            'pricing_monthly': 'Monthly',
            'pricing_annual': 'Annual',
            'pricing_save': 'SAVE 50%',
            'pricing_per_month': '/ month',
            'pricing_annual_plan': 'Annual plan',
            'pricing_monthly_plan': 'Monthly plan',
            'pricing_no_contract': 'No contract. Cancel anytime.',

            # Plan: Solo
            'solo_name': 'Solo',
            'solo_desc': 'Hockey coach, yoga instructor, 1 active program',
            'solo_activity': '1',
            'solo_activity_label': 'activity',

            # Plan: Club
            'club_name': 'Club',
            'club_desc': 'League with divisions, dance school, multi-course',
            'club_activity': '15',
            'club_activity_label': 'activities',

            # Plan: Organisation
            'org_name': 'Organisation',
            'org_desc': 'Foundation, organization, network of programs',
            'org_activity': '100',
            'org_activity_label': 'activities',

            # Pricing features list
            'plan_activity_suffix': '(league, course or service)',
            'plan_tooltip': '1 activity = 1 complete league, course or service, unlimited sessions included.',
            'plan_tooltip_example': 'E.g.: hockey league 20 weeks, 2 games/week = 1 activity.',
            'plan_feat_participants': 'Unlimited participants & QR passes',
            'plan_feat_registrations': 'Registrations and payments',
            'plan_feat_attendance': 'Attendance and automatic reminders',
            'plan_feat_finance': 'Financial tracking reports',
            'plan_feat_survey': 'Participant experience survey',
            'plan_feat_ai': 'Co-pilot & AI analytics for your data',
            'plan_btn': 'Subscribe',

            # Newsletter
            'newsletter_label': 'FREE NEWSLETTER',
            'newsletter_title': 'Be the first to know!',
            'newsletter_placeholder': 'your@email.com',
            'newsletter_btn': 'Subscribe',
            'newsletter_success': 'You are now subscribed! You will receive the next article soon.',
            'newsletter_error': 'An error occurred. Please try again.',

            # Blog section
            'blog_label': 'OUR BLOG',
            'blog_title': 'Latest articles',
            'blog_see_all': 'See all articles',

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
            'meta_title': 'About minipass \u2014 Canadian Activity Management Software',
            'meta_desc': 'Meet the team behind minipass, the Canadian platform that automates sports league management, Interac payments and online registrations.',

            # Section 1
            's1_label': 'The backstory',
            's1_title': 'The $20 that started it all',
            's1_p1': 'One Sunday morning, while counting substitute player fees at hockey, Ken realized he was missing twenty dollars and the petty cash still didn\u2019t balance. Between season passes, cash payments and Interac transfers, financial management had become chaotic. Convinced that a simple app should exist to fix this, he quickly discovered that available options were either too complex, too expensive, poorly designed... or all three at once!',
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
