# Generate Images and Videos

## Goal
Produce project-ready visuals using the available image and video services while keeping requirements portable.

## Use When
- You need hero images, thumbnails, or concept art for the current project.
- Licensing must be clear and recorded alongside the assets.
- You want options that work whether MCP servers are available or not.

## Available Tools 
### MCP Servers
- 'apify': automate access to specified websites
- `exa`: perform web searches with developer-friendly search results
- `filesystem`: save artifacts (screens, notes, diffs). Without it, store them locally and attach later.
- 'mobile-mcp-android': test cross-platform or android native mobile apps - see Run-Mobile-MCP-Android workflow
- 'openrouterai': provides access to a range of other AI models and services
- 'perplexity-ask': Use to perform advanced web queries to obtain detailed, AI-oriented contextualized results
- `Playwright`: automate navigation and screenshots. Without it, browse manually and capture images yourself.
- 'puppeteer': provides deep Javascript control over web pages - great for automating website interfaces
-  'Ref':  current and relevant documentation for APIs, services, libraries, and frameworks
- 'sequential-thinking': enables structured, step-by-step reasoning, breaking down complex problems into manageable components for better planning, analysis, and decision-making
 ### Tools and Extensions
- 'Google' - free images, using basic search options
- 'Shutterstock': find images and videos - please see the Shutterstock-Automation-Workflow
- 'Midjourney': use to create AI-generated visual content - please see Midjourney-Automation-Workflow

## Steps
1. Collect requirements
   - Capture prompt, orientation, color constraints, and usage context.
2. Choose a generator
   - Use Apify actors for Shutterstock and Midjourney for high fidelity, final versions, as videos.
   - If no automation is available, use the provider web UI and download the results manually.
3. Generate
   - Keep prompts versioned (for example in `docs/prompts/`). Record model, resolution, and seed if available.
   - Run a small batch and note the command or MCP call used. Re-run until you have usable options.
4. Review and annotate
   - Check for brand alignment, accessibility, and license rules. Mark AI-generated versus licensed assets clearly.
   - For licensed imagery, log asset IDs and license terms beside the files.
5. Image Preferences
   - Free images and videos from Shutterstock only if they meet design and UI/UX best practice
   - Then AI generated images via Midjourney but only using the highest quality settings so they are not obviously AI-generated
   - Then licensed Shutterstock
6. Video Preferences
   - Shutterstock first and then OpenAI/Web searches
7. General Preferences
   - High visual impact, photo-realistic, high end videos
   - Not too high in terms of cost but never sacrifice quality for price
5. Deliver
   - Export in required formats (PNG, JPG, WebP, MP4) and commit or upload alongside the project.
   - Share a summary covering prompts, selected files, license notes, and suggested follow-up (for example alt text or responsive crops).

## Outputs
- Final image assets stored with the project and named consistently.
- Prompt history and provider details for future reference.
- License or usage notes linked to each delivered asset.
