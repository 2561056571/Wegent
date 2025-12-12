#!/usr/bin/env python

# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""
Claude Code Team Agent

This module provides a team-based Claude Code agent that uses the official
Claude Code subagent approach via .claude/agents/ directory.

The official approach:
1. Create .claude/agents/*.md files defining each specialist
2. Claude Code's Task tool automatically discovers these agents
3. The leader can delegate tasks using Task tool

Supported collaboration modes:
- coordinate: Leader analyzes task, delegates to specific specialists via Task tool
- collaborate: Leader delegates to all specialists in parallel
"""

import os
from typing import Dict, Any, List, Optional

from shared.logger import setup_logger
from shared.status import TaskStatus
from executor.config import config

from .claude_code_agent import ClaudeCodeAgent
from .subagent_builder import SubagentBuilder, build_team_prompt_with_agents

logger = setup_logger("claude_code_team_agent")


class CollaborationMode:
    """Collaboration mode constants."""
    COORDINATE = "coordinate"
    COLLABORATE = "collaborate"


class ClaudeCodeTeamAgent(ClaudeCodeAgent):
    """
    Claude Code Team Agent that uses .claude/agents/ for subagent definitions.

    This agent:
    1. Creates subagent definition files in .claude/agents/
    2. Enhances the leader's prompt to know about available specialists
    3. Uses a single Claude Code instance that can delegate via Task tool
    4. Cleans up subagent files after execution
    """

    def __init__(self, task_data: Dict[str, Any]):
        """
        Initialize the Claude Code Team Agent.

        Args:
            task_data: The task data dictionary containing team configuration
        """
        super().__init__(task_data)

        # Team-specific attributes
        self.mode = task_data.get("mode", CollaborationMode.COORDINATE)
        self._is_team_mode = self._detect_team_mode(task_data)
        self.subagent_builder: Optional[SubagentBuilder] = None
        self._original_prompt = self.prompt
        self._agent_names: List[str] = []

        if self._is_team_mode:
            logger.info(
                f"Initialized ClaudeCodeTeamAgent in team mode with '{self.mode}' collaboration"
            )
        else:
            logger.info("Initialized ClaudeCodeTeamAgent in single agent mode")

    def get_name(self) -> str:
        """Get the agent name."""
        if self._is_team_mode:
            return "ClaudeCodeTeam"
        return "ClaudeCode"

    def _detect_team_mode(self, task_data: Dict[str, Any]) -> bool:
        """
        Detect if the task should run in team mode.

        Team mode is enabled when:
        - There are multiple bots configured
        - The collaboration model is 'coordinate' or 'collaborate'

        Args:
            task_data: The task data dictionary

        Returns:
            True if team mode should be used
        """
        bots = task_data.get("bot", [])
        mode = task_data.get("mode", "")

        if len(bots) < 2:
            return False

        if mode in [CollaborationMode.COORDINATE, CollaborationMode.COLLABORATE]:
            return True

        for bot in bots:
            if bot.get("role") == "leader":
                return True

        return False

    def initialize(self) -> TaskStatus:
        """
        Initialize the Claude Code Team Agent.

        For team mode:
        1. Runs parent initialization (saves settings, downloads skills, etc.)
        2. Creates .claude/agents/ directory with subagent definitions
        3. Enhances the leader's prompt with subagent information

        Returns:
            TaskStatus: Initialization status
        """
        try:
            # Check if task was cancelled before initialization
            if self.task_state_manager.is_cancelled(self.task_id):
                logger.info(f"Task {self.task_id} was cancelled before initialization")
                return TaskStatus.COMPLETED

            # Run parent initialization first
            status = super().initialize()
            if status != TaskStatus.SUCCESS:
                return status

            if not self._is_team_mode:
                return TaskStatus.SUCCESS

            self.add_thinking_step_by_key(
                title_key="thinking.initialize_team",
                report_immediately=False
            )

            # Get project path
            cwd = self.options.get("cwd", self.project_path)
            if not cwd:
                cwd = os.path.join(config.WORKSPACE_ROOT, str(self.task_id))
                os.makedirs(cwd, exist_ok=True)

            # Initialize subagent builder
            self.subagent_builder = SubagentBuilder(cwd)

            # Get team member configurations (excluding leader)
            bots = self.task_data.get("bot", [])
            member_configs = [b for b in bots if b.get("role") != "leader"]
            leader_config = next(
                (b for b in bots if b.get("role") == "leader"),
                bots[0] if bots else None
            )

            # Create subagent files for members
            self.subagent_builder.create_subagents_from_config(member_configs)

            # Get created agent names
            self._agent_names = self.subagent_builder.get_agent_names()

            # Enhance the system prompt with subagent information
            if self._agent_names and leader_config:
                leader_prompt = leader_config.get("system_prompt", "")
                enhanced_prompt = build_team_prompt_with_agents(
                    leader_prompt,
                    self._agent_names,
                    self.mode
                )
                self.options["system_prompt"] = enhanced_prompt
                logger.info(f"Enhanced leader prompt with {len(self._agent_names)} subagents")

            self.add_thinking_step(
                title=f"Team initialized with {len(self._agent_names)} specialist agents",
                report_immediately=True,
                use_i18n_keys=False,
                details={
                    "mode": self.mode,
                    "specialists": self._agent_names
                }
            )

            logger.info("Team mode initialization completed")
            return TaskStatus.SUCCESS

        except Exception as e:
            logger.error(f"Failed to initialize team: {e}")
            self.add_thinking_step_by_key(
                title_key="thinking.initialize_failed",
                report_immediately=False
            )
            return TaskStatus.FAILED

    async def _async_execute(self) -> TaskStatus:
        """
        Asynchronous execution of the Claude Code Team Agent task.

        In team mode, the execution uses a single Claude instance that can
        delegate to specialists via the Task tool. The subagent files in
        .claude/agents/ are automatically discovered by Claude Code.

        Returns:
            TaskStatus: Execution status
        """
        if not self._is_team_mode:
            return await super()._async_execute()

        try:
            if self.task_state_manager.is_cancelled(self.task_id):
                logger.info(f"Task {self.task_id} was cancelled before team execution")
                return TaskStatus.COMPLETED

            # Build the task prompt based on mode and override self.prompt
            # This will be used by parent's _async_execute
            self.prompt = self._build_team_task_prompt()

            self.add_thinking_step(
                title=f"Executing in {self.mode} mode",
                report_immediately=True,
                use_i18n_keys=False
            )

            # Call parent's _async_execute which handles client initialization and query
            result = await super()._async_execute()

            return result

        except Exception as e:
            return self._handle_execution_error(e, "team execution")

        finally:
            if self.subagent_builder:
                self.subagent_builder.cleanup()

    def _build_team_task_prompt(self) -> str:
        """
        Build the task prompt based on collaboration mode.

        Returns:
            Task prompt string
        """
        if self.mode == CollaborationMode.COORDINATE:
            return f"""You have a team of specialists available via the Task tool.

**Your task:**
{self._original_prompt}

**Instructions:**
1. Analyze what needs to be done
2. Delegate specific parts to the appropriate specialists using Task tool
3. Available specialists: {', '.join(self._agent_names)}
4. Collect their responses and synthesize a final result
5. You can delegate to multiple specialists in parallel if their tasks are independent

Use the Task tool like this:
- Task(description="brief desc", prompt="detailed task", subagent_type="specialist-name")

Begin by analyzing the task and delegating to your specialists."""

        else:  # COLLABORATE mode
            return f"""You have a team of specialists available via the Task tool.

**Your task:**
{self._original_prompt}

**Instructions:**
1. Send this task to ALL available specialists simultaneously
2. Available specialists: {', '.join(self._agent_names)}
3. Each specialist will contribute their expertise
4. Collect all responses and create a unified final output

Delegate to all specialists now, then synthesize their contributions."""

    def cancel_run(self) -> bool:
        """
        Cancel the current running task.

        Returns:
            bool: True if cancellation was successful
        """
        result = super().cancel_run()

        if self.subagent_builder:
            self.subagent_builder.cleanup()

        return result

    async def cleanup(self) -> None:
        """Cleanup team resources."""
        if self.subagent_builder:
            self.subagent_builder.cleanup()

        logger.info("Cleaned up ClaudeCodeTeamAgent resources")
