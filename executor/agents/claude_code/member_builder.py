#!/usr/bin/env python

# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""
Claude Code Member Builder

This module provides functionality to build and manage individual Claude Code team members.
Each member is essentially a Claude Code agent with its own configuration derived from Bot CRD.
"""

import asyncio
import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from shared.logger import setup_logger
from executor.utils.mcp_utils import extract_mcp_servers_config

logger = setup_logger("claude_code_member_builder")


class ClaudeCodeMember:
    """
    Represents a single Claude Code team member (subagent).

    Each member has its own system prompt, MCP servers, and configuration,
    but shares the same workspace context with other team members.
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        mcp_servers: Optional[Dict[str, Any]] = None,
        agent_config: Optional[Dict[str, Any]] = None,
        skills: Optional[List[str]] = None
    ):
        """
        Initialize a Claude Code team member.

        Args:
            name: Member name
            role: Member role ('leader' or 'member')
            system_prompt: System prompt for this member
            mcp_servers: MCP servers configuration
            agent_config: Agent configuration (model settings, etc.)
            skills: List of skill names
        """
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.mcp_servers = mcp_servers or {}
        self.agent_config = agent_config or {}
        self.skills = skills or []
        self.client: Optional[ClaudeSDKClient] = None
        self.session_id: Optional[str] = None

    def is_leader(self) -> bool:
        """Check if this member is the team leader."""
        return self.role == "leader"

    def get_options(self) -> Dict[str, Any]:
        """
        Get Claude Code options for this member.

        Returns:
            Dictionary of Claude Code options
        """
        options = {
            "setting_sources": ["user", "project", "local"],
            "permission_mode": "bypassPermissions",
        }

        # Add system prompt if available
        if self.system_prompt:
            options["system_prompt"] = self.system_prompt

        # Add MCP servers if available
        if self.mcp_servers:
            options["mcp_servers"] = self.mcp_servers

        return options

    async def connect(self, cwd: str, session_id: str) -> None:
        """
        Connect the member's Claude Code client.

        Args:
            cwd: Working directory
            session_id: Session ID for this member
        """
        self.session_id = session_id
        options = self.get_options()
        options["cwd"] = cwd

        code_options = ClaudeAgentOptions(**options)
        self.client = ClaudeSDKClient(options=code_options)
        await self.client.connect()

        logger.info(f"Connected Claude Code client for member: {self.name}")

    async def disconnect(self) -> None:
        """Disconnect the member's Claude Code client."""
        if self.client:
            try:
                await self.client.close()
                logger.info(f"Disconnected Claude Code client for member: {self.name}")
            except Exception as e:
                logger.warning(f"Error disconnecting client for member {self.name}: {e}")
            finally:
                self.client = None

    async def query(self, prompt: str) -> None:
        """
        Send a query to this member.

        Args:
            prompt: The prompt to send
        """
        if not self.client:
            raise RuntimeError(f"Member {self.name} is not connected")

        await self.client.query(prompt, session_id=self.session_id)

    async def interrupt(self) -> None:
        """Interrupt the current query."""
        if self.client and hasattr(self.client, 'interrupt'):
            await self.client.interrupt()


class ClaudeCodeMemberBuilder:
    """
    Builds and manages Claude Code team members from Bot configurations.
    """

    def __init__(self, thinking_manager=None):
        """
        Initialize member builder.

        Args:
            thinking_manager: Thinking step manager instance (optional)
        """
        self.thinking_manager = thinking_manager
        self._members: Dict[str, ClaudeCodeMember] = {}

    def create_member(self, member_config: Dict[str, Any]) -> Optional[ClaudeCodeMember]:
        """
        Create a single Claude Code team member from configuration.

        Args:
            member_config: Member configuration from Bot CRD

        Returns:
            ClaudeCodeMember instance or None if creation fails
        """
        try:
            # Extract member properties
            name = member_config.get("name", "TeamMember")
            role = member_config.get("role", "member")
            system_prompt = member_config.get("system_prompt", "")
            agent_config = member_config.get("agent_config", {})
            skills = member_config.get("skills", [])

            # Extract MCP servers configuration
            mcp_servers = extract_mcp_servers_config(member_config)

            # Create member instance
            member = ClaudeCodeMember(
                name=name,
                role=role,
                system_prompt=system_prompt,
                mcp_servers=mcp_servers,
                agent_config=agent_config,
                skills=skills
            )

            # Store member for tracking
            self._members[name] = member

            logger.info(f"Created Claude Code team member: {name} (role: {role})")
            return member

        except Exception as e:
            logger.error(f"Failed to create Claude Code team member: {e}")
            return None

    def create_members_from_config(
        self,
        team_members_config: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple team members from configuration list.

        Args:
            team_members_config: List of member configurations

        Returns:
            Dictionary containing:
            - leader: Team leader (Optional[ClaudeCodeMember])
            - members: List of other team members (List[ClaudeCodeMember])
        """
        leader: Optional[ClaudeCodeMember] = None
        members: List[ClaudeCodeMember] = []

        for member_config in team_members_config:
            member = self.create_member(member_config)
            if member:
                if member.is_leader():
                    if leader is None:
                        leader = member
                        logger.info(f"Found team leader: {member.name}")
                    else:
                        logger.warning(
                            f"Multiple team leaders found. Using first one, ignoring: {member.name}"
                        )
                        members.append(member)
                else:
                    members.append(member)

        logger.info(
            f"Team creation completed: leader={'Yes' if leader else 'No'}, "
            f"members={len(members)}"
        )

        return {
            "leader": leader,
            "members": members
        }

    def get_member(self, name: str) -> Optional[ClaudeCodeMember]:
        """Get a member by name."""
        return self._members.get(name)

    def get_all_members(self) -> List[ClaudeCodeMember]:
        """Get all created members."""
        return list(self._members.values())

    async def cleanup_all_members(self) -> None:
        """Disconnect and cleanup all members."""
        for name, member in self._members.items():
            try:
                await member.disconnect()
            except Exception as e:
                logger.warning(f"Error cleaning up member {name}: {e}")

        self._members.clear()
        logger.info("Cleaned up all Claude Code team members")
