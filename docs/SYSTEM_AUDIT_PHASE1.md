# ERPGENEX AI Employee — System Audit & Architecture (Phase 1)

## Executive Summary

`omnexa_ai_employee` is the autonomous AI employee layer for ERPGENEX. Phase 1 delivers:

- Hybrid local/cloud routing engine
- Six role-based agents (Sales, Support, Healthcare, Education, Tourism, Finance)
- Provider registry (Ollama, OpenAI, Claude, Gemini, DeepSeek, Kimi, Azure, vLLM, LM Studio)
- Conversation ledger with audit trail
- OCR / Vector / Channel configuration DocTypes
- Ecosystem audit API and workcenter dashboard

## Installed Ecosystem (detected at audit time)

- Core: `omnexa_core`, `omnexa_customer_core`, `omnexa_intelligence_core`, `omnexa_experience`, `omnexa_n8n_bridge`
- Verticals: trading, healthcare, education, tourism, restaurant, services, manufacturing, construction, agriculture, accounting, and 30+ additional ERPGENEX apps

## Gap Analysis (initial)

| Area | Severity | Action |
|------|----------|--------|
| AI Providers | High | Configure at least one Local (Ollama) and one Cloud provider |
| Channels | Medium | Add WhatsApp/Telegram channel accounts |
| RAG | Medium | Configure AI Vector Store (Qdrant/Chroma/pgvector) |
| OCR | Low | Register PaddleOCR/Tesseract/Azure OCR provider |
| n8n workflows | Medium | Use `omnexa_n8n_bridge` for complex multi-step agents |

## Architecture

```
Customer Channel → AI Conversation → Hybrid Router → AI Provider
                                    ↓
                          Intelligence Action Queue (optional approval)
                                    ↓
                              ERP Doc / API Action
```

## Hybrid Routing Rules (default)

| Rule | Target | Keywords |
|------|--------|----------|
| Simple ERP Lookup | Local | product lookup, stock balance |
| Document Summary | Local | summarize, short answer |
| Legal Analysis | Cloud | legal, contract, compliance |
| Large Context | Cloud | full report, all transactions |

## Security

- API keys stored as Password fields
- RBAC: `System Manager`, `AI Employee User`
- No secrets in logs or chat meta (provider name only)

## Next Phases

1. Wire OCR engines (PaddleOCR, Tesseract SDK)
2. Vector RAG ingestion pipeline
3. WhatsApp/Telegram webhooks
4. Voice STT (Whisper) + intent detection
5. ERP tool-calling (quotation, appointment, ticket creation)
