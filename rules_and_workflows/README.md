# DCIS Rules and Workflows - Setup Guide

This directory contains all the rules and workflows for the DCIS project that can be integrated with Gemini AI.

## Directory Structure

```
rules_and_workflows/
├── GLOBAL_RULES.md          # Copy to ~/.gemini/GEMINI.md
├── WORKSPACE_RULES.md       # Copy to .agent/WORKSPACE.md
├── workflows/
│   ├── new-agent.md         # Copy to .agent/workflows/
│   ├── advanced-feature.md  # Copy to .agent/workflows/
│   ├── deploy-staging.md    # Copy to .agent/workflows/
│   ├── debug-agent.md       # Copy to .agent/workflows/
│   └── update-models.md     # Copy to .agent/workflows/
└── README.md                # This file
```

## Installation Instructions

### 1. Global Rules (Optional but Recommended)

Copy the global rules to your Gemini configuration:

```bash
# Create Gemini config directory if it doesn't exist
mkdir -p ~/.gemini

# Copy global rules
cat rules_and_workflows/GLOBAL_RULES.md >> ~/.gemini/GEMINI.md
```

**Note**: If you already have a `GEMINI.md` file, the content will be appended. Review and merge as needed.

### 2. Workspace Rules (Required for DCIS Project)

Create the `.agent` directory in your project root and copy the workspace rules:

```bash
# From the project root (/Users/dasuncharuka/Documents/projects/llm/)
mkdir -p .agent

# Copy workspace rules
cp rules_and_workflows/WORKSPACE_RULES.md .agent/WORKSPACE.md
```

### 3. Workflows (Highly Recommended)

Copy all workflows to the `.agent/workflows/` directory:

```bash
# Create workflows directory
mkdir -p .agent/workflows

# Copy all workflow files
cp rules_and_workflows/workflows/*.md .agent/workflows/
```

## Using Workflows

Once installed, you can reference workflows in your conversations with Gemini:

### Example 1: Create a New Agent
```
"Follow the new-agent workflow to create a Scholar agent"
```

### Example 2: Implement a Feature
```
"Use the advanced-feature workflow to implement Chain-of-Verification"
```

### Example 3: Debug Performance
```
"Run the debug-agent workflow for the Logician agent"
```

## Workflow Features

All workflows include:
- **Step-by-step instructions** with code examples
- **`// turbo` annotations** for commands safe to auto-run
- **`// turbo-all` annotations** for fully automated workflow execution
- **Success criteria** checklists

## Available Workflows

1. **new-agent.md** - Create new specialized agents with proper testing and documentation
2. **advanced-feature.md** - Implement advanced AI features following best practices
3. **deploy-staging.md** - Deploy to staging with verification and smoke tests
4. **debug-agent.md** - Debug and optimize agent performance
5. **update-models.md** - Safely update LLM models with A/B testing

## Customization

Feel free to:
- Edit workflows to match your specific needs
- Add new workflows for common tasks
- Adjust rules based on team preferences
- Add project-specific conventions

## Verification

After installation, verify the setup:

```bash
# Check global rules
cat ~/.gemini/GEMINI.md | grep "DCIS"

# Check workspace rules
cat .agent/WORKSPACE.md | grep "DCIS"

# List workflows
ls -la .agent/workflows/
```

You should see all 5 workflow files listed.

## Integration with Gemini

Once installed:
1. Gemini will automatically read `GLOBAL_RULES.md` (if added to `~/.gemini/GEMINI.md`)
2. When working in this project, Gemini will reference `WORKSPACE_RULES.md`
3. You can invoke workflows by name in your prompts
4. Workflows with `// turbo` can auto-execute safe commands

## Support

For issues or questions about these rules and workflows:
- Review the main project documentation
- Check `implementation_workflow.md` for detailed guidance
- Refer to `complete_ai_architecture.md` for technical details
