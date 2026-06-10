# Swarm Coordination

Launch and coordinate multi-agent swarms for parallel task execution.

## Usage

```
/swarm <objective>
```

## Topologies

- **hierarchical** — Lead agent delegates to specialists
- **mesh** — Agents collaborate as peers
- **hierarchical-mesh** — Hybrid (default)

## Examples

```
/swarm "Add offline support to the photo frame app"
/swarm "Audit and harden the app for production"
/swarm "Refactor JavaScript to modern ES modules"
```

## Via Ruflo MCP

```
mcp__claude-flow__swarm_init(objective: "<task>", maxAgents: 5)
```

## Agent Roles

Swarms auto-assign roles based on the task:
- **architect** — System design
- **developer** — Implementation
- **tester** — Quality assurance
- **reviewer** — Code review
- **documenter** — Documentation
