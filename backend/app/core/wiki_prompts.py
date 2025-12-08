# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

from string import Template
from typing import List, Optional

"""
Wiki Generation Prompts Configuration

This file contains the task prompt template for wiki documentation generation.
The wiki bot system prompt is defined in backend/init_data/01-default-resources.yaml
as the 'wiki-ghost' Ghost resource.

Optimization Notes:
- Task prompt focuses on WHAT to do (project-specific parameters)
- Ghost system prompt focuses on HOW to do it (tool usage, format rules)
- This separation reduces redundancy and improves maintainability
"""

# Simplified task prompt template for wiki generation
WIKI_TASK_PROMPT_TEMPLATE = Template(
    """Generate comprehensive technical documentation for the repository: **${project_name}**

## Task Configuration

The following environment variables are pre-configured for wiki submission:
- `WIKI_ENDPOINT`: ${content_endpoint}
- `WIKI_GENERATION_ID`: ${generation_id}

**Note**: Authorization is handled automatically by the wiki_submit skill.

**Target Language**: ${language}
**Available Section Types**: ${section_types}

## Documentation Requirements

### Required Sections
1. **Overview** (`type: overview`): Project objectives, core capabilities, tech stack
2. **Architecture** (`type: architecture`): System design with Mermaid diagrams, module responsibilities, data flows

### Additional Sections (based on project analysis)
- `module`: Key modules with responsibilities, classes/functions, dependencies
- `api`: API endpoints, authentication, request/response schemas
- `guide`: Setup guides, configuration, troubleshooting
- `deep`: In-depth analysis of complex topics

## Workflow

1. **Analyze** the repository structure, README, and key source files
2. **Write** each section as a markdown file (e.g., `/tmp/overview.md`)
3. **Submit** each section using the wiki_submit skill:
   ```bash
   node wiki_submit.js submit --type overview --title "Project Overview" --file /tmp/overview.md
   ```
4. **Complete** the generation after all sections are submitted:
   ```bash
   node wiki_submit.js complete --structure-order "overview: Project Overview" "architecture: System Architecture"
   ```

If you encounter errors, mark the generation as failed:
```bash
node wiki_submit.js fail --error-message "Description of the error"
```

---

Begin by analyzing the repository structure and generating documentation."""
)


# Additional notes for different generation types
GENERATION_TYPE_NOTES = {
    "full": "",
    "incremental": "\n\nNote: This is an incremental update task, please focus on recent code changes.",
    "custom": "\n\nNote: This is a custom scope documentation generation task.",
}


def get_wiki_task_prompt(
    project_name: str,
    generation_type: str = "full",
    generation_id: Optional[int] = None,
    content_endpoint: Optional[str] = None,
    section_types: Optional[List[str]] = None,
    language: Optional[str] = None,
) -> str:
    """
    Generate wiki task prompt

    Args:
        project_name: Project name
        generation_type: Generation type (full/incremental/custom)
        generation_id: Wiki generation identifier for the current run
        content_endpoint: Endpoint the agent must call to submit results
        section_types: Section types to cover in documentation
        language: Target language for documentation generation

    Returns:
        Complete task prompt
    """
    context = {
        "project_name": project_name,
        "generation_id": (
            generation_id if generation_id is not None else "UNKNOWN_GENERATION_ID"
        ),
        "content_endpoint": content_endpoint or "/internal/wiki/generations/contents",
        "section_types": ", ".join(
            section_types
            or ["overview", "architecture", "module", "api", "guide", "deep"]
        ),
        "language": language or "en",
    }

    base_prompt = WIKI_TASK_PROMPT_TEMPLATE.safe_substitute(**context)
    additional_note = GENERATION_TYPE_NOTES.get(generation_type, "")

    return base_prompt + additional_note
