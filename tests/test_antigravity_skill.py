"""Unit tests for Antigravity skill and subagent definitions."""

from pathlib import Path


def test_scenografia_skill_definition_exists_and_valid():
    """Verify the Scenografia Antigravity skill markdown file is properly structured."""
    skill_file = Path(".agent/skills/scenografia/SKILL.md")
    assert skill_file.exists(), "SKILL.md must exist in .agent/skills/scenografia/"
    content = skill_file.read_text(encoding="utf-8")
    
    assert content.startswith("---")
    assert "name: scenografia" in content
    assert "description:" in content
    assert "landscape" in content
    assert "portrait" in content
    assert "square" in content
    assert "PromptEnhancerAgent" in content
    assert "StyleComplianceAgent" in content


def test_scenografia_subagent_definition_exists_and_valid():
    """Verify the Scenografia Designer subagent definition file is properly structured."""
    agent_file = Path(".agent/agents/scenografia-designer.md")
    assert agent_file.exists(), "Subagent definition must exist in .agent/agents/"
    content = agent_file.read_text(encoding="utf-8")
    
    assert content.startswith("---")
    assert "name: scenografia-designer" in content
    assert "theatrical scenic designer" in content.lower()
