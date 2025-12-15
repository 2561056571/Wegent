# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for Claude Code Team Agent and related components.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from executor.agents.claude_code.member_builder import (
    ClaudeCodeMember,
    ClaudeCodeMemberBuilder,
)
from executor.agents.claude_code.team_builder import (
    ClaudeCodeTeam,
    ClaudeCodeTeamBuilder,
    CollaborationMode,
)
from executor.agents.claude_code.team_agent import ClaudeCodeTeamAgent
from executor.agents.factory import AgentFactory


class TestClaudeCodeMember:
    """Test cases for ClaudeCodeMember"""

    def test_member_creation(self):
        """Test creating a member with basic configuration"""
        member = ClaudeCodeMember(
            name="TestMember",
            role="member",
            system_prompt="You are a test member",
            mcp_servers={},
            agent_config={},
            skills=[]
        )

        assert member.name == "TestMember"
        assert member.role == "member"
        assert member.system_prompt == "You are a test member"
        assert not member.is_leader()

    def test_leader_member(self):
        """Test creating a leader member"""
        member = ClaudeCodeMember(
            name="Leader",
            role="leader",
            system_prompt="You are the team leader"
        )

        assert member.is_leader()
        assert member.role == "leader"

    def test_get_options(self):
        """Test getting member options"""
        member = ClaudeCodeMember(
            name="TestMember",
            role="member",
            system_prompt="Test prompt",
            mcp_servers={"test_server": {"command": "test"}}
        )

        options = member.get_options()

        assert "setting_sources" in options
        assert "permission_mode" in options
        assert options["system_prompt"] == "Test prompt"
        assert "mcp_servers" in options


class TestClaudeCodeMemberBuilder:
    """Test cases for ClaudeCodeMemberBuilder"""

    def test_create_member(self):
        """Test creating a member from configuration"""
        builder = ClaudeCodeMemberBuilder()

        member_config = {
            "name": "Coder",
            "role": "member",
            "system_prompt": "You are a coding expert",
            "agent_config": {"model": "claude-3"},
            "skills": ["coding"]
        }

        member = builder.create_member(member_config)

        assert member is not None
        assert member.name == "Coder"
        assert member.role == "member"
        assert member.system_prompt == "You are a coding expert"

    def test_create_members_from_config(self):
        """Test creating multiple members from configuration"""
        builder = ClaudeCodeMemberBuilder()

        team_config = [
            {"name": "Leader", "role": "leader", "system_prompt": "Team leader"},
            {"name": "Coder", "role": "member", "system_prompt": "Coding expert"},
            {"name": "Reviewer", "role": "member", "system_prompt": "Code reviewer"},
        ]

        result = builder.create_members_from_config(team_config)

        assert result["leader"] is not None
        assert result["leader"].name == "Leader"
        assert len(result["members"]) == 2

    def test_create_members_without_leader(self):
        """Test creating members without explicit leader"""
        builder = ClaudeCodeMemberBuilder()

        team_config = [
            {"name": "Coder", "role": "member", "system_prompt": "Coding expert"},
            {"name": "Reviewer", "role": "member", "system_prompt": "Code reviewer"},
        ]

        result = builder.create_members_from_config(team_config)

        assert result["leader"] is None
        assert len(result["members"]) == 2


class TestClaudeCodeTeam:
    """Test cases for ClaudeCodeTeam"""

    @pytest.fixture
    def sample_team(self):
        """Create a sample team for testing"""
        leader = ClaudeCodeMember(
            name="Leader",
            role="leader",
            system_prompt="You are the team leader"
        )
        member1 = ClaudeCodeMember(
            name="Coder",
            role="member",
            system_prompt="You are a coding expert"
        )
        member2 = ClaudeCodeMember(
            name="Reviewer",
            role="member",
            system_prompt="You are a code reviewer"
        )

        return ClaudeCodeTeam(
            name="TestTeam",
            leader=leader,
            members=[member1, member2],
            mode=CollaborationMode.COORDINATE,
            session_id="test_session"
        )

    def test_team_creation(self, sample_team):
        """Test team creation"""
        assert sample_team.name == "TestTeam"
        assert sample_team.leader.name == "Leader"
        assert len(sample_team.members) == 2
        assert sample_team.mode == CollaborationMode.COORDINATE

    def test_all_members(self, sample_team):
        """Test getting all members including leader"""
        all_members = sample_team.all_members

        assert len(all_members) == 3
        assert sample_team.leader in all_members

    def test_member_names(self, sample_team):
        """Test getting member names"""
        names = sample_team.member_names

        assert "Coder" in names
        assert "Reviewer" in names
        assert "Leader" not in names

    def test_team_info(self, sample_team):
        """Test getting team info"""
        info = sample_team.get_team_info()

        assert info["name"] == "TestTeam"
        assert info["mode"] == CollaborationMode.COORDINATE
        assert info["leader"]["name"] == "Leader"
        assert len(info["members"]) == 2

    def test_coordination_prompt(self, sample_team):
        """Test building coordination prompt"""
        prompt = sample_team._build_coordination_prompt("Test user request")

        assert "team leader" in prompt.lower()
        assert "Coder" in prompt
        assert "Reviewer" in prompt
        assert "Test user request" in prompt

    def test_collaboration_prompt(self, sample_team):
        """Test building collaboration prompt"""
        prompt = sample_team._build_collaboration_prompt("Test task")

        assert "collaborative team" in prompt.lower()
        assert "Test task" in prompt

    def test_summary_prompt(self, sample_team):
        """Test building summary prompt"""
        responses = {
            "Coder": "I implemented the feature",
            "Reviewer": "Code looks good"
        }

        prompt = sample_team._build_summary_prompt(responses, "Original request")

        assert "synthesize" in prompt.lower()
        assert "I implemented the feature" in prompt
        assert "Code looks good" in prompt
        assert "Original request" in prompt


class TestClaudeCodeTeamBuilder:
    """Test cases for ClaudeCodeTeamBuilder"""

    @pytest.fixture
    def sample_task_data(self):
        """Sample task data with team configuration"""
        return {
            "task_id": 123,
            "subtask_id": 456,
            "mode": "coordinate",
            "bot": [
                {
                    "name": "Leader",
                    "role": "leader",
                    "system_prompt": "Team leader",
                    "agent_config": {}
                },
                {
                    "name": "Coder",
                    "role": "member",
                    "system_prompt": "Coding expert",
                    "agent_config": {}
                },
            ],
            "user": {"user_name": "testuser"}
        }

    @pytest.mark.asyncio
    async def test_create_team(self, sample_task_data):
        """Test creating a team from task data"""
        builder = ClaudeCodeTeamBuilder()

        team = await builder.create_team(
            options={"team_name": "TestTeam"},
            mode=CollaborationMode.COORDINATE,
            session_id="test_session",
            task_data=sample_task_data
        )

        assert team is not None
        assert team.name == "TestTeam"
        assert team.leader.name == "Leader"
        assert len(team.members) == 1

    @pytest.mark.asyncio
    async def test_create_team_invalid_config(self):
        """Test creating team with invalid configuration"""
        builder = ClaudeCodeTeamBuilder()

        team = await builder.create_team(
            options={},
            mode=CollaborationMode.COORDINATE,
            session_id="test",
            task_data={"bot": []}  # Empty bot config
        )

        assert team is None

    @pytest.mark.asyncio
    async def test_create_team_single_bot(self):
        """Test that single bot does not create team"""
        builder = ClaudeCodeTeamBuilder()

        task_data = {
            "bot": [
                {"name": "SingleBot", "role": "member", "system_prompt": "Test"}
            ]
        }

        team = await builder.create_team(
            options={},
            mode=CollaborationMode.COORDINATE,
            session_id="test",
            task_data=task_data
        )

        assert team is None


class TestAgentFactoryTeamMode:
    """Test cases for AgentFactory team mode detection"""

    @pytest.fixture(autouse=True)
    def mock_http_requests(self):
        """Mock HTTP requests"""
        with patch('executor.callback.callback_client.requests.post') as mock_post:
            mock_post_response = MagicMock()
            mock_post_response.status_code = 200
            mock_post.return_value = mock_post_response
            yield

    def test_should_use_team_mode_with_coordinate(self):
        """Test team mode detection with coordinate mode"""
        task_data = {
            "bot": [
                {"name": "Leader", "role": "leader"},
                {"name": "Member", "role": "member"}
            ],
            "mode": "coordinate"
        }

        assert AgentFactory._should_use_team_mode(task_data) is True

    def test_should_use_team_mode_with_collaborate(self):
        """Test team mode detection with collaborate mode"""
        task_data = {
            "bot": [
                {"name": "Member1", "role": "member"},
                {"name": "Member2", "role": "member"}
            ],
            "mode": "collaborate"
        }

        assert AgentFactory._should_use_team_mode(task_data) is True

    def test_should_not_use_team_mode_single_bot(self):
        """Test no team mode with single bot"""
        task_data = {
            "bot": [{"name": "SingleBot"}],
            "mode": "coordinate"
        }

        assert AgentFactory._should_use_team_mode(task_data) is False

    def test_should_use_team_mode_with_leader_role(self):
        """Test team mode detection with leader role"""
        task_data = {
            "bot": [
                {"name": "Leader", "role": "leader"},
                {"name": "Member", "role": "member"}
            ],
            "mode": ""  # No explicit mode
        }

        assert AgentFactory._should_use_team_mode(task_data) is True

    def test_get_agent_returns_team_agent(self):
        """Test that factory returns team agent for team config"""
        task_data = {
            "task_id": 123,
            "subtask_id": 456,
            "bot": [
                {"name": "Leader", "role": "leader", "system_prompt": "Lead"},
                {"name": "Member", "role": "member", "system_prompt": "Help"}
            ],
            "mode": "coordinate",
            "user": {"user_name": "test"}
        }

        agent = AgentFactory.get_agent("claudecode", task_data)

        assert agent is not None
        assert isinstance(agent, ClaudeCodeTeamAgent)


class TestClaudeCodeTeamAgent:
    """Test cases for ClaudeCodeTeamAgent"""

    @pytest.fixture(autouse=True)
    def mock_http_requests(self):
        """Mock HTTP requests"""
        with patch('executor.callback.callback_client.requests.post') as mock_post:
            mock_post_response = MagicMock()
            mock_post_response.status_code = 200
            mock_post.return_value = mock_post_response
            yield

    @pytest.fixture
    def team_task_data(self):
        """Sample task data for team agent"""
        return {
            "task_id": 123,
            "subtask_id": 456,
            "prompt": "Test prompt",
            "mode": "coordinate",
            "bot": [
                {
                    "name": "Leader",
                    "role": "leader",
                    "system_prompt": "Team leader",
                    "agent_config": {}
                },
                {
                    "name": "Coder",
                    "role": "member",
                    "system_prompt": "Coding expert",
                    "agent_config": {}
                },
            ],
            "user": {"user_name": "testuser"}
        }

    @pytest.fixture
    def single_bot_task_data(self):
        """Sample task data for single agent"""
        return {
            "task_id": 123,
            "subtask_id": 456,
            "prompt": "Test prompt",
            "bot": [
                {
                    "name": "SingleBot",
                    "system_prompt": "Test bot",
                    "agent_config": {}
                }
            ],
            "user": {"user_name": "testuser"}
        }

    def test_team_agent_initialization(self, team_task_data):
        """Test team agent initialization"""
        agent = ClaudeCodeTeamAgent(team_task_data)

        assert agent._is_team_mode is True
        assert agent.team_builder is not None
        assert agent.mode == "coordinate"

    def test_single_agent_mode(self, single_bot_task_data):
        """Test agent falls back to single mode"""
        agent = ClaudeCodeTeamAgent(single_bot_task_data)

        assert agent._is_team_mode is False
        assert agent.team_builder is None

    def test_get_name_team_mode(self, team_task_data):
        """Test agent name in team mode"""
        agent = ClaudeCodeTeamAgent(team_task_data)

        assert agent.get_name() == "ClaudeCodeTeam"

    def test_get_name_single_mode(self, single_bot_task_data):
        """Test agent name in single mode"""
        agent = ClaudeCodeTeamAgent(single_bot_task_data)

        assert agent.get_name() == "ClaudeCode"

    def test_detect_team_mode_coordinate(self, team_task_data):
        """Test team mode detection for coordinate"""
        agent = ClaudeCodeTeamAgent(team_task_data)

        assert agent._detect_team_mode(team_task_data) is True

    def test_detect_team_mode_collaborate(self, team_task_data):
        """Test team mode detection for collaborate"""
        team_task_data["mode"] = "collaborate"
        agent = ClaudeCodeTeamAgent(team_task_data)

        assert agent._detect_team_mode(team_task_data) is True
