# CIPHER-FUSION Context & Domain Knowledge

## Overview
CIPHER-FUSION is an offline cyber fraud investigation prototype built for law enforcement analysts. It provides deterministic, explainable correlation across fragmented digital artifacts (CDR, IPDR, Bank/UPI transactions, Email headers, Android app metadata, Chat exports, and Complaint narratives).

## Key Features & Guarantees
1. **Explainable AI & Deterministic Rules**: Every edge in the evidence graph, every score breakdown, and every item in the Golden-Hour queue contains exact matching reasons and pointers to original source artifacts.
2. **Read-Only Ingestion**: Original raw files are stored with SHA-256 integrity hashes and never modified.
3. **Mule Account & Fund-Flow Analysis**: Traces multi-hop financial transfers, computes fund velocity (time to forward, percentage forwarded), detects N-to-1 fund convergence and 1-to-N fund splitting.
4. **Click-to-Prove Interactive Graph**: Graph edges display full lineage popups showing matching identifiers, confidence, source artifact SHA-256, and row pointers.
5. **PII Masking**: Default display masks phone numbers, account numbers, and email handles (`+91 98****3210`, `ACC-****5678`).
6. **Forensic Report Generation**: Exports PDF summaries and JSON data packages featuring mandatory legal disclaimers:
   *"Forensic-ready investigative summary; final investigative and legal decisions remain with authorized personnel."*
