# Azure AI Troubleshooting Guide
**Issue**: Invalid URI / Hostname parsing error

---

## PROBLEM IDENTIFIED

The error "Invalid URI: The hostname could not be parsed" occurs because:

1. **Incorrect Endpoint Format**: You're using `https://ai-gaming-core.services.ai.azure.com/` but the OpenAI-compatible API requires `https://ai-gaming-core.openai.azure.com/`

2. **Trailing Slash Issue**: Having a trailing slash on the endpoint variable causes URI concatenation problems

---

## SOLUTION

### Option 1: Use OpenAI-Compatible Endpoint (RECOMMENDED)

The OpenAI-compatible endpoint format is:
```
https://{resource-name}.openai.azure.com
```

**Corrected Script**:
```powershell
# Use .openai.azure.com NOT .services.ai.azure.com
$endpoint = "https://ai-gaming-core.openai.azure.com"  # NO trailing slash

$apiKey = "your-api-key"
$deploymentName = "MAI-DS-R1"

$headers = @{
    "api-key" = $apiKey
    "Content-Type" = "application/json"
}

$body = @{
    messages = @(
        @{
            role = "user"
            content = "Test message"
        }
    )
} | ConvertTo-Json -Depth 10

# Construct URI properly
$uri = "$endpoint/openai/deployments/$deploymentName/chat/completions?api-version=2024-02-15-preview"

Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body
```

### Option 2: Use Azure AI Services Endpoint (Newer Format)

If you specifically need the `.services.ai.azure.com` endpoint, the API path is different:

```powershell
$endpoint = "https://ai-gaming-core.services.ai.azure.com"  # NO trailing slash
$apiKey = "your-api-key"
$deploymentName = "MAI-DS-R1"

$headers = @{
    "api-key" = $apiKey
    "Content-Type" = "application/json"
}

$body = @{
    messages = @(
        @{
            role = "user"
            content = "Test message"
        }
    )
} | ConvertTo-Json -Depth 10

# Different path for Azure AI Services
$uri = "$endpoint/openai/deployments/$deploymentName/chat/completions?api-version=2024-06-01"

Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body
```

---

## FINDING YOUR CORRECT ENDPOINT

1. **Azure Portal** → Your AI resource
2. **Keys and Endpoint** section
3. Look for **Endpoint** field
4. It should be either:
   - `https://{name}.openai.azure.com` (OpenAI-compatible)
   - `https://{name}.services.ai.azure.com` (Azure AI Services)

---

## VERIFYING YOUR DEPLOYMENT

From the [Azure AI Models page](https://ai.azure.com/resource/models?wsid=/subscriptions/1935c603-d128-47e0-a7fa-a7c49b214820/resourceGroups/ai-gaming-core/providers/Microsoft.CognitiveServices/accounts/ai-gaming-core/projects/AI-Games&tid=acb1cad2-a48e-408f-9b76-5ada11faab9b):

1. Check if deployment `MAI-DS-R1` exists and is **Active**
2. Verify the deployment name matches exactly (case-sensitive)
3. Confirm the model is deployed to this specific resource

---

## QUICK FIX SCRIPT

Run the test script:

```powershell
.\scripts\test-azure-ai.ps1
```

This script:
- Uses correct endpoint format
- Handles errors gracefully
- Provides troubleshooting tips

---

## COMMON ISSUES

| Error | Cause | Fix |
|-------|-------|-----|
| Invalid URI | Trailing slash or wrong domain | Remove trailing slash, use `.openai.azure.com` |
| 401 Unauthorized | Invalid API key | Check Keys and Endpoint in Azure Portal |
| 404 Not Found | Wrong deployment name | Verify deployment name in Azure Portal |
| 404 Not Found | Deployment not active | Activate deployment in Azure Portal |

---

## UPDATED MODEL SETUP INSTRUCTIONS

The `docs/MODEL-SETUP-INSTRUCTIONS.md` has been updated with the correct endpoint format.

**Key Points**:
- ✅ Use `https://{resource-name}.openai.azure.com` (NO trailing slash)
- ✅ API version: `2024-02-15-preview` or `2024-06-01`
- ✅ Deployment name is case-sensitive
- ✅ Verify deployment is active before testing

---

**Test Your Fix**: Run `.\scripts\test-azure-ai.ps1` to verify the connection works.

