# Devpost paste

**Track:** The Collaborative Partner

GreenChain is a Collaborative Partner for GHG close. An analyst drops mixed evidence (ERP CSV, PDF bills, invoice photos). Gemini 3.5 Flash on ADK drafts a complete inventory in the background via MCP factor/ERP tools, then streams A2UI widgets only for material judgments. Overrides are stored in Firestore so the next period follows this company’s audit style without re-asking.

## Features

- Autonomous draft from a multimodal period pack (CSV + PDF + photo) before any question
- MCP-compatible ERP and emission-factor tools over a deterministic fixture pack
- A2UI v0.9 ExtractionConfirm (basic catalog) for the planted kWh/MWh conflict
- Company override memory; silent second run with a Policy applied chip
- Two Cloud Run services (Next.js + Python ADK), Secret Manager-ready, no keys in the repo

## Built with

Gemini 3.5 Flash (Vertex AI) · Google ADK · Cloud Run · Firestore (file fallback locally) · FastMCP · Next.js App Router · A2UI v0.9 basic catalog

## Data

Demo-only Northwind Energy 2025 pack in `/fixtures` (ERP CSV, generated utility PDF, diesel receipt image, DESNZ/DEFRA-shaped factors). Not a licensed factor extract.

## Learnings

The Collaborative Partner track is won by doing the chore first. Chat-before-draft fails the demo. Planting one material unit conflict and remembering the answer is a clearer “adapts to how this user thinks” proof than a second memory agent.
