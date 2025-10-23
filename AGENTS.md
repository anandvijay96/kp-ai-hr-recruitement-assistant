# AGENTS-GENERIC.md

## Overview

This file defines universal AI development guidelines and best practices for software development projects. It provides consistent direction for code generation, refactoring, documentation, testing, and collaboration that applies across all technology stacks and programming languages.

All AI agents operating in software development environments should adhere to these principles.

---

## Core Principles

### Code Quality
- Write clean, readable, and maintainable code
- Follow the principle of least surprise
- Prefer explicit over implicit
- Keep functions and methods small and focused (single responsibility)
- Use meaningful names for variables, functions, and classes
- Avoid premature optimization - prioritize clarity first
- Write self-documenting code with clear intent

### Type Safety & Validation
- Use static typing when available (TypeScript, Python type hints, etc.)
- Validate all external inputs (user input, API responses, file contents)
- Handle edge cases explicitly
- Prefer compile-time errors over runtime errors
- Use schema validation libraries when appropriate

### Error Handling
- Implement proper error handling at all levels
- Provide meaningful error messages for debugging
- Log errors with sufficient context
- Fail fast and fail loudly in development
- Handle errors gracefully in production
- Never swallow exceptions silently

### Testing
- Write tests before or alongside implementation (TDD/BDD)
- Maintain high test coverage (aim for 80%+)
- Test edge cases and error conditions
- Keep tests fast and independent
- Use descriptive test names that explain intent
- Mock external dependencies appropriately

---

## Do

### General Development
- read existing code before making changes
- follow existing project conventions and patterns
- keep changes focused and atomic
- write commit messages that explain why, not just what
- document complex logic and non-obvious decisions
- refactor incrementally, not in large sweeps
- use version control for all code changes
- review your own code before submitting

### Code Organization
- organize code by feature/domain, not by type
- keep related files close together
- use consistent file and directory naming conventions
- separate concerns (business logic, data access, presentation)
- extract reusable code into shared modules
- maintain clear module boundaries
- use dependency injection for flexibility

### Documentation
- write README files for all projects
- document setup and installation steps
- include usage examples
- maintain API documentation
- document breaking changes
- keep documentation up to date with code changes
- use inline comments for complex logic only

### Security
- never commit secrets or credentials
- use environment variables for configuration
- validate and sanitize all inputs
- implement proper authentication and authorization
- follow principle of least privilege
- keep dependencies up to date
- use security scanning tools

### Performance
- profile before optimizing
- optimize bottlenecks, not everything
- use appropriate data structures
- implement caching strategically
- consider memory usage and leaks
- use lazy loading when appropriate
- monitor production performance

---

## Don't

### Code Quality
- don't write code without understanding requirements
- don't copy-paste code without understanding it
- don't leave commented-out code in production
- don't use magic numbers or strings
- don't create god classes or functions
- don't ignore compiler/linter warnings
- don't mix concerns in a single module

### Testing
- don't skip writing tests
- don't test implementation details
- don't write flaky tests
- don't ignore failing tests
- don't delete tests to make builds pass
- don't test third-party libraries

### Security
- don't trust user input
- don't store passwords in plain text
- don't use deprecated or vulnerable dependencies
- don't expose sensitive information in logs
- don't implement custom cryptography
- don't bypass security measures for convenience

### Version Control
- don't commit directly to main/master
- don't commit broken code
- don't commit large binary files
- don't force push to shared branches
- don't mix unrelated changes in one commit
- don't use vague commit messages

---

## Project Structure Best Practices

### Standard Directories
```
/
├── src/              # Source code
├── tests/            # Test files
├── docs/             # Documentation
├── config/           # Configuration files
├── scripts/          # Build and utility scripts
├── .github/          # GitHub workflows and templates
├── .gitignore        # Git ignore rules
├── README.md         # Project overview
└── LICENSE           # License information
```

### Configuration Files
- keep configuration separate from code
- use environment-specific config files
- provide example configuration files (.env.example)
- document all configuration options
- use validation for configuration values

---

## Development Workflow

### Before Starting Work
1. Understand the requirement fully
2. Check for existing similar implementations
3. Plan the approach and discuss if needed
4. Create a feature branch
5. Set up the development environment

### During Development
1. Write failing tests first (TDD)
2. Implement minimal code to pass tests
3. Refactor while keeping tests green
4. Commit frequently with clear messages
5. Keep changes focused and reviewable

### Before Submitting
1. Run all tests locally
2. Check code formatting and linting
3. Review your own changes
4. Update documentation if needed
5. Write clear PR/MR description
6. Ensure CI/CD passes

---

## Code Review Guidelines

### As a Reviewer
- be constructive and respectful
- explain the "why" behind suggestions
- distinguish between blocking and non-blocking comments
- approve when code meets standards
- respond in a timely manner

### As an Author
- respond to all comments
- explain your reasoning when disagreeing
- make requested changes promptly
- thank reviewers for their time
- learn from feedback

---

## Testing Best Practices

### Test Types
- **Unit Tests**: Test individual functions/methods in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test complete user workflows
- **Performance Tests**: Test speed and resource usage
- **Security Tests**: Test for vulnerabilities

### Test Structure
```
describe('Feature/Component Name', () => {
  describe('method/function name', () => {
    it('should do expected behavior when condition', () => {
      // Arrange: Set up test data
      // Act: Execute the code under test
      // Assert: Verify the results
    })
  })
})
```

### Test Naming
- use descriptive names that explain the scenario
- include the expected behavior
- include the condition or context
- avoid technical jargon in test names

---

## Documentation Standards

### README Structure
1. **Project Title**: Clear, descriptive name
2. **Description**: What the project does and why
3. **Installation**: Step-by-step setup instructions
4. **Usage**: Basic usage examples
5. **Configuration**: Environment variables and settings
6. **Contributing**: How to contribute
7. **License**: License information
8. **Contact**: How to get help

### Code Comments
- explain why, not what
- document assumptions and constraints
- mark TODOs with context
- include examples for complex APIs
- keep comments up to date

### API Documentation
- document all public APIs
- include parameter types and descriptions
- provide usage examples
- document error conditions
- specify return types

---

## Scratchpad & Task Management

### Scratchpad Usage
Maintain a `scratchpad.md` file for:
1. **Current Task**: Description of ongoing work
2. **Progress Tracking**: TODO lists with completion markers
3. **Lessons Learned**: Reusable fixes and patterns
4. **Notes**: Context and observations

### Task Tracking Format
```markdown
## Current Task: [Feature/Bug Name]

### Progress
- [X] Completed subtask 1
- [X] Completed subtask 2
- [ ] Pending subtask 3
- [ ] Pending subtask 4

### Lessons Learned
- Lesson 1: Description and solution
- Lesson 2: Description and solution

### Notes
- Important context or observations
```

### When to Update
- at the start of each work session
- after completing major milestones
- when discovering important patterns
- when fixing mistakes or bugs
- before context switching

---

## Common Patterns

### Error Handling Pattern
```
try:
    result = risky_operation()
    validate(result)
    return success(result)
except SpecificError as e:
    log_error(e, context)
    return error_response(e)
except Exception as e:
    log_critical(e, context)
    raise
```

### Configuration Pattern
```
# Load from environment with validation
config = {
    'database_url': required_env('DATABASE_URL'),
    'api_key': required_env('API_KEY'),
    'debug': optional_env('DEBUG', default=False),
}

validate_config(config)
```

### Logging Pattern
```
# Structured logging with context
logger.info('Operation started', {
    'user_id': user.id,
    'operation': 'data_import',
    'timestamp': now()
})

try:
    result = perform_operation()
    logger.info('Operation completed', {'result': result})
except Exception as e:
    logger.error('Operation failed', {
        'error': str(e),
        'stack_trace': traceback.format_exc()
    })
```

---

## Performance Best Practices

### General
- measure before optimizing
- optimize the critical path first
- use profiling tools to identify bottlenecks
- consider time and space complexity
- cache expensive operations
- use appropriate algorithms and data structures

### Database
- use indexes for frequently queried columns
- avoid N+1 query problems
- use connection pooling
- implement pagination for large datasets
- use database-level constraints
- optimize queries with EXPLAIN/ANALYZE

### API Design
- implement rate limiting
- use pagination for list endpoints
- support filtering and sorting
- implement caching headers
- compress responses
- use appropriate HTTP methods

---

## Security Best Practices

### Input Validation
- validate all external inputs
- use allowlists over denylists
- sanitize data before use
- implement length limits
- validate data types and formats

### Authentication & Authorization
- use established authentication libraries
- implement multi-factor authentication
- use secure session management
- implement proper password policies
- use role-based access control
- validate permissions on every request

### Data Protection
- encrypt sensitive data at rest
- use HTTPS for all communications
- implement proper key management
- follow data retention policies
- implement audit logging
- comply with privacy regulations

---

## Debugging Strategies

### When Encountering a Bug
1. **Reproduce**: Create minimal reproduction case
2. **Isolate**: Narrow down the problem area
3. **Understand**: Read and understand the code
4. **Hypothesize**: Form theories about the cause
5. **Test**: Verify hypotheses systematically
6. **Fix**: Implement minimal fix
7. **Verify**: Ensure fix works and doesn't break other things
8. **Learn**: Document the lesson

### Debugging Tools
- use debuggers, not just print statements
- leverage logging at appropriate levels
- use profilers for performance issues
- use memory analyzers for memory leaks
- use network inspectors for API issues

---

## Continuous Improvement

### Learning from Mistakes
- document all bugs and their fixes
- conduct post-mortems for major issues
- share learnings with the team
- update documentation and tests
- improve processes to prevent recurrence

### Code Quality Metrics
- track test coverage
- monitor code complexity
- measure build times
- track bug rates
- monitor technical debt

### Regular Maintenance
- update dependencies regularly
- refactor problematic code
- improve test coverage
- update documentation
- remove deprecated code

---

## Communication Guidelines

### Writing Issues/Tickets
- use clear, descriptive titles
- provide context and background
- include steps to reproduce (for bugs)
- specify expected vs actual behavior
- add relevant screenshots or logs
- label appropriately

### Pull/Merge Request Descriptions
- summarize what changed and why
- reference related issues
- highlight breaking changes
- include testing notes
- add screenshots for UI changes
- request specific reviewers when needed

### Code Comments
- explain complex algorithms
- document workarounds and why they exist
- note performance considerations
- explain non-obvious decisions
- keep comments concise and relevant

---

## When Stuck

### Problem-Solving Steps
1. **Pause and reflect**: Step back from the problem
2. **Review documentation**: Check official docs and guides
3. **Search for solutions**: Look for similar issues
4. **Break it down**: Divide into smaller problems
5. **Ask for help**: Reach out to team or community
6. **Document the solution**: Help others facing the same issue

### Questions to Ask
- What am I trying to achieve?
- What have I tried so far?
- What are the constraints?
- Is there a simpler approach?
- Who might have solved this before?

---

## Safety and Permissions

### Allowed Without Approval
- reading files and documentation
- running tests
- formatting and linting code
- creating feature branches
- writing draft code

### Requires Approval
- installing new dependencies
- modifying configuration files
- database migrations
- deploying to production
- deleting code or files
- changing CI/CD pipelines
- modifying security settings

---

## Language-Agnostic Best Practices

### Naming Conventions
- use descriptive names that reveal intent
- follow language-specific conventions
- be consistent within the project
- avoid abbreviations unless widely known
- use verbs for functions, nouns for variables

### Code Style
- follow established style guides
- use automated formatters
- maintain consistent indentation
- limit line length (80-120 characters)
- group related code together
- use blank lines to separate logical sections

### Dependencies
- minimize external dependencies
- keep dependencies up to date
- audit dependencies for security
- document why each dependency is needed
- prefer well-maintained libraries

---

## Notes

- adapt these guidelines to your specific project needs
- prioritize team agreement over individual preference
- update this file as the project evolves
- share learnings and improvements
- focus on delivering value while maintaining quality
- when in doubt, ask for clarification

---

**Purpose**: Universal AI development guidelines for all software projects  
**Audience**: AI agents, developers, and development teams  
**Last Updated**: October 2025
