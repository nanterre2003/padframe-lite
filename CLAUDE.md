# Pad Frame — Claude Code Guide

Pad Frame is a single-file web app (`index.html`) that turns an iPad into a digital photo frame. It runs entirely in-browser with no backend.

## Architecture

- Pure HTML/CSS/JavaScript, no build step
- Client-side image resizing via Canvas API (max 1024×768, JPEG 0.75)
- Crossfade/slide transitions between photos using CSS transforms
- Settings panel for transition effect, interval, and clock visibility

## Development

Open `index.html` directly in a browser — no server needed.

## Ruflo Integration

This project uses [Ruflo](https://github.com/ruvnet/ruflo) for AI-assisted development via Claude Code.

### Available Skills

| Skill | Description |
|-------|-------------|
| `/sparc` | SPARC methodology — orchestrate complex tasks across phases |
| `/swarm` | Launch a multi-agent swarm for parallel work |
| `/memory` | Store and retrieve project knowledge |

### MCP Server

The `claude-flow` MCP server starts automatically via `npx ruflo@latest mcp start` and provides 100+ agent tools for swarm coordination, memory, and neural patterns.

### Quick Start

```bash
# Register MCP server manually if needed
claude mcp add ruflo -- npx ruflo@latest mcp start

# Run a SPARC workflow
/sparc "Add PWA offline support to the photo frame"

# Launch a swarm
/swarm "Add Ken Burns zoom effect to photo transitions"
```
