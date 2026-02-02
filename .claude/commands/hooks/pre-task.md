# pre-task

Hook executed before task execution.

## Usage
```bash
npx claude-flow hook pre-task [options]
```

## Options
- `--description <text>` - Task description
- `--auto-spawn-agents` - Automatically spawn required agents
- `--load-context` - Load previous context

## Examples
```bash
# Basic pre-task hook
npx claude-flow hook pre-task --description "Building API endpoints"

# With auto-spawn
npx claude-flow hook pre-task --description "Complex refactoring" --auto-spawn-agents

# Load context
npx claude-flow hook pre-task --description "Continue feature" --load-context
```
