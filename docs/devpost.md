# Devpost paste

**Track:** The Collaborative Partner

GreenChain is a Collaborative Partner for GHG close. An analyst drops mixed evidence (ERP CSV, PDF bills, invoice photos). Gemini 3.7 Flash on ADK drafts a complete inventory in the background via MCP factor/ERP tools, then streams A2UI widgets only for material judgments. Overrides are stored in Firestore so the next period follows this company’s audit style without re-asking.

## Features

- Autonomous draft from a multimodal period pack (CSV + PDF + photo) before any question
- FastMCP HTTP service on the ADK agent's tool list (ERP, factors, persist, memory) — a running HTTP service, not only compatible wrappers
- A2UI v0.9 ExtractionConfirm from Python (`pipeline/a2ui.py`) for the planted kWh/MWh conflict
- Company override memory; silent second run with a Policy applied chip
- Three Cloud Run services (Next.js + Python ADK + FastMCP), Secret Manager-ready, no keys in the repo
- Vertex `gemini-3.7-flash` `generateContent` on Run audit / Confirm when credentials are present; deterministic fallback otherwise

## Built with

Gemini 3.7 Flash (Vertex AI) · Google ADK · Cloud Run · Firestore (file fallback locally) · FastMCP HTTP · Next.js App Router · A2UI v0.9 basic catalog

## Data

Demo-only Northwind Energy 2025 pack in `/fixtures` (ERP CSV, generated utility PDF, diesel receipt image, DESNZ/DEFRA-shaped factors). Not a licensed factor extract.

## Learnings

The Collaborative Partner track is won by doing the chore first. Chat-before-draft fails the demo. Planting one material unit conflict and remembering the answer is a clearer “adapts to how this user thinks” proof than a second memory agent.
