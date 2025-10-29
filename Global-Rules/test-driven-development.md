# Test Driven Development

## Goal
Take a Product Requirements Document, turn in into Cursor AI digestible Tasks and implement those tasks.

## Use When
- A new solution needs to be created from a PRD
- An existing solution needs to be updated
   
## Pre-Work
**Always start from the root folder**
- Verify that you can see the Global-* folders - if not then run scripts/consolidated-startup.ps1 and try again.  They will always be present but, at times, you cannot see them.
If you do not see .gitignore files in this project, then please add all files currently in this folder, and subfolders, to hierarchical .gitignore files if they would otherwise be added to a git push.  All current folders can be use in whole as none of these files or folders should be included in any push.  The only exception is the stylesheet folder and its content which will be deployed.

## Persona
Please act in the role of an expert is project management, transforming business requirements into technical solutions, and organizing task for AI completion.

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
= 'trivy': enables natural language security scans of code, configurations, and everything related to securing projects
 ### Tools and Extensions
- 'Shutterstock': find images and videos - please see the Shutterstock-Automation-Workflow
- 'Midjourney': use to create AI-generated visual content - please see Midjourney-Automation-Workflow and 'generate_ai_images' workflow
### Length Limitations
 - If you discover that you are slowing down or making more mistakes than usual, it is most likely due to the length of this chat
 - When this happens, please write all notes, context, and instructions into a temporary file - which includes instructions for removing this temp file
 - Either start up a new chat window automatically or, if you are unable to do so, prompt me to start up a new chat and provide me with the prompt to do so along with hte location of the temp file you wrote

## Your Process
1. Project Creation
	- Always ensure that you are in the Root Directory
  - Always Run scripts/consolidated-startup.ps1 at the beginning of each Cursor session 
  - Create a folder called Project-Management and add it into the root directory .gitignore so none of its files or the folder itself are added to any repository
	- Inspect the PRD and the Workflow and reduce the workflow into manageable Tasks that will complete all of the requirements of the PRD - Using the PRD Steps below
	- Create a global Project-Workflow.md Document to enable you to track tasks across the entire scope of this effort
		- In this file, include the Names of the tasks, the inputs required, the expected output and the next step to call depending on the output
		- As tasks are completed, change an icon from Open to Complete for both humans and the AI to track progress.
		- If a given task fails, then change the indicator to Failed and ensure that you reference an Task-Failed.md file for that task failure and indicate which file to open here
	- Each task must include a comprehensive workflow to complete a given task, along with the location of any inputs and the location to place all outputs
	- Feel free to re-use tasks, for example one for running the testing, to optimize task creation.
	- Add all other hooks, links, whatever you need to be able to run all of the tasks automatically
2. For each task, also provide a persona for the AI to use in solving that task and ensure that the AI knows which relevant tools and MCP servers it has available to it
3. Images and Videos
  - Please use the generate_images_and_videos.md file to thoroughly adding in images and videos to all frontend pages
  - Do NOT skip this step and ensure all marketing pages are visually impactful and all other pages follow UX/UI best practices.
4. Visual Testing
	- If the PRD includes a frontend then please ensure that you run that workflow only AFTER all other tasks have been successfully completed
5. Parallel Task Completion
	- If you are able to do so, please open new chat windows and run any tasks that can be run in parallel at the same time
6. Chat Length Issues
	- While completing tasks, please ensure you do not go past recommended chat session lengths
		- If possible, simply open a new chat window and keep going
		- If you cannot open a new chat, then write any context into a .md file and point to it under the next task in the Project-Workflow.md file.
			- The goal is for me to simply load the Project-Workflow.md file in a new Chat window and tell you to continue where you left off
7. Timeouts
	- Quite often, the Cursor IDE fails to report timeouts to you and often gets stuck running commands without letting you know
	- My suggestions is to wrap an independent timer around each command to ensure you continue in the event of IDE failures
		- You will also need to capture any output from the IDE during these command runs
	- If you have a better approach then please use that option instead
8. Everything Must Be Completed
  - Please run ALL parts of the workflow, do not skip anything, do not violate the instructions, and do not skip steps.  Expand things out as makes sense and use all MCP and extensions to aid in your efforts.
  - Note that your initial task is to create all the tasks and main file.  Then, if possible, spin up a new chat window and start running these tasks.  Otherwise, end your session with exactly what I need to type into a new chat window to continue.
9. Logging
  - The Cursor IDE is very prone to connection timeouts that lock up the session
  - At the beginning of each session, after running the scripts/consolidated-startup.ps1 script, create a log file and use it to track your progress
    - Write the log file location and name out so all I need to do is tell the next session "Proceed with the efforts found in [LOG FILE NAME]"
    - If you successfully finished a task then write out a prompt to start the next Task

## PRD Steps
1. Analyze Solution
 - Look for a PRD in the current folder it will have the following sections:
   - Overall Requirements: This section will provide the general intent and business goals of this project
   - Technical Specs: This section will breakdown the solution into high-level apps / servers/ etc
     - Each one of these sections will provide a functional specification
   - Considerations: This section will provide some global issues/concerns/restrictions
   - Deployment Target: This section will provide a functional series of deployment target(s)
   - Updates: If this is an existing solution, then this section will detail what was added to the overall solution by Project (app).
 - Note that the PRD might be in a txt or md format so look for the case sensitive 'PRD' in the filename
 - Note that your first step will be to create a Linux Docker Container inside of which all projects will be built.
2. Perform Research
 - Use exa, perplexity-ask, and Ref to research the best options to implement every project
   - exa will provide developer-friendly search results
   - perplexity-ask will provide high contextual answers to queries
   - Ref is ideal to obtain up-to-date documentation for APIs, services, and libraries.
   - Use oenrouterai to discuss options with other AI models to ensure you use the best options
     - Please keep these discussions within a nominal length for cost purposes
   - Ensure that you research best options.practices within the scope of connecting all projects together as well as how to solve each project individually
   - For databases, the PRD will provide its preference and thus you must ensure that a global version of that data store is accessible - look for a global rule to aid in this endeavour
   - For all servers:
     - Research the most widely applicable API options such as RESTful calls across security and support for future projects
     - Research server optimization, stress and load concerns, and any other global options, settings, and configuration.
     - Research project-specific best practices, approaches, and code options - including test harnesses/suites that might be used and project launch such as Expo
   - From frontend apps:
     - Look for a root stylesheets folder and any stylesheets in that folder and research how to best implement that stylesheet
       - Stylesheets might be a tailwind, typescript, and/or css format - or whatever else applies to the current project.
       - Some stylesheets might have a Light and Dark Mode for implementation via, as one example, a button:
           ```
           <script>
             const root = document.documentElement;
             function toggleTheme(){
               root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
             }
           </script>
           <button class="btn" onclick="toggleTheme()">Toggle theme</button>
           ```
     - For anything missing from the stylesheet - for example mobile/tablet options, research the best implementation options
     - If the stylesheet has multiple schemas or skins, prompt the user to select the one they want and then research how to implement that option.
     - If you think the stylesheet can be implemented better (for example exporting theme tokens to a json file, wiring up a tailwind.config.js file to map token to CSS variables, and adding a tiny script to sync .ts and tailwind files) proceed accordingly to best practices
2. Implement The Infrastructure
 - Start by creating the Linux or Windows Docker Container 
   - Look in the global-cursor-repo/docker-templates folder for a matching container-template
     - Note that the choice of container type is predicated on the projects, code being used, and ease of deployment
   - If the template exists and is not more than 6 months old, then create the container using that template
   - If the container does not exist, or is moire than 6 months old:
     - Use best practices and approaches that you researched to generated a new template
     - Delete the existing matched template if it is there and over 6 months old
 - Then create all apps - each in their own subfolder
 - For each project/app:
   - Implement all global files, setups, launching code (e.g. Expo), testing suites, and everything required to run that project
     - Include instructions and insights that will aid you in running the add_update_and_run_tests workflow
     - Include any rules, snippets, and other information that will help with timeouts, application or standards, and so forth in case this chat crashes
   - For the database backend, create the main database - using the PRD and any global rule to this end and ensure connectivity to the project directly connected to that database
   - Add in testing scripts and or pages/files as test artifacts that enable end-to-end connectivity tests and run those tests to ensure all projects load and work together
     - Correct all issues and run these basic tests until everything works
     - Delete all test artifacts once these tests all pass
3. Test-Driven Development Process 
 - Using the PRD, build the most basic parts of this solution first
   - For a website, create the main page
   - For a mobile app, create the initial page
   - Run the add_update_and_run_tests workflow on this minimum setup
   - Only add backend code, as needed, to support your current efforts
    - Run the add_update_and_run_tests workflow on these apps / server / databases / etc. as well for end-to-end incremental testing.
 - Slowly add functional units (for example new pages in an app/website) and run the add_update_and_run_tests workflow between each test.
   - Always obtain the complete requirements for adding new functionality and use that to move from the frontend to the back
   - Only add the data constructs (tables, views, functions, procedures, etc.) required to fulfill the current set of frontend features
   - Only add those backward facing/DB calls and front facing (e.g. RESTful) calls required to fulfill the new functionality.
   - Only add logic specific to the new functionality on the servers.
   - These should all be organized in end-to-end injections of functionality both within and across projects.
   - You must run the add_create_and_run_tests between each addition and, if that workflow fails, modify whatever needs to be changed to overcome the resultant issues
   - Use the trivy to ensure the existing projects all pass security checks
     - If they fail, then adjust the code and run the add_update_and_run_tests workflow again
   - As a final check, launch all servers from the closest to the database to the frontend and verify everything works by using Playwright and puppeteer or options such as the mobile-mcp-android MCP server for cross platform/Android apps to thoroughly exercise the frontend app.
 - Use Your Resources
   - Use the exa and perplexity-ask to obtain more information on anything unknown or unclear
   - Use the openrouterai to leverage other AI models and services to discuss possible options and approaches to enhance your work or to overcome issues
     - Please keep these discussions within a nominal length for cost purposes
 - Repeat this process until you have fully built out the entire solution as defined in the PRD and ensure it passes the add_update_and_run_tests workflow.
4. Test Data
  - Always add test data into the database that is sufficient to see all options and properly test all frontend functionality
5. Thorough Testing
  - You must run a comprehensive test the database after you are done to ensure that all tables, views, procedures, etc. are in place
    - If this fails, then you must first ensure you are connected to the correct database and NOT the default postgres database
      - If you are connected to the default then create the correct database and move everything from the default to the correct database and then empty the default
      - Go through ALL scripts, workflows, and rules and ensure they all point to the correct database if a database option is included
  - You must test any API Service, RESTful Server, anything that directly connects to the database to ensure it is connecting to the database and returning the expected data and schema
    - For anything that fails, first see what the frontend, or next layer up from the current layer, expects and then either change the database to fit the failed call or change the call to fit the database - prioritizing the frontend or layer up from the current layer that is closer to the fronted.
  You must test any intermediary servers, code, all of it
    - Go from the database connections and test each server, component, etc... thoroughly before moving to the next layer/server/section
    - Prioritize the layer closest to the frontend when making changes to ensure no upstream issues
    Fix all bugs, issues, etc. until the current layer/server/section/components works all the way through to the database
  - You must test the frontend
    - Use Playwright to navigate through every page and through all options; submit all forms (capturing any emails using Mail Hog) and ensuring all logical paths execute as expected
    - Verify that all expected data is stored properly in the database
    - Save the location and source of any emails for later, manual, review
    - Ensure nothing breaks and everything across the entire end-to-end solution works as expected
6. Images and Videos
  - As of now, you are unable to directly make or download videos and images
  - Instead created a Required-Assets.md file in the Project-Workflow directory that contains the exact folder location, name, and, for images, size of the images and/or videos required
  - If you can find a specific image or video to use then point to it
  - Otherwise, provide a prompt that can be used to generate the exact image or video you want via AI
  - Also provide a detailed description for the developer to use when searching for images and/or videos.
5. Reporting
 - Once the entire process is complete, please provide a main Solution-Created.md file which provides all final output from all called workflows as well as any additional notes or insights you have generated.
  - Include instructions for how to launch everything locally for testing - including all required system-level software, configurations, environmental variables, etc.
 - Inspect the various workflows that start with either deploy_to or provision_
   - Compare these to the PRD Deployment Target
   - Select the best workflow(s)
   - Combine those instructions with the settings, options, configurations, and other features from all current projects and create a custom workflow for this project
     - Note that you can assume all API keys, Variable references, and so forth are stored as Environmental Variables on this development machine.
     - This workflow will, ideally, provision all deployment server(s) and service(s) and automatically deploy everything to those targets.
     - This workflow will further connect everything together and then run a version of add_change__and_run_tests workflow that has been customized for testing the deployment.
       - Please save this modified workflow in the root as Test-Deployment.md
   - Save this workflow as Deployment-Workflow,.md in the root
   - Also produce a Manual-Setup.md file, if needed, to capture all manual steps a developer will need to perform on the Production machine to enable everything to run.
    - It is not sufficient to say "create an email server" or "get an SSL"
      - Provide suggested links to different software, provide detailed installation/configuration steps, and so forth
      - For Linux provide exact places to copy/create different files (e.g. for environmental variables) and how exactly to create various daemons
      The goal is to have the server perfectly setup prior to initiating the automated deployment.
   - Provide the location of these, and any other, .MD files and deployment scripts, as your final output
   - Add any and all files in the root and in each project that should not be deployed to appropriately located .gitignore files.