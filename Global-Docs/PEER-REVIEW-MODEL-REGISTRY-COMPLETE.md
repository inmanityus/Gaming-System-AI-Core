# Universal Model Registry - Complete Peer Review Report

**Review Date**: November 19, 2025  
**Reviewers**: GPT-5.1 (OpenAI) + Gemini 3 Pro Preview (Google)  
**Registry Version**: 2.0  
**Status**: ✅ Reviews Complete - Implementing Fixes

---

## Executive Summary

Both top-tier models (GPT-5.1 and Gemini 3 Pro Preview) reviewed the Universal Model Registry update. They identified:
- **Critical Issues**: 8 (must fix)
- **High Priority**: 12 (should fix)
- **Medium Priority**: 8 (nice to have)

**Overall Assessment**: Strong foundation, but needs structural improvements for production use.

---

## Critical Issues Found (MUST FIX)

### 1. Provider Count Mismatch (Both Reviewers)
**Issue**: Claims "10 Direct API providers" but only lists 9  
**GPT-5.1**: "Either one provider is missing or the '10' is incorrect"  
**Gemini 3 Pro**: "Resolve the list discrepancy immediately"

**Fix**: Add xAI/Grok Direct API (X_AI_API_KEY) - user should configure
**Count**: Should be 11 total (10 Direct + OpenRouter unified gateway)

### 2. Missing Major Providers (Gemini 3 Pro)
**Issue**: Missing critical enterprise providers  
**Gemini 3 Pro**: "Not seeing AWS Bedrock. If you have Azure, omitting Bedrock is a blind spot"

**Missing**:
- AWS Bedrock (major Anthropic/Claude host for VPC isolation)
- Mistral Direct API (MISTRAL_API_KEY for GDPR-strict deployments)
- Cohere (Command R - critical for RAG/reranking)
- Together AI (if supporting open-source hosting)

**Fix**: Add to registry with "User should configure" status

### 3. Benchmark Source Vagueness (GPT-5.1)
**Issue**: "Perplexity research" too vague  
**GPT-5.1**: "There should be: paper/report title, eval date, SWE-Bench variant, exact configuration"

**Fix**: Add proper citations:
- Benchmark variant (Full vs Lite vs Verified)
- Evaluation date (2025-11-xx)
- Source link or paper title
- Configuration notes (temperature, tools allowed, etc.)

### 4. Azure Endpoint Hardcoded (Both Reviewers)
**Issue**: Personal project URL in registry  
**Gemini 3 Pro**: "Provide a templated form and warn users to plug in their own project"  
**GPT-5.1**: "Avoid hard-coding a personal project URL in public docs"

**Fix**: Template as:
```
https://{YOUR-PROJECT}.services.ai.azure.com/api/projects/{YOUR-PROJECT-ID}
```

### 5. Data Sovereignty Warning Missing (Gemini 3 Pro - CRITICAL)
**Issue**: China-hosted models not flagged  
**Gemini 3 Pro**: "Moonshot/DeepSeek/GLM are China-hosted. Sending PII may violate compliance. Flag as Region: CN"

**Fix**: Add data sovereignty tags:
- DeepSeek: Region CN, PII Warning
- Moonshot/Kimi: Region CN, PII Warning
- Z.AI/GLM: Region CN, PII Warning

### 6. Context Window Ambiguity (GPT-5.1)
**Issue**: "10M context" unclear  
**GPT-5.1**: "Is that total tokens? Effective attention? Marketing max vs tested stable limit?"

**Fix**: Specify:
- Advertised max
- Tested stable
- Whether includes output

### 7. Access Methods Overclaim (GPT-5.1)
**Issue**: Claims "ALL access methods" but proprietary models not in Ollama  
**GPT-5.1**: "This line is almost certainly factually incorrect"

**Fix**: Change to "All **applicable** access methods documented per model"

### 8. MoE Parameter Confusion (GPT-5.1)
**Issue**: Total params vs active params not distinguished  
**GPT-5.1**: "MoE counts are often marketing numbers (total), not active params"

**Fix**: Document both:
- Total params: 400B
- Active per token: 17B
- Architecture: MoE

---

## High Priority Issues (SHOULD FIX)

### 9. No Routing Logic (Gemini 3 Pro)
**Issue**: Multiple paths to same models (OpenAI Direct + Azure + OpenRouter)  
**Gemini 3 Pro**: "Risk: Double billing and split usage limits. Define Preferred_Route"

**Fix**: Add routing priority per model

### 10. Preview Status Unclear (GPT-5.1)
**Issue**: Gemini 3 Pro Preview stability unknown  
**GPT-5.1**: "Mark clearly as preview: true, stability: experimental"

**Fix**: Add status field (preview, GA, deprecated)

### 11. Capability Dimensions Missing (GPT-5.1)
**Issue**: Only context/params described  
**GPT-5.1**: "Should capture: modalities, tool_calling, structured_output, system_prompt_support, streaming"

**Fix**: Add capability matrix per model

### 12. Benchmark Variants Not Specified (GPT-5.1)
**Issue**: SWE-Bench Full vs Verified vs Lite unclear  
**GPT-5.1**: "Specify variant, date, harness, source/link"

**Fix**: Add benchmark metadata section

### 13. Missing Cost Normalization (Gemini 3 Pro)
**Issue**: Pricing format varies  
**Gemini 3 Pro**: "Add cost_per_1m_tokens normalized for automated routing"

**Fix**: Standardize all costs to per-1M-token format

### 14. Perplexity Usage Confusion (Gemini 3 Pro)
**Issue**: Perplexity via MCP vs Direct API  
**Gemini 3 Pro**: "Perplexity via MCP implies Tool (Search), not raw model provider"

**Fix**: Clarify Perplexity is for search augmentation, not primary generation

### 15. NVIDIA vs Ollama Conflation (Gemini 3 Pro)
**Issue**: Both listed as "inference engines"  
**Gemini 3 Pro**: "Distinguish: NVIDIA (speed/cloud) vs Ollama (privacy/free). Different hardware requirements"

**Fix**: Separate cloud hosting from local hosting clearly

### 16. Missing Embeddings/Rerankers (GPT-5.1)
**Issue**: Only chat models covered  
**GPT-5.1**: "Missing: Embedding models, Rerankers, Vision-only, ASR/TTS, Specialized math/planning, Guardrails"

**Fix**: Add modality sections or mark as "out of scope"

### 17. Tier System Needed (Gemini 3 Pro)
**Issue**: No model tiers for automated selection  
**Gemini 3 Pro**: "Add tier field: S-Tier (complex logic), A-Tier (general), B-Tier (classification)"

**Fix**: Add tier classification

### 18. No Fallback Strategy (Gemini 3 Pro)
**Issue**: What happens if primary API fails?  
**Gemini 3 Pro**: "Add fallback_id: If OPEN_AI fails, route to AZURE"

**Fix**: Add fallback routing

### 19. Authentication Details Missing (GPT-5.1)
**Issue**: Header formats not documented  
**GPT-5.1**: "Document: Required headers (api-key, Authorization: Bearer), where to obtain keys"

**Fix**: Add auth method per provider

### 20. Model Name Inconsistency (GPT-5.1)
**Issue**: Naming varies  
**GPT-5.1**: "Standardize: 'Gemini 3 Pro (Preview)' vs 'Gemini 3 Pro Preview'"

**Fix**: Choose one convention throughout

---

## Medium Priority Issues (NICE TO HAVE)

### 21. Schema Versioning (Both Reviewers)
**Issue**: No registry schema version  
**Fix**: Add schema version (v2.0) and changelog

### 22. Rate Limiting Not Documented (Gemini 3 Pro)
**Issue**: No quota/rate limit info  
**Fix**: Add per-provider rate limits

### 23. Regional Endpoints (Gemini 3 Pro)
**Issue**: No region-specific endpoints  
**Fix**: Add Azure regions, Google regions, etc.

### 24. Benchmark Source Links (GPT-5.1)
**Issue**: No clickable links to benchmark papers  
**Fix**: Add URLs to SWE-Bench, GPQA, AIME papers

### 25. Tool Use Capabilities (GPT-5.1)
**Issue**: Which models support function calling?  
**Fix**: Add tool_calling: true/false per model

### 26. JSON/Structured Output (GPT-5.1)
**Issue**: Which models guarantee JSON?  
**Fix**: Add structured_output capabilities

### 27. Streaming Support (GPT-5.1)
**Issue**: Which models support streaming?  
**Fix**: Add streaming: true/false

### 28. License Information (Gemini 3 Pro)
**Issue**: Open-source license info incomplete  
**Fix**: Add license field (MIT, Apache 2.0, Llama 3, etc.)

---

## Key Insights from Reviewers

### GPT-5.1 Key Quotes:

> "SWE-Bench scores ~75–78% would represent a major step change from 2024 SOTA (~30–50%). Plausible by late 2025, but you must back this with a citation, not just a name-drop."

> "MoE counts are often marketing numbers (total parameters), not 'active parameters per token.' To avoid misleading users, distinguish: total_params vs active_params_per_token."

> "The claim 'ALL access methods documented' is almost certainly factually incorrect. Many proprietary models are NOT available in Ollama."

### Gemini 3 Pro Key Quotes:

> "You have built a 'God Mode' registry with access to everything. However, without a strict Routing Logic Layer and Compliance Tags, this will lead to unpredictable costs and data leaks."

> "Not seeing AWS Bedrock. If you have Azure Foundry, omitting Bedrock is a blind spot."

> "China-hosted models (DeepSeek, Moonshot, GLM): Sending PII may violate compliance protocols. These models should be flagged Region: CN."

> "Gemini 3 Pro Preview: Previews often have lower rate limits and data retention policies unsuitable for production."

---

## Implementation Priority

### Phase 1: Critical Fixes (Immediate)
1. ✅ Fix provider count (add xAI direct to list)
2. ✅ Template Azure endpoint
3. ✅ Add data sovereignty warnings
4. ✅ Clarify "applicable" access methods
5. ✅ Add benchmark source citations
6. ✅ Distinguish total vs active params for MoE
7. ✅ Add context window details (advertised vs tested)

### Phase 2: High Priority (This Session)
8. ⏳ Add missing providers (AWS Bedrock, Mistral Direct, Cohere)
9. ⏳ Add routing priority/fallback logic
10. ⏳ Add tier classification (S/A/B tier)
11. ⏳ Add capability matrix (modalities, tool use, streaming)
12. ⏳ Clarify Perplexity usage (tool vs model)

### Phase 3: Medium Priority (Next Update)
13. ⏳ Add rate limiting info
14. ⏳ Add schema versioning
15. ⏳ Add license info
16. ⏳ Add embeddings/rerankers section

---

## Validation Checklist

After implementing fixes:

- [ ] Provider count matches actual list
- [ ] All endpoints are templated (no personal URLs)
- [ ] Data sovereignty flags on China-hosted models
- [ ] Benchmark sources have citations with dates
- [ ] MoE models show total AND active params
- [ ] Context windows show advertised AND tested limits
- [ ] Access methods marked as "applicable per model"
- [ ] Preview models marked with stability warnings
- [ ] Routing priority defined for overlapping access
- [ ] Tier system implemented for automated selection

---

## Sign-Off

**Reviewed By**:
- ✅ GPT-5.1 (OpenAI) - 5,535 tokens reasoning + recommendations
- ✅ Gemini 3 Pro Preview (Google) - 2,903 tokens reasoning + arch review
- ✅ Claude 3.5 Sonnet (Implementation)

**Verdict**: Excellent coverage with critical fixes needed before production use

**Next Steps**: Implement Phase 1 (Critical) fixes immediately

---

**Report Location**: C:\Users\kento\.cursor\Deployment\Projects\PEER-REVIEW-MODEL-REGISTRY-COMPLETE.md


