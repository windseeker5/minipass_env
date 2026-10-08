---
target: "http://localhost:5000/admin/email-preview/deployment-ready"
total_score: 21
max_score: 36
na_heuristics: 7
p0_count: 0
p1_count: 3
target_identity: "url:http://localhost:5000/admin/email-preview/deployment-ready"
timestamp: 2026-10-07T22-45-44Z
slug: localhost-admin-email-preview-deployment-ready
---
Method: dual-agent (A: design review, B: detector and browser evidence)

## Design Health Score
Total 21/36 (heuristic 7 n/a: one-shot transactional email). 58%, Acceptable.
1 Status 3 | 2 Real world 3 | 3 Control 2 | 4 Consistency 3 | 5 Error prevention 1 | 6 Recognition 3 | 7 n/a | 8 Minimalist 2 | 9 Error recovery 1 | 10 Help 3

## Design Specificity Verdict
Category-interchangeable. Brand lives only in images (fox, navy thumbnail, logo bars); UI chrome is default periwinkle on grey. Deterministic scan: 3 low-contrast warnings (CTA white on #667eea 3.7:1; footer copyright 2.5:1; footer links 1.8:1). Overlay skipped: CSP blocks injected scripts.

## Priority Issues
- [P1] Generic identity not tied to brand. Fix: palette from logo/thumbnail, real headline voice, authored ending. Commands: shape, colorize, bolder.
- [P1] Credentials block: weak hierarchy, two identical-looking cards, plaintext mailbox password that users are told to ignore, no change-password path, mid-word wrap on mobile. Commands: layout, clarify, harden.
- [P1] No dark-mode, Outlook button fallback, preheader or lang attribute. Commands: harden, adapt.
- [P2] CTA detached from credentials; video lacks play affordance; mailbox paragraph too long. Commands: distill, layout.
- [P2] Mobile polish: wrapped CTA, oversized logo, small text, misaligned Discord row. Commands: adapt, typeset.

## Persona Red Flags
Jordan: cannot tell app login from mailbox login. Casey: button above credentials, mid-word wrap breaks copy, tiny footer links. Sam: contrast failures, no lang attribute, headings are paragraphs.

## Minor Observations
Fox overlaps wordmark; French punctuation spacing; mailto unsubscribe; hardcoded year; maxresdefault thumbnail may be missing for new video; dangling colon if no forwarding email.

## Questions to Consider
One-time set-password link with no passwords in the email? Mailbox as one sentence? Brand device only minipass owns? Founder name/face in the sign-off? Video as hero?
