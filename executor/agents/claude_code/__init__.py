#!/usr/bin/env python

# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from executor.agents.claude_code.claude_code_agent import ClaudeCodeAgent
from executor.agents.claude_code.team_agent import ClaudeCodeTeamAgent, CollaborationMode
from executor.agents.claude_code.subagent_builder import (
    SubagentBuilder,
    SubagentDefinition,
    build_team_prompt_with_agents,
)

# Legacy imports for backward compatibility
from executor.agents.claude_code.team_builder import (
    ClaudeCodeTeam,
    ClaudeCodeTeamBuilder,
)
from executor.agents.claude_code.member_builder import (
    ClaudeCodeMember,
    ClaudeCodeMemberBuilder,
)

__all__ = [
    # Primary exports
    "ClaudeCodeAgent",
    "ClaudeCodeTeamAgent",
    "CollaborationMode",
    "SubagentBuilder",
    "SubagentDefinition",
    "build_team_prompt_with_agents",
    # Legacy exports (for backward compatibility)
    "ClaudeCodeTeam",
    "ClaudeCodeTeamBuilder",
    "ClaudeCodeMember",
    "ClaudeCodeMemberBuilder",
]