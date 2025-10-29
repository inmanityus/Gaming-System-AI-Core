# Midjourney (Artlist) Automation Workflow

## Goal
Generate on-brand images and short videos with reproducible settings, while keeping the process portable and properly documented.

## How To Access
Use the **apify MCP** to open the Midjourney workspace on **artlist.io** and sign in with Google (same environment variables as Shutterstock):
- `GOOGLE_EMAIL`
- `GOOGLE_APP_PASSWORD`

> If an API or automation token is provisioned for your account, expose it to the workflow as `MIDJOURNEY_ACCESS_TOKEN` (optional). If no token is available, operate entirely via the web UI—this workflow covers both paths.

## Use When
- You need custom visuals (image or video) that stock libraries can’t provide.
- Rapid concepting or brand-specific styles are required.
- You want reproducible generations with prompts, seeds, and parameters logged.
- You must document usage rights (plan-based) for handoff.

## Optional MCP Shortcuts
- `midjourney`: run prompts, variations, upscales, and downloads directly. Without it, use the Artlist/Midjourney web interface.
- `apify`: chain multi-prompt batches, iterate seeds/aspect ratios, and export logs. Without it, do the same actions manually.
- `filesystem`: persist prompts, seeds, parameter presets, and exported media + receipts into the repo. Without it, store them in your asset library and reference the location.

## Steps

1. **Define the brief**  
   - Specify **subject**, **style/look** (e.g., cinematic, product macro, flat color, photoreal), **mood**, **palette**, **camera** (lens, depth of field), **aspect ratio**, **orientation**, **text/negative space**, **brand constraints**, and **mandatory exclusions**.  
   - Record **intended usage** (web, social, print, OOH, packaging, broadcast), **formats** (still, short form video), and **legal constraints** (e.g., avoid likeness of living persons, trademarks, or protected IP; keep it generative/original).  
   - Save as `brief.md` in the project’s `art/` folder.

2. **Prepare a generation plan**  
   - Create a prompt sheet with columns: `prompt`, `negative_prompt`, `model/version`, `aspect_ratio`, `stylize`, `chaos`, `seed`, `variations`, `video (y/n)`, `duration`, `reference_images (paths/URLs)`, `notes`.  
   - Include 2–3 **prompt variants** per concept (tight, medium, exploratory).  
   - For video: add **camera cues** (pan, tilt, dolly), **motion descriptors** (slow drift, macro glide), **beats/duration**, and **looping (y/n)**.

3. **Generate (images & videos)**  
   - **With MCP `midjourney` or `apify`:**
     - Authenticate via Google using `GOOGLE_EMAIL` / `GOOGLE_APP_PASSWORD`.  
     - If available, set `MIDJOURNEY_ACCESS_TOKEN` for API-like operations.  
     - For each row in the prompt sheet, run:
       - *Stills*: set `--ar`, `--seed` (when reproducibility matters), `--stylize`, and any model switches.  
       - *Videos*: set `--ar`, `--duration`, motion cues, and (if supported) **init image** / **image-to-video** references.
     - Capture response metadata (IDs, seeds, parameters, links) back into the sheet.
   - **Without MCP:**  
     - Use the web UI to enter prompts and parameters, attach any reference images, and trigger upscales/variations.  
     - Manually paste returned IDs/seed/params into the sheet.

4. **Iterate & refine**  
   - Run **Variations (V1–V4)** to explore composition; **Upscale** for final detail; use **zoom/outpaint** or **inpaint** tools for layout fixes (e.g., extend background or remove artifacts).  
   - For video, test **shorter drafts** first (e.g., 3–5s) before final durations; adjust motion intensity if artifacts appear.  
   - Keep an **A/B grid**: 1 winner + 2 runners-up per concept.

5. **Compliance & review**  
   - Check each candidate for **brand fit, accessibility, inclusivity**, legibility of any embedded text, and **artifact scan** (hands, eyes, text, product details).  
   - Confirm output respects **usage constraints** (e.g., no real-person likenesses, no logos). Flag anything questionable for revision.

6. **Approve & export**  
   - Export final stills as **PNG** (master) + **JPG** (delivery) and videos as **ProRes / high-bitrate MP4** (master) + platform-ready encodes.  
   - Name with a strict convention:  
     `proj_slug/channel/concept/version/AR/seed/size.ext`  
     Example: `orion_site/hero/metallic-bloom/v3/ar16x9/seed1234/4k.png`  
   - Save **source grids/renders** alongside finals for provenance.

7. **Document rights & provenance**  
   - Create/update `license_ledger.csv` (even for AI assets) with:  
     `asset_path, generated_on, tool=Midjourney(Artlist), account_email, plan_tier, prompt, negative_prompt, seed, params, model/version, usage_notes`.  
   - Record your **plan tier** and any **enterprise terms** that govern commercial use; note any attribution requirements or redistribution limits.  
   - Add a **provenance note**: “AI-generated via Midjourney on Artlist; no third-party trademarks or identifiable individuals prompted or used.”

8. **Handoff**  
   - Deliver finals + ledger + prompt sheet to the project folder.  
   - Include a short `rationale.md` explaining why generative assets were chosen (e.g., unique style, faster iteration) and any limitations accepted.

## Outputs
- Curated set of **approved images/videos** stored with the project (masters + delivery formats).
- A **prompt & parameter log** enabling exact regeneration (prompts, seeds, model, AR, stylize, chaos, video settings).
- A **license/provenance ledger** capturing account/plan and usage notes.
- **Notes** explaining why generative media was selected over stock, with risk/brand checks documented.

---

### Quick-Start Checklists

**Image Preset (safe baseline)**
- `--ar 4:5` or `16:9`  
- `--stylize 100–250` (balanced)  
- `--seed` (set for reproducibility)  
- Negative prompt: artifacts to avoid (e.g., “extra fingers, watermark, text”).  
- Two prompt variants: “tight” vs “cinematic descriptive”.

**Video Preset (draft)**
- Duration 3–5s, `--ar 9:16` or `16:9`  
- Motion cue: “subtle camera drift”  
- If supported, init image → video for layout lock  
- Export low-res proof first; only upscale after approval.

---

### Notes & Caveats
- Usage rights for AI-generated outputs depend on your **account plan/terms**. Record your plan tier in the ledger and link to the governing terms in project notes. When in doubt, route to legal for approval.  
- Avoid prompts likely to generate protected logos, distinctive characters, or celebrity likenesses. Prefer abstract descriptors or fictionalized elements.  
- If Midjourney/Artlist can’t meet a specific compliance or fidelity requirement, fall back to the **Shutterstock** workflow to source licensed assets.

---

### Example Folder Structure
```
/assets
  /midjourney
    /brief
      brief.md
    /runs
      prompt_sheet.csv
      license_ledger.csv
    /renders
      /conceptA
        grid_v1.png
        final_seed1234_4k.png
        final_seed1234_9x16.mp4
    rationale.md
```
