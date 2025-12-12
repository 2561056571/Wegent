#!/usr/bin/env python

# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""
Claude Code Subagent Builder

This module creates subagent definition files in .claude/agents/ directory,
which are automatically discovered and used by Claude Code's Task tool.

The official Claude Code subagent approach:
1. Create .claude/agents/ directory in the project
2. Add markdown files with YAML frontmatter defining each agent
3. Claude Code's Task tool automatically discovers and uses these agents
"""

import os
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

from shared.logger import setup_logger

logger = setup_logger("subagent_builder")


class SubagentDefinition:
    """
    Represents a subagent definition that will be written as a markdown file.
    """

    def __init__(
        self,
        name: str,
        description: str,
        prompt: str,
        model: Optional[str] = None,
        agent_type: str = "general-purpose"
    ):
        """
        Initialize a subagent definition.

        Args:
            name: Unique name for the subagent (used as filename)
            description: Short description shown in Task tool
            prompt: The full system prompt for this subagent
            model: Optional model to use (sonnet, opus, haiku)
            agent_type: Type of agent (general-purpose, Explore, Plan, etc.)
        """
        self.name = self._sanitize_name(name)
        self.description = description
        self.prompt = prompt
        self.model = model
        self.agent_type = agent_type

    def _sanitize_name(self, name: str) -> str:
        """Sanitize name to be a valid filename."""
        # Replace spaces and special chars with hyphens
        sanitized = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower())
        # Remove consecutive hyphens
        sanitized = re.sub(r'-+', '-', sanitized)
        # Remove leading/trailing hyphens
        return sanitized.strip('-')

    def to_markdown(self) -> str:
        """
        Generate the markdown content for this subagent.

        Returns:
            Markdown string with YAML frontmatter
        """
        lines = [
            "---",
            f"name: {self.name}",
            f"description: {self.description}",
        ]

        if self.model:
            lines.append(f"model: {self.model}")

        if self.agent_type and self.agent_type != "general-purpose":
            lines.append(f"subagent_type: {self.agent_type}")

        lines.append("---")
        lines.append("")
        lines.append(self.prompt)

        return "\n".join(lines)


class SubagentBuilder:
    """
    Builds and manages Claude Code subagent definition files.

    This creates .claude/agents/*.md files that Claude Code's Task tool
    automatically discovers and uses for delegation.
    """

    AGENTS_DIR = ".claude/agents"

    def __init__(self, project_path: str):
        """
        Initialize the subagent builder.

        Args:
            project_path: Root directory of the project
        """
        self.project_path = project_path
        self.agents_path = os.path.join(project_path, self.AGENTS_DIR)
        self._created_agents: List[str] = []

    def ensure_agents_directory(self) -> None:
        """Create the .claude/agents directory if it doesn't exist."""
        os.makedirs(self.agents_path, exist_ok=True)
        logger.info(f"Ensured agents directory exists: {self.agents_path}")

    def create_subagent(self, definition: SubagentDefinition) -> str:
        """
        Create a subagent definition file.

        Args:
            definition: The subagent definition

        Returns:
            Path to the created file
        """
        self.ensure_agents_directory()

        filename = f"{definition.name}.md"
        filepath = os.path.join(self.agents_path, filename)

        content = definition.to_markdown()

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        self._created_agents.append(filepath)
        logger.info(f"Created subagent definition: {filepath}")

        return filepath

    def create_subagents_from_config(
        self,
        team_members_config: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Create subagent files from team configuration.

        Args:
            team_members_config: List of member configurations from task data

        Returns:
            Dictionary mapping member names to their file paths
        """
        created_files = {}

        for member_config in team_members_config:
            name = member_config.get("name", "")
            role = member_config.get("role", "member")

            # Skip leader - leader is the main Claude instance
            if role == "leader":
                logger.info(f"Skipping leader '{name}' - will use main Claude instance")
                continue

            system_prompt = member_config.get("system_prompt", "")
            if not system_prompt:
                logger.warning(f"Skipping member '{name}' - no system prompt")
                continue

            # Create description from first line of system prompt
            description = self._extract_description(system_prompt, name)

            definition = SubagentDefinition(
                name=name,
                description=description,
                prompt=system_prompt,
                agent_type="general-purpose"
            )

            filepath = self.create_subagent(definition)
            created_files[name] = filepath

        logger.info(f"Created {len(created_files)} subagent definitions")
        return created_files

    def _extract_description(self, system_prompt: str, fallback_name: str) -> str:
        """
        Extract a short description from the system prompt and format it
        to tell Claude WHEN to use this subagent.
        
        According to official Claude Code documentation, the description field
        should describe WHEN to call this subagent, not what the subagent is.
        Adding "Use proactively" makes Claude more likely to use it.
        
        Note: This method is only called for subagents (not leader), as leader
        is skipped in create_subagents_from_config().

        Args:
            system_prompt: The full system prompt
            fallback_name: Name to use if no description can be extracted

        Returns:
            Short description string with "Use proactively to" prefix
        """
        # Try to get first meaningful line from system prompt
        lines = system_prompt.strip().split('\n')
        extracted_desc = None
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and headers
            if not line or line.startswith('#'):
                continue
            # Use first non-empty, non-header line
            extracted_desc = line
            break
        
        if not extracted_desc:
            extracted_desc = f"handle specialized tasks for {fallback_name}"
        
        # Check if description already starts with "use proactively" (case insensitive)
        if extracted_desc.lower().startswith("use proactively"):
            # Already has the prefix, just truncate if needed
            if len(extracted_desc) > 150:
                return extracted_desc[:147] + "..."
            return extracted_desc
        
        # Add "Use proactively to" prefix as recommended by official docs
        # This makes Claude more likely to use the subagent
        desc_lower = extracted_desc.lower()
        
        # If it starts with "You are" or similar, extract the role
        if desc_lower.startswith("you are"):
            # "You are an API specialist" -> "handle API documentation tasks"
            role_part = extracted_desc[7:].strip()  # Remove "You are"
            if role_part.startswith("a ") or role_part.startswith("an "):
                role_part = role_part.split(" ", 1)[1] if " " in role_part else role_part
            # Truncate role part if too long
            if len(role_part) > 80:
                role_part = role_part[:77] + "..."
            return f"Use proactively to {role_part.rstrip('.')}"
        
        # For other descriptions, just add the prefix
        # Truncate to keep total length reasonable
        if len(extracted_desc) > 120:
            extracted_desc = extracted_desc[:117] + "..."
        
        return f"Use proactively to {extracted_desc.lower().rstrip('.')}"

    def cleanup(self) -> None:
        """Remove all created subagent files."""
        for filepath in self._created_agents:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"Removed subagent file: {filepath}")
            except Exception as e:
                logger.warning(f"Failed to remove subagent file {filepath}: {e}")

        self._created_agents.clear()

        # Try to remove the agents directory if empty
        try:
            if os.path.exists(self.agents_path) and not os.listdir(self.agents_path):
                os.rmdir(self.agents_path)
                logger.info(f"Removed empty agents directory: {self.agents_path}")
        except Exception as e:
            logger.warning(f"Failed to remove agents directory: {e}")

    def get_created_agents(self) -> List[str]:
        """Get list of created agent file paths."""
        return self._created_agents.copy()

    def get_agent_names(self) -> List[str]:
        """Get list of created agent names (without .md extension)."""
        return [
            os.path.splitext(os.path.basename(f))[0]
            for f in self._created_agents
        ]


def build_team_prompt_with_agents(
    leader_prompt: str,
    agent_names: List[str],
    mode: str = "coordinate"
) -> str:
    """
    Build an enhanced prompt for the leader that knows about available subagents.

    Args:
        leader_prompt: Original leader system prompt
        agent_names: List of available subagent names
        mode: Collaboration mode (coordinate or collaborate)

    Returns:
        Enhanced prompt with subagent information
    """
    agents_list = "\n".join([f"- **{name}**: Use Task tool with this agent" for name in agent_names])

    if mode == "coordinate":
        delegation_instructions = """
## Task Delegation
When you need specialized work done:
1. Use the Task tool to delegate to the appropriate specialist
2. Provide clear, specific instructions for the task
3. Wait for the specialist's response
4. Integrate their work into the final result

Example Task tool usage:
```
Task(description="Generate architecture docs", prompt="Analyze the codebase and create architecture documentation with Mermaid diagrams", subagent_type="{agent_name}")
```
"""
    else:  # collaborate
        delegation_instructions = """
## Parallel Collaboration
For comprehensive work, delegate to ALL specialists simultaneously:
1. Use the Task tool to send the same request to each specialist
2. Each specialist will focus on their area of expertise
3. Collect and synthesize all responses
4. Create a unified final output
"""

    enhanced_prompt = f"""{leader_prompt}

## Available Specialist Agents
You have access to the following specialist agents via the Task tool:
{agents_list}

{delegation_instructions}
"""
    return enhanced_prompt
