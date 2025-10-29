# Shutterstock Automation Workflow

## Goal
Source licensed imagery when free or AI-generated assets are insufficient, while keeping the process portable.

## How To Access
Use the apify MCP to go to the Shutterstock and login using my Google Login with the username being the environmental variable 
GOOGLE_EMAIL and the password being GOOGLE_APP_PASSWORD There is also the SHUTTERSTOCK_ACCESS_TOKEN environmental 
variable for API access.

## Use When
- Legal or brand guidelines require licensed assets.
- The `generate_ai_images` workflow could not deliver the required look.
- You must document license details for handoff.

## Optional MCP Shortcuts
- `shutterstock`: search and download approved assets. Without it, use the Shutterstock web interface.
- `apify`: automate complex searches or bulk downloads. Without it, perform the same actions manually.
- `filesystem`: track selections and license receipts inside the repo. Without it, store them in your asset library and reference the location.

## Steps
1. Define the brief
   - List subject, style, mood, orientation, text space, and mandatory exclusions.
   - Record intended usage (web, print, campaign) and any legal constraints.
2. Search
   - With MCP access, query Shutterstock using the brief and collect candidate IDs.
   - Without MCP, search via the browser and bookmark or export shortlisted assets.
3. Review
   - Check each candidate for composition, accessibility, inclusivity, and brand fit.
   - Avoid duplicates, watermarks, or assets already owned unless reuse is intentional.
4. License and download
   - Purchase or allocate licenses within your Shutterstock account.
   - Save the original files and license receipts in the project assets folder.
5. Document
   - Maintain an index containing asset ID, usage rights, expiry (if any), and where the asset appears.
   - Share the index with the team so future work respects the license terms.

## Outputs
- Licensed assets stored with the project.
- License ledger capturing IDs, usage restrictions, and renewal reminders.
- Notes explaining why licensed media was chosen over generated alternatives.
