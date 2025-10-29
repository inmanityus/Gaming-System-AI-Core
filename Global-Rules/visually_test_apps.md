# Visually Test Apps

## Goal
Perform a deep visual analysis of the frontend of either a mobile app or of a website frontend.  The goal
is to ensure that the current frontend app or site meets all current UI/UX best practices and is properly 
integrating the current stylesheet and meets or exceeds the project PRD.

## Use When
- You need confidence in layout, accessibility, and navigation before a release.
- The project moved to a new environment and visual regressions might appear.
- Frontend work finished and you want a thorough UX validation loop.

## Available Tools 
### MCP Servers
- 'apify': automate access to specified websites
- 'exa': perform web searches with developer-friendly search results
- 'filesystem': save artifacts (screens, notes, diffs). Without it, store them locally and attach later.
- 'mobile-mcp-android': test cross-platform or android native mobile apps - see Run-Mobile-MCP-Android workflow
- 'openrouterai': provides access to a range of other AI models and services
- 'perplexity-ask': Use to perform advanced web queries to obtain detailed, AI-oriented contextualized results
- 'Playwright': automate navigation and screenshots. Without it, browse manually and capture images yourself.
- 'puppeteer': provides deep Javascript control over web pages - great for automating website interfaces
-  'Ref':  current and relevant documentation for APIs, services, libraries, and frameworks
- 'sequential-thinking': enables structured, step-by-step reasoning, breaking down complex problems into manageable components for better planning, analysis, and decision-making
 ### Tools and Extensions
- 'Shutterstock': find images and videos - please see the Shutterstock-Automation-Workflow
- 'Midjourney': use to create AI-generated visual content - please see Midjourney-Automation-Workflow and 'generate_ai_images' workflow

## Steps
1. Collect context
   - If a Visual-Testing-Context.md file does not exist in the root of the project then run the following sub steps and save the results as Visual-Testing-Context.md
     - Confirm project purpose, target devices, and key journeys from the sole PRD file that will be found in the root directory.  
       - Note that the PRD file might be a text or MD file so look for the case-sensitive term 'PRD' in the filename.
     - Perform online searches using available MCP options to determine best practices and optimal UI/UX approaches for the given frontend project.
     - Locate the main stylesheet - most often included in the stylesheets subfolder - to ensure it is properly applied to the frontend
       - Inspect the stylesheet if this is a website to ensure mobile and tablet options are included and, if not, add those in based on best practices.
       - If the stylesheet contains multiple options, schemes, etc:
         - First look for an indicator in the main app page that determines this selection
         - If no determination can be made, then prompt the user to choose one and then add that selection to the main page of the app tp ensure proper application.
   - If the Visual-Testing-Context.md file does exist, then load it as your current context.
2. Prepare the runtime
   - Install dependencies and start the dev server (for example `npm run web`, `yarn dev`, `expo start --web` or use the mobile-mcp-android MCP).
     - When launching this workflow, ensure that you are monitoring the output so you can capture any errors
   - Check to see if the frontend projects relies on any other project, for example a backend, and launch those projects BEFORE starting the frontend
   - If any errors occur during this process then launch the add_update_and_run_tests workflow
   - Note the local URL and required credentials.
3. Initial Check
   - With Playwright, record a route list and capture screenshots. Without it, manually walk the journeys and take captures.
     - If you have access to puppeteer, then use it to click on options within the page to submit forms, pop up windows, etc.  Test form validation and look at any responses at separate screenshots.
   - Compare the screenshot of each page against the context that was collected and modify the code to address any issues
     - All code changes should be minimized to only address given issues while always attempting to centralize common constructs - for example using a UI service for a common menu
     - Prioritize the user experience and minimize load times
     - Use normal image searches, Shutterstock and Midjourney to add images and videos - prioritizing free options and then the less expensive of licenses vs. AI-generated content to achieve optimal interfaces
   - If there are issues, then make the changes, reload the page, take a new screenshot and check the page again thus defining an initial loop to ensure the page meets expectations
     - If the page causes errors either on the page or during load then run the add_update_and_run_tests workflow.
   - Repeat this process for all pages until all issues are overcome or you cannot fix an issue and log the outcome of testing in a simple table, called Visual Tests, showing Pass/Fail and, for Fails, the outstanding issue.
4. UX Check
   - Now go back through each page and, with Playwright, record a route list and capture screenshots. Without it, manually walk the journeys and take captures.
   - Grade this screenshot against best UI/UX practices with the grade of A equating to meet or exceeds all best practices to C meaning that the page is meeting the average number of best practices to F meaning the page fails completely to meet best practices
   - For all pages not obtaining at least a B (or a specific grade if entered by the user), modify the page to progressively follow more best practices - prioritizing simple changes over more complex ones.
     - All code changes should be minimized to only address given issues while always attempting to centralize common constructs - for example using a UI service for a common menu
     - Prioritize the user experience and minimize load times
     - Use normal image searches, Shutterstock and Midjourney to add images and videos - prioritizing free options and then the less expensive of licenses vs. AI-generated content to achieve optimal interfaces
   - After each change, take another screenshot, grade that screenshot and then repeat until the page obtains at least a grade of B
     - If a given change causes errors, revert those changes and move to the next change until you have run through your list of suggested changes for that page noting that a given page might not ever reach at least a B.
   - Repeat this process for all pages.
   - Once done, create a table of results, titled Page Scores, and list each page and the final grade that page achieved.
5. Share results
   - Provide a single summary that includes both tables and save it to a Results subfolder in the format Visual-Test-Run- and the current date timestamp as a .md file.
   - Make sure to delete all screenshots and associated testing artifacts at the end of this run.
