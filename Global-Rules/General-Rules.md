# General Rules & Guidelines — Be Free Fitness Project

## Global Settings & Customizations
<!-- Centralized cross-project requirements for Cursor sessions. Review before running any workflow to keep shared automation consistent. -->

### Command Execution Framework
- **Watchdog Wrapper**: All commands must use `powershell -ExecutionPolicy Bypass -File scripts/cursor_run.ps1 -TimeoutSec <secs> -Label "<label>" -Args "<command>"`
- **Purpose**: Provides timeout protection, output capture, error handling, and prevents command hanging
- **Setup**: Ensure `scripts/cursor_run.ps1` exists (created by startup script)
- **Benefits**: Robust command execution with automatic cleanup and debugging support

### Session Management
- **Progression Rule**: Always advance to the next task immediately upon completion
- **Setup Command**: `PowerShell -ExecutionPolicy Bypass -File Global-Scripts/ensure-progression-rule.ps1`
- **Session Continuity**: For long chats, save context to `Project-Management/session-notes.md` and start new chat with continuation prompt
- **Next-Task Prompt**: Use format `Continue Be Free Fitness Project using Project-Management/Project-Workflow.md (current task: <ID>)`

### Visual Testing Environment
- **Service Lifecycle**: Start services via `scripts/start-visual-test-env.ps1` (through watchdog)
- **Cleanup Protocol**: Always execute `scripts/stop-visual-test-env.ps1 -IncludeBrowsers` after each test run
- **Browser Hygiene**: Recycle browser contexts between discrete test cases to prevent cache/storage leaks
- **Clean Slate Principle**: Ensures no process conflicts or resource leaks between test runs

### 🚨 CRITICAL: NEVER Show Reports in Browser
- **Rule**: NEVER open HTML reports in a browser window during testing
- **Critical**: Browser report display traps the AI session and prevents continuation
- **Action**: Always use `--reporter=list` or `--reporter=dot` instead of HTML reporter that opens browser
- **Playwright**: When running Playwright tests, NEVER use default HTML reporter that serves reports
- **Output**: Use list or dot reporters that output to console only
- **Files**: HTML reports can be saved to files for later review, but NEVER automatically opened
- **Rationale**: Auto-opening reports causes session to hang waiting for browser interaction
- **Exception**: None - this rule applies to ALL testing tools (Playwright, Jest, etc.)

### Environment Configuration
- **Working Directory**: Always `Set-Location` to project root before launching services
- **Database Defaults**: 
  - Host: `localhost`
  - User: `postgres` 
  - Database: `project-specific`
  - Command Template: `psql -h localhost -U postgres -d project-specific -W -c "<SQL>"`
- **Service Management**: Start long-running servers in dedicated PowerShell windows using watchdog wrapper

## Task Execution Framework

### Status Icons
- **⬜ Open**: Task ready to begin or currently in progress
- **✅ Complete**: Task successfully finished
- **❌ Failed**: Task encountered error (document in `Project-Management/Task-Failed.md`)

### Task Dependencies
- **Sequential Tasks**: Must complete in order, each building on the previous
- **Parallel Tasks**: Can run concurrently once dependencies are satisfied
- **Test Tasks**: Task TR (Add/Update/Run Tests) is reusable and should be invoked after each feature slice

### Failure Handling
- **Documentation**: All failures must be documented in `Project-Management/Task-Failed.md`
- **Logging**: Include detailed failure logs with command outputs and error messages
- **Resolution**: Address failures before proceeding to dependent tasks
- **Retry Logic**: Implement appropriate retry mechanisms for transient failures

## Development Standards

### 🤝 **MUTUAL TRUST PRINCIPLE**
- **Rule**: "If you have my back, I have yours"
- **Critical**: This relationship is built on mutual trust and reliability
- **Actions**:
  - Take ownership of all work assigned
  - Deliver on commitments made
  - Communicate honestly about progress and issues
  - Do the work correctly the first time
  - Maintain transparency in all decisions
- **Enforcement**: Trust is earned through consistent, quality delivery
- **Purpose**: Creates collaborative environment where both parties succeed

### 🧪 **THREE-AI ACCOUNTABILITY**
- **Rule**: ALL work will be checked by at least three different AI models
- **Critical**: "Do things correct and be honest or I will find out"
- **Actions**:
  - No shortcuts - do real implementations
  - No fake data - use production-ready code
  - No mock interfaces - real functionality only
  - All tests must test real functionality
  - Expect rigorous review from multiple AI models
  - Take pride in work that withstands scrutiny
- **Enforcement**: Work quality must be production-ready at ALL times
- **Purpose**: Ensures sustainable, maintainable, quality codebase through multi-model validation

### Test-Driven Development
- **TDD Approach**: Follow test-driven development principles throughout
- **Test Coverage**: Maintain comprehensive test coverage for all implemented features
- **Test Execution**: Run tests after each significant change or feature completion
- **Test Documentation**: Document test results and coverage metrics

### Security & Compliance
- **Security First**: Implement security measures from the beginning, not as an afterthought
- **Compliance**: Ensure all implementations meet GDPR-style retention and encryption requirements
- **Audit Trail**: Maintain comprehensive logging and auditing for all operations
- **Vulnerability Management**: Regular security scans and dependency audits

### Code Quality
- **Standards**: Follow established coding standards and best practices
- **Linting**: Use appropriate linting tools and fix all warnings
- **Type Safety**: Maintain strong typing throughout the codebase
- **Error Handling**: Implement comprehensive error handling and logging
- **Performance**: Optimize for performance from the beginning with appropriate caching strategies

### Documentation Standards
- **Living Documentation**: Keep all documentation current with implementation changes
- **Artifact Tracking**: Maintain clear links between planning artifacts and implementation
- **API Documentation**: Document all API endpoints and contracts
- **User Flows**: Document user journeys and interaction patterns

## Project Organization

### Artifacts Directory
- **Planning Artifacts**: Place intermediate planning artifacts under `Project-Management/artifacts/`
- **Code Outputs**: Code/config outputs go in their respective project folders
- **Organization**: Maintain clear separation between planning documents and implementation artifacts

### Visual Testing Artifacts
- **Screenshot Management**: Organize visual test artifacts in dedicated directories
- **Test Isolation**: Ensure tests don't interfere with each other
- **Resource Monitoring**: Monitor system resources during development and testing

## Deployment & Operations

### Deployment Strategy
- **Environment Management**: Clear separation between development, staging, and production
- **Configuration Management**: Environment-specific configuration handling
- **Rollback Capability**: Ability to rollback deployments if issues arise
- **Monitoring**: Comprehensive monitoring and alerting

### Operational Excellence
- **Logging**: Comprehensive logging for debugging and monitoring
- **Monitoring**: Real-time monitoring of system health and performance
- **Alerting**: Appropriate alerting for critical issues
- **Documentation**: Operational runbooks and procedures

## Risk Management

### Technical Risks
- **Dependency Management**: Regular updates and vulnerability scanning
- **Security Vulnerabilities**: Proactive security scanning and patching
- **Performance Issues**: Performance monitoring and optimization
- **Data Loss**: Comprehensive backup and recovery procedures

### Project Risks
- **Scope Creep**: Clear scope definition and change management
- **Timeline Delays**: Regular progress monitoring and risk assessment
- **Resource Constraints**: Resource planning and allocation
- **Quality Issues**: Quality gates and review processes

## Best Practices Summary

### Development Workflow
1. **Setup**: Ensure all global settings and scripts are in place
2. **Planning**: Review requirements and create detailed plans
3. **Implementation**: Follow TDD principles with comprehensive testing
4. **Documentation**: Keep all documentation current
5. **Quality**: Maintain high code quality and security standards
6. **Deployment**: Use proven deployment strategies and procedures

### Communication
- **Status Updates**: Regular status updates and progress reporting
- **Issue Escalation**: Clear escalation procedures for blockers
- **Knowledge Sharing**: Regular knowledge sharing and documentation
- **Stakeholder Communication**: Clear communication with all stakeholders

### Continuous Improvement
- **Process Refinement**: Regular review and improvement of processes
- **Tool Evaluation**: Regular evaluation of tools and technologies
- **Best Practice Adoption**: Adoption of industry best practices
- **Learning**: Continuous learning and skill development

---

*This document serves as the central repository for all general rules, guidelines, and best practices for the Be Free Fitness project. It should be referenced and updated as the project evolves.*