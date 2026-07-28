# Added-Value Analysis

| Differentiator | Classification | Evidence |
|---|---|---|
| Polished reader experience | Partially working differentiator | Strong authored UI; browser E2E absent |
| Side-by-side documents | Partially working differentiator | Two panes, but translated pane is original until export |
| Synchronized scrolling/zoom | Planned but not implemented | Shared page/zoom state; independent scroll containers |
| Block-level editing | Working differentiator, unverified | Persisted manual edits and review action |
| OCR-confidence review | Planned but not implemented | No OCR |
| Completeness reporting | Partially working differentiator | Persisted statuses, but formula/status is inaccurate |
| Image-text replacement | Planned but not implemented | No implementation |
| Glossary / translation memory | Planned but not implemented | No models or APIs |
| Multi-provider support | Working differentiator, unverified | Two real provider adapters |
| Fully local self-hosting | Partially working differentiator | Local services supported; stack not started in audit |
| Multi-format support | Planned but not implemented | PDF only |
| Export quality | Partially working differentiator | Geometry-aware insertion but serious overflow defect |
| Page/block retries | Partially working differentiator | Block fallback; no durable retry workflow |
| Human review workflow | Partially working differentiator | Edit/review fields, no assignment/history/approval |

## Conclusion

**Promising prototype** is the best-supported classification. The auditable
element model and reader/editor can add value beyond command-line PDF translators,
but the current product cannot claim broad document translation, OCR, or reliable
layout preservation. Its strongest route to differentiation is a provider-agnostic
review and completeness layer over mature PDF/OCR engines.
