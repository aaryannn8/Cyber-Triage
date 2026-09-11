# Product Requirements Document (PRD)
## AI-Powered Cybercrime Complaint Triage & Pattern Detection System

**Version:** 1.0 (Hackathon MVP)
**Prepared for:** Hackathon Submission
**Date:** September 2026

---

## 1. Executive Summary

Cybercrime helplines and portals (e.g., National Cyber Crime Reporting Portal-style systems) receive a high volume of complaints daily — phishing, UPI/financial fraud, sextortion, identity theft, ransomware, social media impersonation, etc. Today, most triage is manual: officers read each complaint, classify it, assign priority, and try to spot links to other cases largely from memory or basic keyword search. This is slow, inconsistent, and misses cross-complaint patterns (e.g., the same mule bank account or phone number reused across hundreds of complaints).

This product uses AI/NLP to **automatically classify, prioritize, and cluster cybercrime complaints**, surfacing linked cases and emerging fraud patterns in near real time — helping law enforcement respond faster and smarter with limited human resources.

---

## 2. Problem Statement

- Complaints arrive in unstructured, free-text form (multiple languages, typos, inconsistent formats) via web portals, call centers, and mobile apps.
- Manual triage is slow (hours to days), leading to delayed action on time-sensitive fraud (e.g., freezing a bank account before money is withdrawn).
- Officers cannot easily detect that dozens of "isolated" complaints share a common phone number, UPI ID, bank account, IP address, or modus operandi — meaning organized fraud rings go undetected.
- Low-severity/duplicate complaints consume the same triage time as high-severity, urgent ones.
- No centralized, evolving view of "trending scams" for public advisories or resource allocation.

---

## 3. Goals & Objectives

| Goal | Description |
|---|---|
| G1 | Automatically classify incoming complaints into cybercrime categories with high accuracy |
| G2 | Assign a priority/urgency score to route time-sensitive cases (e.g., active financial fraud) to officers first |
| G3 | Detect patterns and links across complaints (shared entities: phone numbers, UPI IDs, bank accounts, URLs, IPs) |
| G4 | Cluster related complaints to reveal organized fraud rings or trending scam campaigns |
| G5 | Provide an officer-facing dashboard for triage queue, case linking, and pattern visualization |
| G6 | Reduce average triage time and improve first-response prioritization accuracy |

---

## 4. Target Users / Personas

1. **Intake/Triage Officer** — reviews incoming complaints, needs quick classification + priority to decide next action.
2. **Investigating Officer** — needs to see linked/similar cases to build a fuller picture of an ongoing fraud ring.
3. **Cybercrime Cell Supervisor/Admin** — needs dashboards on trends, volumes, and hotspot patterns for resource allocation and public advisories.
4. **(Stretch) Citizen Complainant** — submits complaint via form/chatbot and gets an acknowledgment with category and reference ID.

---

## 5. Scope

### In Scope (Hackathon MVP)
- Complaint intake form (text-based; optionally simple file/screenshot upload)
- NLP-based classification into predefined cybercrime categories
- Rule + ML-based priority/urgency scoring
- Entity extraction (phone numbers, emails, UPI IDs, bank account numbers, URLs, IP addresses) from complaint text
- Similarity/duplicate detection and clustering of complaints sharing entities or semantic similarity
- Officer dashboard: triage queue, complaint detail view, linked-case graph/list, basic analytics (trending categories, geo hotspots if location given)
- Sample/synthetic dataset for demo (no real PII)

### Out of Scope (for hackathon; future roadmap)
- Integration with live government databases (NCRP, bank APIs, telecom lookup)
- Multi-language voice/call transcription
- Legal case management / chargesheet generation
- Real production-grade authentication, audit trails, compliance (DPDP Act, evidence chain-of-custody)
- Mobile app

---

## 6. Key Features & Functional Requirements

### 6.1 Complaint Intake
- FR1: System accepts complaint text (and optional structured fields: category hint, location, date of incident, amount lost).
- FR2: System generates a unique complaint ID and timestamp on submission.

### 6.2 AI Classification Engine
- FR3: Classify each complaint into categories such as: Phishing, Financial/UPI Fraud, Identity Theft, Sextortion/Harassment, Ransomware/Malware, Social Media Impersonation, Job/Investment Scam, Other.
- FR4: Return a confidence score per prediction; low-confidence cases flagged for manual review.
- FR5: Support multilingual input (at minimum English + Hindi, using translation or multilingual embeddings).

### 6.3 Priority / Urgency Scoring
- FR6: Compute an urgency score based on signals such as: financial loss amount, time since incident (freshness — money can still be traced/frozen), category severity weight (e.g., sextortion of a minor > generic spam), and presence of ongoing threat language.
- FR7: Rank the triage queue by urgency score, with manual override by officers.

### 6.4 Entity Extraction (NER)
- FR8: Extract structured entities from free text: phone numbers, emails, UPI IDs/VPAs, bank account/IFSC, URLs/domains, IP addresses, social media handles.
- FR9: Store extracted entities linked to the complaint record for cross-referencing.

### 6.5 Pattern Detection & Clustering
- FR10: Detect exact-match links between complaints sharing an extracted entity (e.g., same UPI ID appears in 40 complaints).
- FR11: Detect semantic similarity between complaints (similar narrative/modus operandi) using text embeddings, even without shared entities.
- FR12: Cluster linked/similar complaints into "case groups" and visualize as a network graph.
- FR13: Flag clusters that cross a threshold (e.g., 5+ complaints) as a potential "organized fraud ring" alert.

### 6.6 Officer Dashboard
- FR14: Triage queue view — sortable/filterable by category, urgency, date, status.
- FR15: Complaint detail view — full text, extracted entities, predicted category/confidence, linked complaints.
- FR16: Pattern/analytics view — trending categories over time, top repeated entities, geo-distribution (if location captured), cluster graph explorer.
- FR17: Manual correction — officer can reclassify or merge/split clusters; system should support feedback for future model improvement (human-in-the-loop).

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | Classification + entity extraction response under ~2–3 seconds per complaint for demo scale |
| Scalability | Architecture should conceptually scale to thousands of complaints/day (batch clustering jobs) |
| Data Privacy | No real PII in the hackathon demo; discuss encryption-at-rest and access control in design even if not fully implemented |
| Explainability | Show why a complaint got its category/priority (key phrases, matched entities) — builds officer trust |
| Usability | Dashboard usable by non-technical officers; minimal clicks to act on a case |
| Reliability | Graceful fallback to manual categorization if model confidence is low |

---

## 8. High-Level System Architecture

```
[Complaint Intake: Web Form / API]
              │
              ▼
   [Preprocessing: language detect,
      normalization, PII masking]
              │
              ▼
   ┌────────────────────────────┐
   │   AI Processing Pipeline    │
   │  1. Classification model    │
   │  2. Urgency scoring         │
   │  3. NER / entity extraction │
   │  4. Embedding generation    │
   └────────────────────────────┘
              │
              ▼
   [Complaint Store / Database]
              │
              ▼
   ┌────────────────────────────┐
   │ Pattern Detection Engine    │
   │  - Entity graph matching    │
   │  - Vector similarity search │
   │  - Clustering (e.g. HDBSCAN)│
   └────────────────────────────┘
              │
              ▼
     [Officer Dashboard (Web UI)]
   Triage queue | Case detail | Graph view | Analytics
```

**Suggested tech stack (hackathon-friendly):**
- **Backend:** Python (FastAPI/Flask)
- **NLP/ML:** Pretrained transformer for classification (fine-tuned or few-shot with an LLM), spaCy/regex for entity extraction, sentence-transformers for embeddings
- **Similarity/Clustering:** FAISS or simple cosine similarity + HDBSCAN/DBSCAN for clustering
- **Database:** PostgreSQL (structured) + a vector store (FAISS/Chroma) for embeddings
- **Frontend:** React (dashboard), with a graph visualization library (e.g., react-force-graph or vis.js) for cluster views
- **Optional LLM use:** Use an LLM API for zero/few-shot classification, summarization of complaint clusters ("what is this fraud ring doing"), and generating officer-readable case summaries

---

## 9. Success Metrics (Demo & Real-World)

| Metric | Hackathon Demo Target | Real-World North Star |
|---|---|---|
| Classification accuracy | >80% on sample/synthetic test set | >90% with continuous retraining |
| Avg. triage time per complaint | Reduced from minutes to seconds (auto pre-sorted) | 50%+ reduction in manual triage time |
| Pattern detection precision | Correctly links planted duplicate/linked test complaints | Reduction in undetected fraud rings |
| Officer satisfaction (qualitative) | Positive feedback from judges/demo users | Adoption rate by cybercrime cells |

---

## 10. User Stories (Sample)

- *As a triage officer*, I want incoming complaints auto-classified and prioritized, so I can act on urgent financial fraud first.
- *As an investigating officer*, I want to see all complaints linked to a specific UPI ID or phone number, so I can build a case against an organized fraud ring.
- *As a supervisor*, I want a dashboard of trending scam types this week, so I can issue a public advisory or reallocate staff.
- *As a citizen*, I want an acknowledgment with a reference number right after filing, so I know my complaint is in the system.

---

## 11. Hackathon MVP Build Plan (Suggested Timeline)

| Phase | Time | Deliverable |
|---|---|---|
| Setup & data | Hours 0–3 | Synthetic complaint dataset, schema, repo scaffolding |
| Core AI pipeline | Hours 3–10 | Classification + entity extraction working end-to-end |
| Pattern detection | Hours 10–16 | Similarity search + clustering producing linked-case groups |
| Dashboard | Hours 16–24 | Triage queue, complaint detail, cluster graph view |
| Polish & demo prep | Hours 24–30 | Seed realistic demo scenario (e.g., 1 fraud ring hidden in 50 complaints), pitch deck, walkthrough script |

---

## 12. Risks & Assumptions

- **Assumption:** Synthetic/sample data will be used since real complaint data is sensitive and access-restricted.
- **Risk:** Over-reliance on exact entity matches may miss obfuscated fraud (e.g., slightly altered phone numbers) — mitigate with fuzzy matching.
- **Risk:** False positives in urgency scoring could cause alert fatigue — needs tunable thresholds and officer override.
- **Risk:** Multilingual/code-mixed complaints (Hinglish, regional languages) reduce classification accuracy — plan for translation/multilingual model as a mitigation, flagged as future work if not fully solved in MVP.

---

## 13. Future Roadmap (Post-Hackathon)

- Integration with real portals (e.g., NCRP-style systems), bank/telecom verification APIs for faster account freezing.
- Voice complaint intake with speech-to-text for call-center channels.
- Automated public advisory generation from detected trending scam clusters.
- Feedback loop to continuously retrain models on officer corrections.
- Full compliance layer: audit logs, role-based access, data protection (aligned with India's DPDP Act).

---

*End of PRD*
