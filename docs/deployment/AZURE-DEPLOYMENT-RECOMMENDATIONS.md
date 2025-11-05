# Azure AI Model Deployment Recommendations
**Project**: "The Body Broker" Gaming Core  
**Date**: January 29, 2025

---

## RECOMMENDED MODELS FOR DEPLOYMENT

Based on your hierarchical LLM architecture and requirements, deploy these models in Azure AI:

### Tier 4: Orchestration Layer (Cloud LLMs)

These handle story direction, battle coordination, and complex orchestration:

#### **1. GPT-4 Turbo / GPT-4o** (Priority 1)
- **Use Case**: Primary orchestration, story direction
- **Why**: Excellent reasoning, follows instructions well
- **Deployment Name**: `gpt-4-turbo` or `gpt-4o`
- **Tier**: Layer 4 (Orchestration)
- **Cost**: Higher, but worth it for orchestration

#### **2. GPT-4o-mini** (Priority 2)
- **Use Case**: Secondary orchestration, fallback for less critical tasks
- **Why**: Good performance at lower cost
- **Deployment Name**: `gpt-4o-mini`
- **Tier**: Layer 4 (Secondary orchestration)
- **Cost**: Lower cost alternative

#### **3. GPT-3.5 Turbo** (Priority 3)
- **Use Case**: Validation, simple coordination tasks
- **Why**: Very cost-effective for high-volume simple tasks
- **Deployment Name**: `gpt-35-turbo`
- **Tier**: Layer 4 (Validation/Simple tasks)
- **Cost**: Lowest cost option

### Tier 3: Complex NPC Dialogue (If Available)

#### **4. GPT-4** (If Available)
- **Use Case**: Major NPC dialogue (Tier 3 NPCs - bosses, nemeses)
- **Why**: Highest quality for important character interactions
- **Deployment Name**: `gpt-4`
- **Tier**: Layer 3 (Important NPCs only)
- **Cost**: Higher, use sparingly

---

## MICROSOFT-SPECIFIC MODELS

If Microsoft models are available in your Azure AI resource:

### **MAI-1-preview** or **MAI-1-Foundation** (If Available)
- **Use Case**: Try for orchestration if GPT-4 isn't available
- **Status**: May require whitelisting/approval
- **Note**: This is Microsoft's model, may have different capabilities

### **Phi Models** (If Available)
- **Phi-3**: Good for smaller tasks
- **Use Case**: Could work for Tier 3 NPCs if GPT-4 unavailable
- **Limitation**: Smaller context window

---

## DEPLOYMENT STRATEGY

### Minimum Deployment (Start Here)
Deploy these 3 models to start:

1. **GPT-4 Turbo** (`gpt-4-turbo`) - Primary orchestration
2. **GPT-4o-mini** (`gpt-4o-mini`) - Secondary/fallback
3. **GPT-3.5 Turbo** (`gpt-35-turbo`) - Validation/high-volume

### Full Deployment (Recommended)
Deploy all 4-5 models:

1. GPT-4 Turbo - Primary orchestration
2. GPT-4o-mini - Secondary orchestration  
3. GPT-3.5 Turbo - Validation
4. GPT-4 (if available) - Tier 3 NPCs
5. MAI-1 (if available) - Alternative/experimental

---

## HOW TO DEPLOY IN AZURE AI

### Step 1: Go to Azure AI Studio
1. Navigate to: https://ai.azure.com
2. Select your resource: `ai-gaming-core`
3. Go to "Deployments" section

### Step 2: Create Deployment
For each model:

1. Click "Create" or "Deploy model"
2. Select model from catalog:
   - Search for "GPT-4 Turbo" or "gpt-4-turbo"
   - Select the latest version
3. Configure:
   - **Deployment name**: Use lowercase with hyphens (e.g., `gpt-4-turbo`, `gpt-4o-mini`)
   - **Model version**: Select latest
   - **Compute**: Use recommended tier
4. Click "Deploy"

### Step 3: Deployment Names (Important!)

Use these exact deployment names in your code:

```powershell
# Primary orchestration
$primaryOrchestrationDeployment = "gpt-4-turbo"

# Secondary/fallback
$secondaryOrchestrationDeployment = "gpt-4o-mini"

# Validation/simple tasks
$validationDeployment = "gpt-35-turbo"

# Tier 3 NPCs (if deployed)
$tier3NPCDeployment = "gpt-4"
```

**CRITICAL**: Deployment names are case-sensitive and must match exactly!

---

## COST CONSIDERATIONS

### Estimated Costs (Per 1K Tokens)

| Model | Prompt | Completion | Use Case |
|-------|--------|------------|----------|
| GPT-4 Turbo | $0.01 | $0.03 | Primary orchestration |
| GPT-4o-mini | $0.00015 | $0.0006 | Secondary/fallback |
| GPT-3.5 Turbo | $0.0005 | $0.0015 | Validation/high-volume |

### Cost Optimization Strategy

1. **Use GPT-4o-mini** for 70% of orchestration tasks (if quality acceptable)
2. **Use GPT-4 Turbo** for 20% of critical orchestration (story beats, battles)
3. **Use GPT-3.5 Turbo** for 10% of validation/simple tasks

This gives you high quality where needed while controlling costs.

---

## WHAT ABOUT LOCAL MODELS?

**Important**: Azure AI deployments are for **Layer 4 (Orchestration) only**.

For Layers 1-3 (NPC dialogue, customization), you'll use:
- **Local Ollama models** (already have Qwen, Llama models)
- These handle 80%+ of NPC interactions
- Azure models handle only the complex orchestration (20%)

This hybrid approach achieves your 77% cost savings target.

---

## QUICK START CHECKLIST

- [ ] Deploy GPT-4 Turbo (`gpt-4-turbo`)
- [ ] Deploy GPT-4o-mini (`gpt-4o-mini`)
- [ ] Deploy GPT-3.5 Turbo (`gpt-35-turbo`)
- [ ] Verify deployments are "Active"
- [ ] Note exact deployment names (case-sensitive!)
- [ ] Test each deployment with test script
- [ ] Update environment variables with deployment names

---

## TESTING AFTER DEPLOYMENT

Once deployed, test each one:

```powershell
.\scripts\test-azure-ai.ps1
```

Update the script with your deployment names and verify each works.

---

**Recommendation**: Start with the 3 minimum models (GPT-4 Turbo, GPT-4o-mini, GPT-3.5 Turbo). This gives you the full range from high-quality to cost-effective, covering all orchestration needs.

