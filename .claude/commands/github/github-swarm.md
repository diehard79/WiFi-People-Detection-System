# github-swarm

Create a specialized swarm for GitHub repository management.

## Usage
```bash
npx claude-flow github swarm [options]
```

## Options
- `--repository <owner/repo>` - Target repository
- `--agents <n>` - Number of specialized agents
- `--focus <area>` - Focus area (maintenance, features, security)

## Examples
```bash
# Create GitHub swarm
npx claude-flow github swarm --repository myorg/myrepo

# With specific focus
npx claude-flow github swarm --repository myorg/myrepo --focus security

# Custom agent count
npx claude-flow github swarm --repository myorg/myrepo --agents 6
```
