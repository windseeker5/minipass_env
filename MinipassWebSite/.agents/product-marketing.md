# Product Marketing Context

**Document version:** v5
**Last updated:** 2026-10-16

Sources: Ken's notes (2026-10-16 conversation), the current website text (`translations.py`, `templates/nouveau/`), the pitch draft `~/Documents/marketing-pitch-new-website.md`, a code check of the customer app (`../app`), and a competitor scan (October 2026). Items marked **[ASSUMPTION]** or **[NEED]** are not confirmed by Ken yet.

## Product Overview
**One-liner:** minipass gère les inscriptions et les paiements de ta ligue, de ton école ou de tes cours, et jumelle tout seul chaque virement Interac à la bonne inscription. Prix fixe, aucun pourcentage.
**What it does:** The organizer creates an activity (price, spots, sessions), shares a link or QR code, and participants register and pay by Interac e-Transfer or card. minipass reads the Interac notification emails in the organizer's mailbox, matches each transfer to the right registration, emails the participant a QR passport they open without an account, and keeps per-activity finances. Participants can book sessions with limited spots; the organizer can sell passes and products in an online store (pickup); surveys and an AI assistant (Wayne) round it out.
**Product category:** Logiciel d'inscription et de paiement en ligne pour activités (registration software for leagues, clubs, classes). Customers search: "inscription en ligne ligue", "gestion des inscriptions", "paiement Interac inscription", "carte de membre", "logiciel pour club sportif".
**Product type:** SaaS, one private app per customer at `nom.minipass.me`.
**Business model:** Subscription. Solo 10 $/mois (1 activity), Club 25 $/mois (15), Organisation 60 $/mois (100), billed yearly; monthly billing is double (20/50/120). Unlimited participants. No contract. minipass takes no percentage on any payment. Invitation (promo) codes give free access to strategic people. **Plan contents (Ken, 2026-10-16): Solo does NOT include the online store, surveys or Wayne; Club and Organisation include everything.** The app does not enforce this today (no feature is locked by tier in code). Ken (2026-10-16): the site shows Solo without them on purpose, to steer people to Club; do not change the app for now.

## Target Audience
**Target organizations:** Small Quebec organizations that collect money for an activity: recreational sports leagues (adult hockey, ball, volleyball), sport and lesson schools (snowboard, wing foil, swimming, dance, yoga), small clubs, foundations and fundraising programs. Launch market: French-speaking Quebec, starting from Rimouski / Bas-Saint-Laurent.
**Decision-makers:** The person who does the admin, often a volunteer or a one-person business: league treasurer or organizer, school owner, independent instructor, foundation coordinator. They buy alone, with a credit card, without a sales call.
**Primary use case:** Get people registered and paid by Interac without checking every transfer by hand, and know at the door who paid and what they have left.
**Jobs to be done:**
- "Dis-moi qui a payé, sans que j'aie à vérifier chaque virement."
- "Laisse les gens s'inscrire et réserver leur place sans que je réponde à 40 courriels."
- "Que ma caisse balance à la fin de la saison."
**Use cases:**
- Adult hockey league: season pass with credits, scanned at the rink door, last season's pass still accepted.
- Snowboard / wing foil school: dated lessons with limited spots, students book their next session from their passport.
- Foundation / team: sell passes, jerseys or tickets in one cart; track income and expenses per program.

## Personas
| Persona | Cares about | Challenge | Value we promise |
|---|---|---|---|
| League treasurer (volunteer) | Not losing evenings; money balancing | Opens every Interac email, matches names in a spreadsheet, chases unpaid players | Transfers matched for them; unpaid list and reminders automatic |
| School / instructor owner | Full classes, no admin, no % fees | Booking through DMs and texts, card fees eating margins, clunky platform for students | Students book and pay alone; flat price; Interac with no fee |
| Foundation coordinator | Clear books for the board | Several programs, receipts everywhere | Income/expenses per activity, receipts, CSV for the accountant |
| Participant / parent (not the buyer) | Paying fast, no new account | Platforms that force an account and card fees | Pays with own bank, opens passport from email |

## Problems & Pain Points
**Core problem:** Interac is how Quebec pays, but every transfer has to be checked and matched by hand against a list, then the participant confirmed, then tracked at the door.
**Why alternatives fall short:**
- Google Forms / Jotform + manual Interac: the organizer does all the matching, confirming and tracking.
- Amilia: built for municipalities; 99 $/mois + 1 % service fee + card fees; Interac only on in-person terminals; parents must create an account.
- Activity Messenger: matches Interac too, but costs about 69-199 $/mois **plus 1 % per Interac transfer**.
- Qidigo: parents create an account and subscribe to each organization; more clicks.
- Zeffy: free, but nonprofits only, no Interac, donors confused by the "tip".
- Studio tools (Mindbody, Momence): English-first, percentages or high monthly fees.
**What it costs them:** Evenings per week checking transfers; unpaid players nobody follows; a cash box that doesn't balance (Ken's 20 $ story); 1-4 % of revenue lost to fees on other platforms.
**Emotional tension:** "Est-ce que tout le monde a payé?" Awkward chasing of friends and parents. Fear of looking disorganized in front of the team or the board.

## Competitive Landscape
**Direct:** Activity Messenger (Quebec) — same Interac matching, but priced for bigger organizations and takes 1 % per Interac transfer.
**Direct:** Amilia / SmartRec — municipal-scale, 99 $+ /mois plus percentages, no online Interac, accounts required.
**Direct:** Qidigo — municipal camps; account and per-organization subscription for parents.
**Secondary:** Zeffy (nonprofit ticketing/fundraising, free), Square (store/appointments, card only), Bookeo, Mindbody/Momence (studios).
**Indirect / status quo:** Google Forms or Jotform + Interac to an email + Excel + paper punch cards.

## Differentiation
**Key differentiators:**
- Automatic Interac matching at a small-club price: from 10 $/mois, 0 % on Interac and on card (only Stripe's own fee on card).
- A QR passport with credits (punch card / season pass) scanned at the door, opened from the email without an account.
- Built for the small organizer (one person, one activity) as much as for a club; for-profit schools welcome (unlike Zeffy).
- A family business from Rimouski; the founders answer support themselves.
**How we do it differently:** minipass reads the Interac notifications already arriving in the organizer's mailbox, so nothing changes for the payer: they pay with their usual bank.
**Why that's better:** No new habit for parents or players, no fee on the money, no spreadsheet.
**Why customers choose us:** Price + Interac + simplicity. **[NEED: confirm with FLHGI, the snowboard school and the wing foil teacher why they said yes.]**

## Objections
| Objection | Response |
|---|---|
| "Mes participants vont devoir créer un compte?" | Non. Ils s'inscrivent avec un lien, paient avec leur banque et ouvrent leur passeport depuis leur courriel. |
| "Comment ça peut lire mes virements?" | minipass lit seulement les avis de virement d'Interac dans ta boîte courriel, vérifie qu'ils viennent bien d'Interac, puis jumelle nom et montant. |
| "Un parent paie pour son enfant, ça marche?" | Le virement t'attend dans ta boîte de réception Interac; tu le relies à l'inscription en deux clics. |
| "C'est quoi l'attrape sur le prix?" | Prix fixe. Aucun pourcentage. Carte: ton propre compte Stripe, seuls les frais de Stripe. |
| "Changer de système en pleine saison, c'est long?" | Ton minipass est créé quelques minutes après l'abonnement; première activité la journée même. |
| "Et si ça ne marche pas pour moi?" | Sans contrat. Annule quand tu veux; l'accès reste jusqu'à la fin de la période payée. (No refunds per policy.) |

**Anti-persona:** Municipalities and day camps needing Relevé 24, federation-mandated registration (Hockey Québec uses Spordle), organizations needing waitlists, custom form fields, waivers, refunds through the platform, or product shipping. Organizers whose bank sends English Interac notifications (parser reads French notifications only) **[NEED: confirm before marketing in English]**.

## Switching Dynamics
**Push:** Evenings matching transfers; unpaid players; card fees and percentages; parents complaining about accounts.
**Pull:** Transfers matched alone; passport on the phone; flat low price; a real family answering in French.
**Habit:** "Mon chiffrier marche." Google Forms is free. Everyone already knows the Interac email.
**Anxiety:** Giving mailbox access; losing data mid-season; being stuck in a contract; tech too complicated for a volunteer.

## Customer Language
**How they describe the problem (Quebec, public sources):**
- "virement Interac à [courriel]", "question de sécurité", "dépôt automatique"
- "Votre achat sera contrôlé, puis vous recevrez un courriel de confirmation" (manual checking)
- "inscriptions", "premier arrivé, premier servi", "carte de membre", "carte de 10 cours", "frais d'administration"
- Ken: "la petite caisse ne balance pas", "il manquait 20 $"
**True origin story (Ken, 2026-10-16), use this, not "born in an arena":** Ken was the treasurer of a big hockey league, the one who kept asking players and substitutes for money. When they started the foundation, the league went to three days a week, and collecting by hand (Interac transfers, paper punch cards) became too much to follow. That is why he built minipass.
**How they describe us:**
- "nous concentrer sur nos résultats plutôt que sur la paperasse", "simplifié nos suivis de 75 %" — Jean-François Goulet, FLHGI
- **[NEED: verbatim from the snowboard school and the wing foil teacher.]**
**Words to use:** virement Interac, inscription, payé / pas payé, passeport, crédits, places, séance, boutique, cueillette, prix fixe, aucun pourcentage, chiffrier, ta saison.
**Words to avoid:** "jumelage" alone without saying what is matched; "automatisation", "plateforme tout-en-un", "solution", "révolutionner", "rédemption" (anglicism; say "utilisation" or "passage"), "co-pilot", "sans frais" (Zeffy owns it; card has Stripe fees), "le seul / la seule plateforme", "fait au Québec" as a differentiator (every competitor is from Quebec; say "Rimouski, en famille").
**Glossary:**
| Term | Meaning |
|---|---|
| Passeport | The participant's pass: QR code, credits left, bookings, history. Opened from a link, no account. |
| Crédit | One use of the pass (one game, one lesson). Scanning uses one credit. |
| Activité | One league, course or program, unlimited sessions. Plans count activities. |
| Boîte de réception Interac | Where transfers that couldn't be matched wait for one click. |
| Wayne | The admin's AI assistant, read-only, answers questions about their own data in French or English. |

## Brand Voice
| Attribute | Means | Doesn't mean | Example line |
|---|---|---|---|
| Comme au vestiaire | "tu", plain Quebec French, short sentences | Slang, jokes at the reader's expense | "Tu crées. Tout s'automatise." |
| Concret | Names the transfer, the spreadsheet, the rink door | Abstract benefits ("gagne en efficacité") | "Tu scannes à l'entrée, le solde se met à jour." |
| Honnête | Says exactly what is automatic and what takes a click | Overclaiming ("le seul", "zéro effort") | (new) |
| Famille | We, the four of us, from Rimouski | Cute or amateur | "Une aventure familiale où chacun apporte sa passion" |

**Tone by context:**
- Support: "vous" is fine one-on-one if the person writes "vous"; otherwise "tu". Warm, fast, signed by a first name.
- Launch: specifics (what's new, who it's for, one number).
- Errors: what happened and what to do, no apology loops.
- Sales: price and Interac first, story second.
- Social: real arena / lesson moments, real screens.
**Terms we own:** passeport, "aucun pourcentage", Wayne.
**Never use (and why):** fake testimonials (Marc Tremblay, Sophie Lavoie are not real); QuickBooks/Wave/Xero export (CSV only); "le seul / seule" (Activity Messenger also matches Interac); shipping (pickup only); emojis.

## Proof Points
**Metrics:** FLHGI league on minipass for about 2 seasons; about 25-26 k$ per season handled **[NEED: FLHGI OK to publish the amount]**. "Suivis simplifiés de 75 %" (FLHGI quote).
**Customers:** FLHGI (real, logo available). Beta: a second hockey league, a snowboard school **[NEED: names and permission]**.
**Testimonials:**
> "Avec minipass, nous avons enfin une plateforme qui nous permet de nous concentrer sur nos résultats plutôt que sur la paperasse. […] simplifié nos suivis de 75 %." — Jean-François Goulet, co-administrateur de la FLHGI
**Value themes:**
| Theme | Proof |
|---|---|
| Interac matched alone | Code: reads Interac notifications (DKIM-checked), matches name + amount at 85 %+ |
| No percentage | Code: no platform fee; card via the organizer's own Stripe |
| No account for participants | Code: passport at /pass/<code>, opened from the email |
| Bookings with spots | Code: dated sessions, hard capacity, "X places restantes" |
| Family, local support | About page, team photos, 2 % to the Fondation de la ligue de hockey Gagnon Image **[NEED: still true?]** |

## Goals
**Business goal:** First paying customers in French Quebec (leagues, schools, small organizations), starting from Rimouski.
**Conversion action:** Choose a plan and complete the signup (Stripe checkout), or enter an invitation code.
**Current metrics:** Not measured yet. GA4 and Meta pixel installed.

## Learnings
*Decisions and tested lessons. Newest first.*
| Date | Learning | Evidence | Applies to | Status |
|---|---|---|---|---|
| 2026-10-16 | No FAQ block on the homepage; Ken finds it heavy and off-moment. Put key reassurances in short lines near the prices instead. | Ken on mockup v5 | Homepage | active |
| 2026-10-16 | Don't repeat the About page on the homepage (no family section there). The story lives on the About page. | Ken on mockup v4 | Homepage | active |
| 2026-10-16 | Hero must say what minipass is as a whole ("Tu crées ton activité. minipass s'occupe du reste."), not one feature. Interac alone is too narrow. | Ken rejected the Interac-only hero | Homepage, ads | active |
| 2026-10-16 | No problem-agitation scenes the reader doesn't recognize ("la soirée des virements Interac"). | Ken: "Personne ne sait ça" | All copy | active |
| 2026-10-16 | Features: short, plain, list them all (incl. surveys, passport updated + confirmation at each visit). No mechanism details on the homepage. | Ken feedback on v1 | Homepage | active |
| 2026-10-16 | Don't lead with Rimouski or "we are four"; Rimouski means nothing to most visitors. | Ken feedback on v1 | All copy | active |
| 2026-10-16 | Pricing message must be dead simple: "Un prix par mois. Tout est inclus." Don't talk about renting the software, percentages or competitors on the page. Card fees (Stripe) only in the FAQ. Never claim "the only platform". | Ken rejected "Tu loues le logiciel..." | Pricing, FAQ, ads | active |
| 2026-10-16 | Don't lead with "the only Interac platform": a Quebec competitor (Activity Messenger) also matches Interac. Lead with Interac matched + flat price + 0 %. | Competitor scan, activitymessenger.com/help/interac | All copy | active |
| 2026-10-16 | Ken rejected a quick headline rewrite ("Ils s'inscrivent. Ils paient. Tu n'as rien à faire.") as unthought. Copy must come from this document and the skills. | Ken, conversation | Copywriting | active |

## Changelog
*Newest first.*
- v5 (2026-10-16) — Corrected origin story (treasurer of a big league, foundation, three days a week); no family section on the homepage.
- v4 (2026-10-16) — Solo excludes store, surveys and Wayne (Ken). Never write "tout est inclus" without that caveat.
- v3 (2026-10-16) — Pricing message simplified to "Un prix par mois. Tout est inclus." per Ken.
- v2 (2026-10-16) — Learnings from Ken on homepage mockup v1: broad hero, short features, no Rimouski, "tu loues le logiciel" pricing message.
- v1 (2026-10-16) — Initial context, drafted from the site, the app code, Ken's notes and a competitor scan.
