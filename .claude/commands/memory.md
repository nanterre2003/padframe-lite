# Memory Management

Store and retrieve project knowledge using AgentDB vector memory.

## Usage

```
/memory store <key> <value>
/memory search <query>
/memory list
```

## Via Ruflo MCP

```
mcp__claude-flow__memory_store(key: "arch/decisions", value: "...")
mcp__claude-flow__memory_search(query: "photo frame architecture")
mcp__claude-flow__memory_list()
```

## Use Cases

- Store architectural decisions
- Remember past debugging solutions
- Share context between agent sessions
- Track feature specifications
