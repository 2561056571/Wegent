#!/usr/bin/env python

# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from typing import Dict, Any, Optional

from shared.logger import setup_logger
from executor.agents.base import Agent
from executor.agents.claude_code.claude_code_agent import ClaudeCodeAgent
from executor.agents.claude_code.team_agent import ClaudeCodeTeamAgent
from executor.agents.agno.agno_agent import AgnoAgent
from executor.agents.dify.dify_agent import DifyAgent
from executor.agents.image_validator.image_validator_agent import ImageValidatorAgent

logger = setup_logger("agent_factory")


# Collaboration modes that indicate team execution
TEAM_COLLABORATION_MODES = ["coordinate", "collaborate"]


class AgentFactory:
    """
    Factory class for creating agent instances based on agent_type

    Agents are classified into types:
    - local_engine: Agents that execute code locally (ClaudeCode, Agno)
    - external_api: Agents that delegate execution to external services (Dify)
    - validator: Agents that perform validation tasks (ImageValidator)
    """

    _agents = {
        "claudecode": ClaudeCodeAgent,
        "claudecodeteam": ClaudeCodeTeamAgent,
        "agno": AgnoAgent,
        "dify": DifyAgent,
        "imagevalidator": ImageValidatorAgent,
    }

    @classmethod
    def get_agent(cls, agent_type: str, task_data: Dict[str, Any]) -> Optional[Agent]:
        """
        Get an agent instance based on agent_type

        For ClaudeCode agents, automatically determines whether to use
        single agent or team agent based on task configuration.

        Args:
            agent_type: The type of agent to create
            task_data: The task data to pass to the agent

        Returns:
            An instance of the requested agent, or None if the agent_type is not supported
        """
        normalized_type = agent_type.lower()

        # Special handling for ClaudeCode: check if team mode is needed
        if normalized_type == "claudecode":
            if cls._should_use_team_mode(task_data):
                logger.info("Detected team configuration, using ClaudeCodeTeamAgent")
                return ClaudeCodeTeamAgent(task_data)

        agent_class = cls._agents.get(normalized_type)
        if agent_class:
            return agent_class(task_data)
        else:
            logger.error(f"Unsupported agent type: {agent_type}")
            return None

    @classmethod
    def _should_use_team_mode(cls, task_data: Dict[str, Any]) -> bool:
        """
        Determine if task should use team mode based on configuration.

        Team mode is enabled when:
        - There are multiple bots configured (more than 1)
        - The mode is 'coordinate' or 'collaborate'
        - Any bot has a 'leader' role

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
        if mode in TEAM_COLLABORATION_MODES:
            return True

        # Check if any bot has a 'leader' role
        for bot in bots:
            if bot.get("role") == "leader":
                return True

        return False

    @classmethod
    def is_external_api_agent(cls, agent_type: str) -> bool:
        """
        Check if an agent type is an external API type

        Args:
            agent_type: The type of agent to check

        Returns:
            True if the agent is an external API type, False otherwise
        """
        agent_class = cls._agents.get(agent_type.lower())
        if agent_class and hasattr(agent_class, 'AGENT_TYPE'):
            return agent_class.AGENT_TYPE == "external_api"
        return False

    @classmethod
    def get_agent_type(cls, agent_type: str) -> Optional[str]:
        """
        Get the agent type classification (local_engine or external_api)

        Args:
            agent_type: The type of agent to check

        Returns:
            "local_engine", "external_api", or None if agent type not found
        """
        agent_class = cls._agents.get(agent_type.lower())
        if agent_class:
            if hasattr(agent_class, 'AGENT_TYPE'):
                return agent_class.AGENT_TYPE
            return "local_engine"  # Default for older agents without AGENT_TYPE
        return None
