# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The person who runs an activity and collects money for it: a coach or instructor with one program (hockey, yoga), a league with divisions, a dance or sports school, or a foundation or nonprofit running several programs. Usually in Québec or elsewhere in Canada, often a volunteer or a one-person operation, managing the season on top of other work. Their job: get people registered and paid, know who paid, let them in at the door, and keep the books straight without spending weekends checking Interac transfers one by one.

Secondary audience: the participants and parents who register and pay. They never install an app.

## Product Purpose

minipass automates the admin of a league, course or event: online registration, payment (Interac e-Transfer or card), automatic matching of each payment to the right registration, QR digital passports scanned at the door, automatic emails and reminders, and season finances. Success for the organizer: the season runs on autopilot and the money always balances.

Origin (from the About page): Ken could not balance the petty cash of his hockey league one Sunday morning, twenty dollars short. minipass grew from that.

## Positioning

minipass reads Interac e-Transfer notifications and matches each transfer to the right registration automatically. The current site claims it is the only Canadian platform that does this, and that American platforms do not understand Interac natively. Built in Canada, French support, flat monthly price.

## Operating Context

- The organizer creates an activity (league, course or service: sessions, price, capacity) in about 4 minutes; a registration form is generated.
- They share a link or QR code. Participants register from their phone and pay by Interac transfer or card.
- Each payment is matched to the participant; confirmation, attendance and the QR passport are emailed automatically.
- At the door, the organizer scans the passport and the balance updates.
- Finances: revenue, expenses, pending balances; export to QuickBooks, Wave and Xero (per current site copy).
- Each customer gets their own app at `name.minipass.me`.

## Capabilities and Constraints

- Plans (current site): Solo (1 activity), Club (15 activities), Organisation (100 activities). Monthly or annual (annual saves 50%). From $10/month. No contract, cancel anytime. 1 activity = 1 complete league, course or service, unlimited sessions.
- Included: unlimited participants and QR passports, registrations and payments, attendance and automatic reminders, financial reports, participant experience surveys, an AI co-pilot over the organizer's data.
- Signup flow: plan choice, then a modal asking for the app address, organization name and admin email, optional invitation code, then Stripe checkout.
- Bilingual: French first at `/`, English at `/en`. Site voice uses "tu".
- Site stack: Flask + Jinja templates in this repo, translations in `translations.py`.

## Brand Commitments

- Name always lowercase: "minipass", one word, even at the start of a sentence.
- Logo: five right-aligned horizontal bars, then the wordmark in Montserrat Bold. Bar colors never change, even on dark backgrounds: orange #F46F1C, rose #E31A5A, prune #9F1574, violet #5A2692, bleu #103B99. Text black #000000, or white on dark. No outline, no shadow, never stretched. Source: `../Marketing/brand/logo-spec/`.
- Ken's binding direction for the new site (2026-10-16): keep the approved animated hero (`templates/partials/hero_motion.html`) as is; use the exact logo colors; Montserrat for titles and Inter (the app's font) for text; one calm button style; real app captures only, never stock photos and never redrawn app UI; keep all current content, including the YouTube explainer video (https://www.youtube.com/watch?v=eftLJ7hTPPs).
- Voice: direct, warm, Québec French, "tu".

## Evidence on Hand

- Testimonial 1, confirmed real (marked "réel" in the template): Jean-François Goulet, co-administrator of the FLHGI. Quote mentions budget dashboards and follow-ups simplified by 75%. Photo: `static/image/home-3/jfg-circle-1.png`; logos `static/image/flhgi.png`, `flhgi-logo-kd.png`.
- Testimonials 2 (Marc Tremblay, Académie Tremblay) and 3 (Sophie Lavoie, Studio Lumière): NOT real (Ken, 2026-10-16). Never use them; the new site shows only Jean-François Goulet's quote.
- Real app captures and demo-data method: see the hero (`static/image/hero/`), taken from the running app with injected demo content. Real customer data must never appear.
- Commitment: 2% of annual revenue goes to the Fondation de la ligue de hockey Gagnon Image.
- Team: Ken, Marie-France, Elizabeth, Philippe (family business).
- No customer counts, logos wall, press or benchmarks exist. Do not invent any.

## Product Principles

1. The organizer's time is the product: every promise is about hours not spent chasing payments.
2. Interac is the wedge: lead with what no other platform does for Canadian organizers.
3. Show the real product: proof comes from real screens and real customers, never mockups or invented numbers.
4. French first, plain words, "tu": talk like a person from the same arena.
5. Simple, fixed pricing with no cut of registrations.
