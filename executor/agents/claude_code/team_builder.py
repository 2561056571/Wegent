#!/usr/bin/env python

# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""
Claude Code Team Builder

This module provides functionality to build and manage Claude Code teams
with coordinate and collaborate collaboration modes.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, AsyncIterator

from shared.logger import setup_logger
from shared.status import TaskStatus
from .member_builder import ClaudeCodeMember, ClaudeCodeMemberBuilder

logger = setup_logger("claude_code_team_builder")


class CollaborationMode:
    """Collaboration mode constants."""
    COORDINATE = "coordinate"  # Leader splits tasks, selects members, summarizes
    COLLABORATE = "collaborate"  # All members work in parallel, leader summarizes


class ClaudeCodeTeam:
    """
    Represents a Claude Code team with a leader and multiple members.

    The team supports two collaboration modes:
    - coordinate: Leader analyzes the task, delegates to specific members, and summarizes
    - collaborate: All members process the task in parallel, leader summarizes results
    """

    def __init__(
        self,
        name: str,
        leader: ClaudeCodeMember,
        members: List[ClaudeCodeMember],
        mode: str = CollaborationMode.COORDINATE,
        session_id: str = "",
        shared_context: bool = True
    ):
        """
        Initialize a Claude Code team.

        Args:
            name: Team name
            leader: Team leader (ClaudeCodeMember)
            members: List of team members (ClaudeCodeMember)
            mode: Collaboration mode ('coordinate' or 'collaborate')
            session_id: Base session ID for the team
            shared_context: Whether all members share the same conversation context
        """
        self.name = name
        self.leader = leader
        self.members = members
        self.mode = mode
        self.session_id = session_id
        self.shared_context = shared_context
        self._cwd: Optional[str] = None
        self._is_running = False
        self._conversation_history: List[Dict[str, Any]] = []

    @property
    def all_members(self) -> List[ClaudeCodeMember]:
        """Get all members including the leader."""
        return [self.leader] + self.members

    @property
    def member_names(self) -> List[str]:
        """Get names of all non-leader members."""
        return [m.name for m in self.members]

    async def initialize(self, cwd: str) -> None:
        """
        Initialize the team by connecting the leader.
        Members are connected on-demand when they receive tasks.

        Args:
            cwd: Working directory for all members
        """
        self._cwd = cwd

        # Connect leader immediately (always needed)
        leader_session_id = f"{self.session_id}_leader" if not self.shared_context else self.session_id
        await self.leader.connect(cwd, leader_session_id)

        logger.info(
            f"Initialized team '{self.name}' with leader '{self.leader.name}' "
            f"({len(self.members)} members available for on-demand connection) in '{self.mode}' mode"
        )

    async def connect_member(self, member: 'ClaudeCodeMember', index: int = 0) -> None:
        """
        Connect a specific team member on-demand.

        Args:
            member: The member to connect
            index: Index of the member for session ID generation
        """
        if member.client is not None:
            # Already connected
            return

        if self.shared_context:
            member_session_id = self.session_id
        else:
            member_session_id = f"{self.session_id}_member_{index}"

        await member.connect(self._cwd, member_session_id)
        logger.info(f"Connected member '{member.name}' on-demand")

    async def cleanup(self) -> None:
        """Cleanup all team resources."""
        # Disconnect leader
        await self.leader.disconnect()

        # Disconnect all members
        for member in self.members:
            await member.disconnect()

        self._conversation_history.clear()
        logger.info(f"Cleaned up team '{self.name}'")

    def _build_coordination_prompt(self, original_prompt: str) -> str:
        """
        Build the coordination prompt for the leader in coordinate mode.

        Args:
            original_prompt: The original user prompt

        Returns:
            Enhanced prompt for task coordination
        """
        member_descriptions = []
        for member in self.members:
            desc = f"- **{member.name}**: {member.system_prompt[:200]}..." if len(
                member.system_prompt) > 200 else f"- **{member.name}**: {member.system_prompt}"
            member_descriptions.append(desc)

        members_info = "\n".join(member_descriptions)

        coordination_prompt = f"""You are the team leader coordinating a task with the following team members:

{members_info}

**Your Responsibilities:**
1. Analyze the user's request and break it down into subtasks
2. Decide which team member(s) should handle each subtask based on their expertise
3. Delegate tasks to appropriate members using the format: @member_name: <task description>
4. After receiving responses from members, synthesize the results into a coherent final response

**Original User Request:**
{original_prompt}

**Instructions:**
- First, analyze the request and identify the subtasks
- Then, delegate each subtask to the most suitable team member
- Use @member_name to address specific members
- Coordinate the work and provide a unified response
"""
        return coordination_prompt

    def _build_planning_prompt(self, original_prompt: str) -> str:
        """
        Build a planning prompt for the leader to create a task plan.

        Args:
            original_prompt: The original user prompt

        Returns:
            Planning prompt for the leader
        """
        member_descriptions = []
        for member in self.members:
            desc = f"- **{member.name}**: {member.system_prompt[:300]}..." if len(
                member.system_prompt) > 300 else f"- **{member.name}**: {member.system_prompt}"
            member_descriptions.append(desc)

        members_info = "\n".join(member_descriptions)

        planning_prompt = f"""You are the team leader. Your task is to create a plan to delegate work to your team members.

**Available Team Members:**
{members_info}

**Original Request:**
{original_prompt}

**Your Task:**
Create a task delegation plan. For each team member you want to assign work to, use this format:

@member-name: Specific task description for this member

For example:
@wiki-overview-bot: Generate the project overview section including introduction and features
@wiki-architecture-bot: Create the system architecture diagram and component descriptions

**Important:**
- Assign tasks only to the most relevant team members based on their expertise
- Be specific about what each member should produce
- Each member will work in parallel, so tasks should be independent
- You can skip members if their expertise is not needed for this request

Now create your delegation plan:
"""
        return planning_prompt

    def _build_collaboration_prompt(self, original_prompt: str) -> str:
        """
        Build the collaboration prompt for parallel processing.

        Args:
            original_prompt: The original user prompt

        Returns:
            Enhanced prompt for collaboration
        """
        return f"""You are working as part of a collaborative team.
All team members will process this request in parallel.

**Your Task:**
{original_prompt}

**Instructions:**
- Focus on your area of expertise as defined in your system prompt
- Provide your analysis and contributions
- Your response will be combined with other team members' responses
"""

    def _build_summary_prompt(self, responses: Dict[str, str], original_prompt: str) -> str:
        """
        Build a summary prompt for the leader to synthesize member responses.

        Args:
            responses: Dictionary of member name to their response
            original_prompt: The original user prompt

        Returns:
            Summary prompt for the leader
        """
        response_sections = []
        for name, response in responses.items():
            response_sections.append(f"**Response from {name}:**\n{response}\n")

        responses_text = "\n---\n".join(response_sections)

        summary_prompt = f"""As the team leader, synthesize the following responses from your team members into a coherent final answer.

**Original Request:**
{original_prompt}

**Team Member Responses:**
{responses_text}

**Your Task:**
- Review all team member responses
- Identify key insights and contributions from each
- Resolve any conflicts or inconsistencies
- Provide a unified, comprehensive response to the original request
"""
        return summary_prompt

    def get_team_info(self) -> Dict[str, Any]:
        """
        Get information about the team structure.

        Returns:
            Dictionary containing team information
        """
        return {
            "name": self.name,
            "mode": self.mode,
            "leader": {
                "name": self.leader.name,
                "role": self.leader.role,
            },
            "members": [
                {
                    "name": m.name,
                    "role": m.role,
                }
                for m in self.members
            ],
            "shared_context": self.shared_context,
            "session_id": self.session_id,
        }


class ClaudeCodeTeamBuilder:
    """
    Builds and manages Claude Code teams from Team CRD configurations.
    """

    def __init__(self, thinking_manager=None):
        """
        Initialize team builder.

        Args:
            thinking_manager: Thinking step manager instance (optional)
        """
        self.thinking_manager = thinking_manager
        self.member_builder = ClaudeCodeMemberBuilder(thinking_manager)
        self._teams: Dict[str, ClaudeCodeTeam] = {}

    async def create_team(
        self,
        options: Dict[str, Any],
        mode: str,
        session_id: str,
        task_data: Dict[str, Any]
    ) -> Optional[ClaudeCodeTeam]:
        """
        Create a Claude Code team from configuration.

        Args:
            options: Team configuration options
            mode: Collaboration mode ('coordinate' or 'collaborate')
            session_id: Session ID for the team
            task_data: Task data containing bot configurations

        Returns:
            Configured ClaudeCodeTeam instance or None if creation fails
        """
        logger.info(f"Starting to build Claude Code team with mode: {mode}")

        # Get team members configuration from bot list
        team_members_config = task_data.get("bot", [])

        if not team_members_config:
            logger.error("No bot configurations found for team creation")
            return None

        # Create team members
        team_data = self.member_builder.create_members_from_config(team_members_config)
        leader = team_data["leader"]
        members = team_data["members"]

        # Validate team structure
        if leader is None:
            if len(members) < 2:
                logger.error("Team requires at least 2 members or 1 leader + 1 member")
                return None
            # Use first member as leader if no explicit leader
            leader = members.pop(0)
            leader.role = "leader"
            logger.info(f"No explicit leader found, using {leader.name} as leader")

        if len(members) == 0:
            logger.error("Team requires at least one non-leader member")
            return None

        # Validate mode
        if mode not in [CollaborationMode.COORDINATE, CollaborationMode.COLLABORATE]:
            logger.warning(f"Unknown mode '{mode}', defaulting to 'coordinate'")
            mode = CollaborationMode.COORDINATE

        # Create team instance
        team_name = options.get("team_name", "ClaudeCodeTeam")
        shared_context = options.get("shared_context", True)

        team = ClaudeCodeTeam(
            name=team_name,
            leader=leader,
            members=members,
            mode=mode,
            session_id=session_id,
            shared_context=shared_context
        )

        # Store team for tracking
        self._teams[team_name] = team

        logger.info(
            f"Created Claude Code team '{team_name}' with leader '{leader.name}' "
            f"and {len(members)} members in '{mode}' mode"
        )

        return team

    def get_team(self, name: str) -> Optional[ClaudeCodeTeam]:
        """Get a team by name."""
        return self._teams.get(name)

    async def cleanup(self) -> None:
        """Cleanup all teams and members."""
        for name, team in self._teams.items():
            try:
                await team.cleanup()
            except Exception as e:
                logger.warning(f"Error cleaning up team {name}: {e}")

        self._teams.clear()
        await self.member_builder.cleanup_all_members()
        logger.info("Cleaned up all Claude Code teams")

    def _get_mode_config(self, mode: str) -> Dict[str, Any]:
        """
        Get mode configuration.

        Args:
            mode: Collaboration mode

        Returns:
            Mode configuration dictionary
        """
        if mode == CollaborationMode.COORDINATE:
            return {
                "delegate_to_specific": True,
                "require_summary": True,
            }
        elif mode == CollaborationMode.COLLABORATE:
            return {
                "parallel_execution": True,
                "require_summary": True,
            }
        else:
            return {
                "delegate_to_specific": False,
                "parallel_execution": False,
            }
