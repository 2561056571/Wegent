---
description: "Submit wiki documentation sections to Wegent backend API. Simplifies the HTTP POST process for wiki content submission."
version: "1.0.0"
author: "Wegent Team"
tags: ["wiki", "documentation", "api", "submission"]
---

# Wiki Submit Skill

This skill provides a simple command-line tool to submit wiki documentation sections to the Wegent backend.

## Usage

### Submit a single section from a markdown file

```bash
node wiki_submit.js submit \
  --endpoint "http://localhost:8000/api/internal/wiki/generations/contents" \
  --generation-id 123 \
  --type overview \
  --title "Project Overview" \
  --file /path/to/overview.md
```

### Submit section content directly

```bash
node wiki_submit.js submit \
  --endpoint "http://localhost:8000/api/internal/wiki/generations/contents" \
  --generation-id 123 \
  --type architecture \
  --title "System Architecture" \
  --content "# Architecture\n\nYour markdown content here..."
```

### Complete the wiki generation

```bash
node wiki_submit.js complete \
  --endpoint "http://localhost:8000/api/internal/wiki/generations/contents" \
  --generation-id 123 \
  --structure-order "overview: Project Overview" "architecture: System Architecture" "module: Core Modules"
```

### Mark generation as failed

```bash
node wiki_submit.js fail \
  --endpoint "http://localhost:8000/api/internal/wiki/generations/contents" \
  --generation-id 123 \
  --error-message "Failed to analyze repository structure"
```

## Section Types

- `overview`: Project overview and objectives
- `architecture`: System architecture and design
- `module`: Module documentation
- `api`: API documentation
- `guide`: User guides and tutorials
- `deep`: In-depth technical analysis

## Authentication

The authorization token is **automatically obtained** from the `TASK_INFO.auth_token` environment variable when running inside an executor container. You don't need to specify it manually.

## Environment Variables

You can set these environment variables instead of passing arguments:

- `WIKI_ENDPOINT`: API endpoint URL
- `WIKI_GENERATION_ID`: Generation ID