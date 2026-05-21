# SPARC Development Methodology

Orchestrate complex workflows using the SPARC framework.

## Phases

1. **Specification** — Clarify objectives, constraints, and scope
2. **Pseudocode** — High-level logic with TDD anchors
3. **Architecture** — Extensible system design and service boundaries
4. **Refinement** — TDD, debugging, security hardening, optimization
5. **Completion** — Integration, documentation, monitoring

## Usage

```
/sparc <objective>
```

## Available Modes

- `/sparc-architect` — System design and architecture
- `/sparc-code` — Auto-coding with best practices
- `/sparc-tdd` — Test-driven development
- `/sparc-debug` — Debugging and root cause analysis
- `/sparc-security` — Security review and hardening
- `/sparc-devops` — Deployment and CI/CD
- `/sparc-docs` — Documentation writing

## Execution via Ruflo MCP

When the claude-flow MCP server is available, SPARC modes run as coordinated agent workflows:

```
mcp__claude-flow__sparc_run(mode: "architect", task: "<your task>")
```

## Key Principles

- Modular, testable design
- Environment variables for all secrets
- Test-first approach
- Memory integration for storing architectural decisions
