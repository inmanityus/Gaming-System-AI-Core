# Create, Update, and Run Tests

## Goal
Build a reliable, portable test suite that thoroughly tests all functions, pages, functional units, subsystems, projects and overall system

## Use When
- An entire solution needs to be tested
- A specific page, functionality, or project has been added or modified
- A backend data store has been added or changed
- A repo is being moved between environments and the tests must work without custom scripts.
- A deployment has occurred and a Production/Testing deployment must be validated

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
1. Analyze Solution
    - In the open folder, look for each app and determine the type of project it is
      - This includes the general type - database, backend, middleware, frontend
      - This also includes the code used and the intent of the project
    - Organize these hierarchically in your testing plan such that any database will be tested first followed by any backend project, then any middleware project, and then any frontend projects.
      - The flow must go from database to frontend, in order, so projects dependent on other projects are only tested AFTER the projects upon which they are dependent have passed testing.
2. Confirm context
   - If a Project-Testing-Context.md file does not exist in the root, then run the following steps and save it to the root as Project-Testing-Context.md
     - Confirm project purpose, target devices, and key journeys from the sole PRD file that will be found in the root directory.  
         - Note that the PRD file might be a text or MD file so look for the case-sensitive term 'PRD' in the filename.
       - Perform online searches using available MCP options to determine the optimal testing suites to use for each project type.
   - If the Project-Testing-Context.md file does exist, then load it as your current context.
     - If the loaded context does not include one of the discovered apps then re-write the file using the steps above.
2. Capture baseline
   - For each project, look for a Testing folder within that project
     - If the Testing folder exists then load all of those tests and instructions
     - If the Testing folder does not exist:
       - Use best practices and preferred testing suites to install the best automated testing suite for that project and store these choices as instructions in the Testing folder
     - Inspect any existing tests and compare those to the current functions, functional units, subsystems, pages, etc. in that project and update any existing tests to match current code
3. Write Tests
   - Create all new tests from the unit level up through the entire project to ensure a thorough and comprehensive series of tests that cover all possible options
     - Store all of these in the Testing folder for that project.
       - Save the tests in a hierarchical format for ease of re-testing such that the lowest subfolder for a given high-level unit (e.g., a given frontend page or end-to-end RESTful call to DB call) consists of the function tests up to the end-to-end test
     - Always use option like exa and perplexity-ask to aid in understanding how to best test anything you do not understand
     - For databases, use the global database connection rules as they make sense to connect to any local data store
       - Ensure the database for a project exists - prompting the user as needed to provide a name
       - Ensure that all data structures exist - tables, views, procedures, etc. - based on the backend project's requirements
       - Ensure that all test data exists, looking in the PRD for these requirements
     - For all servers:
       - Include load and stress tests
       - Ensure optimal serving options - including singleton vs. other options where it makes sense
     - For backend servers:
       - Ensure that all forward looking calls - e.g. RESTful calls - exist based on the requirements of the project in front of it - be it a middleware server or frontend app
       - Ensure that all database calls are tested
       - Ensure that any intermediary logical functions are tested
       - Ensure that the connections between all forward looking to database calls are tested
     - For middleware servers:
       - Ensure that all forward looking calls - e.g. RESTful calls - exist based on the requirements of the project in front of it - be it a middleware server or frontend app
       - Ensure that all backward looking calls - e.g. RESTful calls - exist based on the requirements of the project in front of it - be it a backend or middleware server
       - Ensure that any intermediary logical functions are tested
       - Ensure that the connections between all forward looking to backward looking calls are tested
     - For frontend tests:
       - Ensure that all calls to the previous project in the hierarchy are tested
       - Look for the root level stylesheets folder and ensure that these stylesheets are properly applied
         - If a given stylesheet does not have mobile and tablet options add those as it makes sense given the project
         - If the stylesheet has multiple options and you cannot find a given option implemented then prompt the user to choose an option and then implement that option
       - Use Playwright and puppeteer to write tests that explore all button, popup, menu, and other interface options
       - Ensure that every function on every page is tested
       - Ensure that every page, and all options on that page, are tested
       - Ensure that any route flows between pages are tested
       - Ensure that the entire frontend app is tested end-to-end
   - Decide how data will be reset: migrations, seed scripts, or teardown hooks.
     - For database calls ensure that you use database rollbacks when possible or reversion scripts as needed
     - Ensure this rollback functionality is extended through all projects so it is callable at every testing level and used between all tests when data is modified
4. Implement tests
   - Never use mock data if a datastore is present
     - If a database is not present then only add mock data to the furthest back server if more than one project
       - In these cases, write all mock data to a file and read from that file for all tests
       - Include a file backup in these cases for ease of data reversion
   - Run the tests from database/backend server through to the frontend
     - If a given test fails, then modify the code to address that specific issue
     - Do not write code beyond the scope of given issue
     - Consolidate common functionality - e.g. data or UI common services - where it makes sense
     - Use a loop to make incremental changes to overcome a given issue until the given test passes or ou cannot fix the issue
       - If you are running a higher level test then re-run all lower tests under that higher level test as you make changes to ensure nothing lower level breaks
     - Continue to make changes until you are unable to fix an issue
       - In these cases, log the location of the error, the level and name of the test, and the general steps attempted.
     - ALWAYS use a timer on ALL tests to ensure you do not get stuck
       - Make the timer run outside of the test in case the test locks up its process
       - Use a timeout that makes sense given the level of the test while minimizing overall testing times.
   - If any end-to-end testing block fails for anything other than the last frontend project, then stop the workflow
     - For the frontend, test all independent end-to-end tests but avoid testing page flows wherein one of the pages has failed
5. Report
   - Output the highest level of pass/fail for each end-to-end test block by project
   - For each end-to-end provide a Red/Green icon indicator of success or failure or a Neutral Not Tested icon for those tests that were not run
   - For all failed end-to-end tests provide the test(s) that failed and include all information outlined previously
   - Save this file in the Testing/Results folder as Testing-Run- the current date timestamp and an .md file.
6. General Rules
    - Always use a timer for ALL commands as you have timeout issues
      - Run the timer outside of the command as many commands can block the process
      - Use the minimum amount of expected time for a command to run plus some reasonable buffer
    - Use your MCP options - including the openrouterai, exa, and perplexity to aid in trying to overcome issues
    - Constantly check your processing to ensure you do not get stuck
    - ALways prompt the user if you are unclear on how to proceed with anything

## Backend Notes
- Prioritize database schema coverage, API contract tests, and rollback paths for migrations.
- Use transactions or truncate helpers so reruns stay clean.
- Record connection info or seed data in docs, not in ad-hoc scripts.

## Frontend Notes
- Confirm the build/start command before launching UI tests.
- Aim for a mix of unit (component), interaction (integration), and user journey (E2E) tests.
- Capture screenshots or logs when UI automation is unavailable and attach them to the summary.

## Outputs
- Updated or newly created tests checked into version control.
- A short report listing executed commands, environment needs, outstanding failures, and next steps.
- Recommendations for additional workflows (for example, provisioning or deployment) once tests are green.
