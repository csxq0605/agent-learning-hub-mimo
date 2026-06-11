"""Custom Agents system - reusable agent definitions and invocation.

Implements Claude Code-style custom agents:
- Agent definition files with YAML frontmatter
- Agent discovery from multiple directories
- /agents command for management
- Agent invocation with custom system prompts and tool restrictions
"""

import os
import re
import yaml
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from pathlib import Path


@dataclass
class AgentConfig:
    """Agent configuration from frontmatter."""
    name: str
    description: str
    prompt: str = ""
    tools: List[str] = field(default_factory=list)
    disallowed_tools: List[str] = field(default_factory=list)
    model: str = "inherit"
    permission_mode: str = "default"
    max_turns: int = 0
    memory: str = "none"
    background: bool = False
    color: str = "blue"
    effort: Optional[str] = None


@dataclass
class Agent:
    """Represents a loaded agent."""
    name: str
    config: AgentConfig
    source_path: str
    source_type: str  # 'user', 'project'


class AgentParser:
    """Parse agent definition files with YAML frontmatter."""

    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n?(.*)$',
        re.DOTALL
    )

    @classmethod
    def parse(cls, content: str, source_path: str = '') -> tuple[AgentConfig, str]:
        """Parse agent definition content into config and prompt."""
        match = cls.FRONTMATTER_PATTERN.match(content.strip())
        if match:
            yaml_content = match.group(1)
            prompt = match.group(2).strip()
            try:
                frontmatter_data = yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError:
                frontmatter_data = {}
        else:
            frontmatter_data = {}
            prompt = content.strip()

        # Parse frontmatter
        config = AgentConfig(
            name=frontmatter_data.get('name', Path(source_path).stem if source_path else 'unnamed'),
            description=frontmatter_data.get('description', ''),
            prompt=prompt,
            tools=cls._parse_tools(frontmatter_data.get('tools', [])),
            disallowed_tools=cls._parse_tools(frontmatter_data.get('disallowedTools', [])),
            model=frontmatter_data.get('model', 'inherit'),
            permission_mode=frontmatter_data.get('permissionMode', 'default'),
            max_turns=frontmatter_data.get('maxTurns', 0),
            memory=frontmatter_data.get('memory', 'none'),
            background=frontmatter_data.get('background', False),
            color=frontmatter_data.get('color', 'blue'),
            effort=frontmatter_data.get('effort'),
        )

        return config, prompt

    @classmethod
    def _parse_tools(cls, tools) -> List[str]:
        """Parse tools field (string or list)."""
        if isinstance(tools, str):
            return [t.strip() for t in tools.replace(',', ' ').split()]
        elif isinstance(tools, list):
            return [str(t) for t in tools]
        return []


class AgentDiscovery:
    """Discover agents from multiple directories."""

    @classmethod
    def discover_agents(cls, project_root: str = '.') -> Dict[str, Agent]:
        """Discover all available agents."""
        agents = {}

        # Project-level agents
        project_agents_dir = os.path.join(project_root, '.mimo', 'agents')
        if os.path.exists(project_agents_dir):
            for agent in cls._scan_directory(project_agents_dir, 'project'):
                agents[agent.name] = agent

        # User-level agents
        user_agents_dir = os.path.join(os.path.expanduser('~'), '.mimo', 'agents')
        if os.path.exists(user_agents_dir):
            for agent in cls._scan_directory(user_agents_dir, 'user'):
                if agent.name not in agents:
                    agents[agent.name] = agent

        return agents

    @classmethod
    def _scan_directory(cls, directory: str, source_type: str) -> List[Agent]:
        """Scan a directory for agent definitions."""
        agents = []
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.md'):
                    filepath = os.path.join(root, filename)
                    try:
                        agent = cls._load_agent(filepath, source_type)
                        if agent:
                            agents.append(agent)
                    except Exception as e:
                        print(f"Warning: Failed to load agent from {filepath}: {e}")
        return agents

    @classmethod
    def _load_agent(cls, filepath: str, source_type: str) -> Optional[Agent]:
        """Load an agent from a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            config, prompt = AgentParser.parse(content, filepath)
            return Agent(
                name=config.name,
                config=config,
                source_path=filepath,
                source_type=source_type,
            )
        except Exception:
            return None


class AgentManager:
    """Manage and invoke custom agents."""

    def __init__(self, project_root: str = '.'):
        self.project_root = project_root
        self.agents: Dict[str, Agent] = {}
        self._refresh_agents()

    def _refresh_agents(self):
        """Refresh agent discovery."""
        self.agents = AgentDiscovery.discover_agents(self.project_root)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents."""
        return [
            {
                'name': agent.name,
                'description': agent.config.description,
                'source': agent.source_type,
                'model': agent.config.model,
                'tools': agent.config.tools,
            }
            for agent in self.agents.values()
        ]

    def get_agent(self, name: str) -> Optional[Agent]:
        """Get an agent by name."""
        return self.agents.get(name)

    def create_agent(self, name: str, description: str, prompt: str,
                     tools: List[str] = None, model: str = "inherit",
                     scope: str = "user") -> str:
        """Create a new agent definition file."""
        # Determine directory
        if scope == "project":
            agents_dir = os.path.join(self.project_root, '.mimo', 'agents')
        else:
            agents_dir = os.path.join(os.path.expanduser('~'), '.mimo', 'agents')

        os.makedirs(agents_dir, exist_ok=True)

        # Build frontmatter
        frontmatter = {
            'name': name,
            'description': description,
        }
        if tools:
            frontmatter['tools'] = tools
        if model != "inherit":
            frontmatter['model'] = model

        # Build content
        yaml_content = yaml.dump(frontmatter, default_flow_style=False)
        content = f"---\n{yaml_content}---\n\n{prompt}"

        # Write file
        filepath = os.path.join(agents_dir, f"{name}.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        # Refresh agents
        self._refresh_agents()

        return filepath

    def delete_agent(self, name: str) -> bool:
        """Delete an agent definition file."""
        agent = self.get_agent(name)
        if not agent:
            return False

        try:
            os.remove(agent.source_path)
            self._refresh_agents()
            return True
        except Exception:
            return False
