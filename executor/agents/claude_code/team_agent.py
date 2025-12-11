#!/usr/bin/env python

# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""
Claude Code Team Agent

This module provides a team-based Claude Code agent that coordinates
multiple Claude Code subagents to work together on tasks.

Supported collaboration modes:
- coordinate: Leader analyzes task, delegates to specific members, summarizes results
- collaborate: All members process in parallel, leader summarizes results
"""

import asyncio
import os
import re
from typing import Dict, Any, List, Optional, Tuple

from shared.logger import setup_logger
from shared.status import TaskStatus
from shared.models.task import ThinkingStep, ExecutionResult
from executor.config import config

from .claude_code_agent import ClaudeCodeAgent
from .team_builder import ClaudeCodeTeam, ClaudeCodeTeamBuilder, CollaborationMode
from .member_builder import ClaudeCodeMember
from .response_processor import process_response

logger = setup_logger("claude_code_team_agent")


class ClaudeCodeTeamAgent(ClaudeCodeAgent):
    """
    Claude Code Team Agent that coordinates multiple Claude Code subagents.

    This agent extends ClaudeCodeAgent to support team collaboration modes
    similar to Agno's team functionality, but using Claude Code SDK.
    """

    def __init__(self, task_data: Dict[str, Any]):
        """
        Initialize the Claude Code Team Agent.

        Args:
            task_data: The task data dictionary containing team configuration
        """
        super().__init__(task_data)

        # Team-specific attributes
        self.team: Optional[ClaudeCodeTeam] = None
        self.team_builder: Optional[ClaudeCodeTeamBuilder] = None
        self.mode = task_data.get("mode", CollaborationMode.COORDINATE)
        self._is_team_mode = self._detect_team_mode(task_data)

        if self._is_team_mode:
            self.team_builder = ClaudeCodeTeamBuilder(self.thinking_manager)
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

        # Check if we have multiple bots
        if len(bots) < 2:
            return False

        # Check if the mode is a team collaboration mode
        if mode in [CollaborationMode.COORDINATE, CollaborationMode.COLLABORATE]:
            return True

        # Check if any bot has a 'leader' role
        for bot in bots:
            if bot.get("role") == "leader":
                return True

        return False

    def initialize(self) -> TaskStatus:
        """
        Initialize the Claude Code Team Agent.

        Returns:
            TaskStatus: Initialization status
        """
        # First run parent initialization
        status = super().initialize()
        if status != TaskStatus.SUCCESS:
            return status

        if not self._is_team_mode:
            return TaskStatus.SUCCESS

        try:
            self.add_thinking_step_by_key(
                title_key="thinking.initialize_team",
                report_immediately=False
            )

            logger.info("Team mode initialization completed")
            return TaskStatus.SUCCESS

        except Exception as e:
            logger.error(f"Failed to initialize team: {e}")
            return TaskStatus.FAILED

    async def _async_execute(self) -> TaskStatus:
        """
        Asynchronous execution of the Claude Code Team Agent task.

        Returns:
            TaskStatus: Execution status
        """
        if not self._is_team_mode:
            # Fall back to single agent mode
            return await super()._async_execute()

        try:
            # Check cancellation
            if self.task_state_manager.is_cancelled(self.task_id):
                logger.info(f"Task {self.task_id} was cancelled before team execution")
                return TaskStatus.COMPLETED

            progress = 65
            self._update_progress(progress)

            # Create and initialize team
            team_options = {
                "team_name": self.task_data.get("team_name", "ClaudeCodeTeam"),
                "shared_context": True,
            }

            self.team = await self.team_builder.create_team(
                options=team_options,
                mode=self.mode,
                session_id=self.session_id,
                task_data=self.task_data
            )

            if not self.team:
                logger.error("Failed to create team")
                return TaskStatus.FAILED

            # Initialize team with working directory
            cwd = self.options.get("cwd", self.project_path)
            if not cwd:
                cwd = os.path.join(config.WORKSPACE_ROOT, str(self.task_id))
                os.makedirs(cwd, exist_ok=True)

            await self.team.initialize(cwd)

            self.add_thinking_step(
                title=f"Team initialized: {self.team.leader.name} + {len(self.team.members)} members",
                report_immediately=True,
                use_i18n_keys=False,
                details={
                    "leader": self.team.leader.name,
                    "members": self.team.member_names,
                    "mode": self.mode
                }
            )

            progress = 75
            self._update_progress(progress)

            # Execute based on collaboration mode
            if self.mode == CollaborationMode.COORDINATE:
                result = await self._execute_coordinate_mode()
            else:
                result = await self._execute_collaborate_mode()

            return result

        except Exception as e:
            return self._handle_execution_error(e, "team execution")

        finally:
            # Cleanup team resources
            if self.team:
                await self.team.cleanup()

    async def _execute_coordinate_mode(self) -> TaskStatus:
        """
        Execute task in coordinate mode.

        In coordinate mode:
        1. Leader analyzes the task and breaks it down
        2. Leader delegates subtasks to specific members
        3. Members execute their assigned tasks
        4. Leader summarizes the results

        Returns:
            TaskStatus: Execution status
        """
        logger.info("Executing in COORDINATE mode")

        self.add_thinking_step(
            title="Starting coordinate mode execution",
            report_immediately=True,
            use_i18n_keys=False
        )

        # Build coordination prompt for leader
        coordination_prompt = self.team._build_coordination_prompt(self.prompt)

        # Send to leader
        logger.info(f"Sending coordination prompt to leader: {self.team.leader.name}")
        await self.team.leader.query(coordination_prompt)

        # Process leader's response
        result = await process_response(
            self.team.leader.client,
            self.state_manager,
            self.thinking_manager,
            self.task_state_manager,
            session_id=self.team.leader.session_id
        )

        # Check for member delegation in leader's response
        # This is a simplified implementation - in production, you'd parse
        # the leader's response to identify delegated tasks

        return result

    async def _execute_collaborate_mode(self) -> TaskStatus:
        """
        Execute task in collaborate mode.

        In collaborate mode:
        1. All members receive the same task in parallel
        2. Each member processes based on their expertise
        3. Leader summarizes all responses

        Returns:
            TaskStatus: Execution status
        """
        logger.info("Executing in COLLABORATE mode")

        self.add_thinking_step(
            title="Starting collaborate mode execution",
            report_immediately=True,
            use_i18n_keys=False,
            details={"members": self.team.member_names}
        )

        # Build collaboration prompt
        collab_prompt = self.team._build_collaboration_prompt(self.prompt)

        # Send to all members in parallel
        member_tasks = []
        for member in self.team.members:
            task = asyncio.create_task(self._query_member(member, collab_prompt))
            member_tasks.append((member.name, task))

        # Wait for all members to complete
        member_responses: Dict[str, str] = {}
        for name, task in member_tasks:
            try:
                response = await task
                member_responses[name] = response
                logger.info(f"Received response from member: {name}")
            except Exception as e:
                logger.error(f"Error getting response from member {name}: {e}")
                member_responses[name] = f"Error: {str(e)}"

        # Have leader summarize the responses
        summary_prompt = self.team._build_summary_prompt(member_responses, self.prompt)

        self.add_thinking_step(
            title="All members completed, leader summarizing",
            report_immediately=True,
            use_i18n_keys=False,
            details={"responses_received": len(member_responses)}
        )

        # Send summary prompt to leader
        await self.team.leader.query(summary_prompt)

        # Process leader's final response
        result = await process_response(
            self.team.leader.client,
            self.state_manager,
            self.thinking_manager,
            self.task_state_manager,
            session_id=self.team.leader.session_id
        )

        return result

    async def _query_member(self, member: ClaudeCodeMember, prompt: str) -> str:
        """
        Send a query to a team member and collect the response.

        Args:
            member: The team member to query
            prompt: The prompt to send

        Returns:
            The member's response as a string
        """
        try:
            await member.query(prompt)

            # Collect response
            response_parts = []
            async for msg in member.client.receive_response():
                if hasattr(msg, 'content'):
                    response_parts.append(str(msg.content))

            return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"Error querying member {member.name}: {e}")
            raise

    def cancel_run(self) -> bool:
        """
        Cancel the current running task.

        Returns:
            bool: True if cancellation was successful
        """
        # First cancel the parent
        result = super().cancel_run()

        # Then cancel team members if in team mode
        if self._is_team_mode and self.team:
            try:
                # Create async task to cancel all members
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(self._async_cancel_team())
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self._async_cancel_team())
                    finally:
                        loop.close()
            except Exception as e:
                logger.error(f"Error cancelling team: {e}")

        return result

    async def _async_cancel_team(self) -> None:
        """Asynchronously cancel all team members."""
        if not self.team:
            return

        # Interrupt leader
        try:
            await self.team.leader.interrupt()
        except Exception as e:
            logger.warning(f"Error interrupting leader: {e}")

        # Interrupt all members
        for member in self.team.members:
            try:
                await member.interrupt()
            except Exception as e:
                logger.warning(f"Error interrupting member {member.name}: {e}")

        logger.info("Cancelled all team members")

    async def cleanup(self) -> None:
        """Cleanup team resources."""
        if self.team_builder:
            await self.team_builder.cleanup()

        logger.info("Cleaned up ClaudeCodeTeamAgent resources")
