"""Tests for the permission pipeline (Ch4 patterns)."""

import pytest
import json
import tempfile
import os
from mimo_harness.permissions import (
    Permission, PermissionMode, PermissionRule, PermissionGate,
)


class TestPermissionRule:
    def test_exact_match(self):
        rule = PermissionRule(tool_pattern="read_file", action="allow")
        assert rule.matches("read_file")
        assert not rule.matches("write_file")

    def test_wildcard_match(self):
        rule = PermissionRule(tool_pattern="*", action="allow")
        assert rule.matches("anything")
        assert rule.matches("read_file")

    def test_prefix_match(self):
        rule = PermissionRule(tool_pattern="run_command:npm:*", action="allow")
        assert rule.matches("run_command", "npm test")
        assert rule.matches("run_command", "npm install")
        assert not rule.matches("run_command", "git status")

    def test_context_exact_match(self):
        rule = PermissionRule(tool_pattern="run_command:git status", action="allow")
        assert rule.matches("run_command", "git status")
        assert not rule.matches("run_command", "git log")

    def test_path_scoped_rule_match(self):
        rule = PermissionRule(
            tool_pattern="edit_file",
            action="allow",
            path_pattern="/src/**",
        )
        assert rule.matches("edit_file", "/src/foo.py")
        assert rule.matches("edit_file", "/src/sub/module.py")

    def test_path_scoped_rule_no_match(self):
        rule = PermissionRule(
            tool_pattern="edit_file",
            action="allow",
            path_pattern="/src/**",
        )
        assert not rule.matches("edit_file", "/other/foo.py")
        assert not rule.matches("edit_file", "/etc/passwd")

    def test_path_scoped_with_tilde(self):
        home = os.path.expanduser("~")
        rule = PermissionRule(
            tool_pattern="read_file",
            action="allow",
            path_pattern="~/Documents/**",
        )
        assert rule.matches("read_file", f"{home}/Documents/test.txt")
        assert not rule.matches("read_file", "/other/path.txt")

    def test_path_scoped_gate_integration(self):
        """Path-scoped rules integrate with PermissionGate."""
        gate = PermissionGate(auto_approve=True, rules=[
            PermissionRule("write_file", "allow", path_pattern="/src/**"),
        ])
        # write_file to /src/ should be allowed
        assert gate.check(Permission.WRITE, "write_file(/src/main.py)")
        # write_file outside /src/ falls through to auto-approve
        assert gate.check(Permission.WRITE, "write_file(/tmp/other.py)")


class TestPermissionGate:
    def test_read_always_approved(self):
        gate = PermissionGate()
        assert gate.check(Permission.READ, "read_file(path)")

    def test_write_needs_confirmation_default(self, monkeypatch):
        gate = PermissionGate()
        monkeypatch.setattr("builtins.input", lambda _: "y")
        assert gate.check(Permission.WRITE, "write_file(path)")

    def test_write_denied_by_user(self, monkeypatch):
        gate = PermissionGate()
        monkeypatch.setattr("builtins.input", lambda _: "n")
        assert not gate.check(Permission.WRITE, "write_file(path)")

    def test_auto_approve(self):
        gate = PermissionGate(auto_approve=True)
        assert gate.check(Permission.WRITE, "write_file(path)")

    def test_dry_run_blocks(self):
        gate = PermissionGate(dry_run=True)
        assert not gate.check(Permission.WRITE, "write_file(path)")

    def test_plan_mode_blocks_writes(self):
        gate = PermissionGate(plan_mode=True)
        assert not gate.check(Permission.WRITE, "write_file(path)")
        assert gate.check(Permission.READ, "read_file(path)")

    def test_deny_rule_takes_precedence(self):
        gate = PermissionGate(auto_approve=True)
        gate.rules.append(PermissionRule(
            tool_pattern="write_file", action="deny"
        ))
        assert not gate.check(Permission.WRITE, "write_file(path)")

    def test_allow_rule(self):
        gate = PermissionGate()
        gate.rules.append(PermissionRule(
            tool_pattern="read_file", action="allow"
        ))
        assert gate.check(Permission.READ, "read_file(path)")

    def test_deny_over_allow(self):
        gate = PermissionGate()
        gate.rules.append(PermissionRule(tool_pattern="run_command", action="allow"))
        gate.rules.append(PermissionRule(tool_pattern="run_command", action="deny"))
        assert not gate.check(Permission.WRITE, "run_command(rm -rf /)")

    def test_approval_log(self, monkeypatch):
        gate = PermissionGate(auto_approve=True)
        gate.check(Permission.WRITE, "write_file(path)")
        log = gate.summary()
        assert len(log) == 1
        assert log[0]["result"] == "auto_approved"

    def test_load_rules_from_file(self):
        rules_content = {
            "permissions": {
                "allow": ["read_file", "glob_files"],
                "deny": ["run_command:rm *"],
                "ask": ["write_file"]
            }
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(rules_content, f)
            path = f.name

        try:
            gate = PermissionGate()
            gate.load_rules_from_file(path)
            assert len(gate.rules) == 4
            assert gate.rules[0].action == "allow"
            assert gate.rules[2].action == "deny"
        finally:
            os.unlink(path)

    def test_plan_mode_allows_read(self):
        gate = PermissionGate(plan_mode=True)
        assert gate.check(Permission.READ, "read_file(/etc/passwd)")

    def test_plan_mode_blocks_destructive(self):
        gate = PermissionGate(plan_mode=True)
        assert not gate.check(Permission.DESTRUCTIVE, "run_command(rm -rf /)")


class TestPermissionMode:
    def test_modes(self):
        assert PermissionMode.DEFAULT.value == "default"
        assert PermissionMode.PLAN.value == "plan"
        assert PermissionMode.AUTO.value == "auto"
        assert PermissionMode.ACCEPT_EDITS.value == "accept_edits"
        assert PermissionMode.DONT_ASK.value == "dont_ask"
        assert PermissionMode.BYPASS.value == "bypass"


# ============================================================================
# S4: Protected path checks
# ============================================================================

class TestProtectedPaths:
    """S4: Protected directories and files cannot be written to."""

    def test_blocks_git_dir(self):
        """S4: Write to .git/ is blocked."""
        gate = PermissionGate(auto_approve=True)
        assert not gate.check(Permission.WRITE, "write_file(path=.git/config)")

    def test_blocks_git_head(self):
        """S4: Write to .git/HEAD is blocked."""
        gate = PermissionGate(auto_approve=True)
        assert not gate.check(Permission.WRITE, "write_file(path=.git/HEAD)")

    def test_blocks_env_file(self):
        """S4: Write to .env is blocked."""
        gate = PermissionGate(auto_approve=True)
        assert not gate.check(Permission.WRITE, "write_file(path=.env)")

    def test_blocks_bashrc(self):
        """S4: Write to .bashrc is blocked."""
        gate = PermissionGate(auto_approve=True)
        assert not gate.check(Permission.WRITE, "write_file(path=.bashrc)")

    def test_blocks_zshrc(self):
        """S4: Write to .zshrc is blocked."""
        gate = PermissionGate(auto_approve=True)
        assert not gate.check(Permission.WRITE, "write_file(path=.zshrc)")

    def test_blocks_profile(self):
        """S4: Write to .profile is blocked."""
        gate = PermissionGate(auto_approve=True)
        assert not gate.check(Permission.WRITE, "write_file(path=.profile)")

    def test_allows_normal_file(self):
        """S4: Write to a normal file is allowed."""
        gate = PermissionGate(auto_approve=True)
        assert gate.check(Permission.WRITE, "write_file(path=src/main.py)")

    def test_blocks_nested_git_dir(self):
        """S4: Write to nested .git/ path is blocked."""
        gate = PermissionGate(auto_approve=True)
        assert not gate.check(Permission.WRITE, "write_file(path=project/.git/config)")

    def test_read_not_blocked_by_protected_path(self):
        """S4: Read operations are not affected by protected path checks."""
        gate = PermissionGate()
        assert gate.check(Permission.READ, "read_file(path=.env)")
        assert gate.check(Permission.READ, "read_file(path=.git/config)")


# ============================================================================
# S7: ACCEPT_EDITS permission mode
# ============================================================================

class TestAcceptEditsMode:
    """S7: ACCEPT_EDITS mode auto-approves file writes but asks for shell."""

    def test_accept_edits_approves_file_write(self):
        """S7: ACCEPT_EDITS mode auto-approves write_file."""
        gate = PermissionGate()
        gate.mode = PermissionMode.ACCEPT_EDITS
        assert gate.check(Permission.WRITE, "write_file(path=output.txt)")

    def test_accept_edits_approves_edit_file(self):
        """S7: ACCEPT_EDITS mode auto-approves edit_file."""
        gate = PermissionGate()
        gate.mode = PermissionMode.ACCEPT_EDITS
        assert gate.check(Permission.WRITE, "edit_file(path=output.txt)")

    def test_accept_edits_approves_read(self):
        """S7: ACCEPT_EDITS mode auto-approves read operations."""
        gate = PermissionGate()
        gate.mode = PermissionMode.ACCEPT_EDITS
        assert gate.check(Permission.READ, "read_file(path=output.txt)")

    def test_accept_edits_asks_for_shell(self, monkeypatch):
        """S7: ACCEPT_EDITS mode falls through to interactive for shell commands."""
        gate = PermissionGate()
        gate.mode = PermissionMode.ACCEPT_EDITS
        monkeypatch.setattr("builtins.input", lambda _: "y")
        # run_command is NOT in _FILE_TOOLS, so it should fall through
        assert gate.check(Permission.WRITE, "run_command(npm install)")

    def test_accept_edits_denies_shell_if_user_says_no(self, monkeypatch):
        """S7: ACCEPT_EDITS mode denies shell if user says no."""
        gate = PermissionGate()
        gate.mode = PermissionMode.ACCEPT_EDITS
        monkeypatch.setattr("builtins.input", lambda _: "n")
        assert not gate.check(Permission.WRITE, "run_command(rm -rf /)")


# ============================================================================
# S7: DONT_ASK permission mode
# ============================================================================

class TestDontAskMode:
    """S7: DONT_ASK mode denies tools not in allow rules."""

    def test_dont_ask_allows_rule_match(self):
        """S7: DONT_ASK mode allows tools matching allow rules."""
        gate = PermissionGate(rules=[
            PermissionRule("read_file", "allow"),
        ])
        gate.mode = PermissionMode.DONT_ASK
        assert gate.check(Permission.READ, "read_file(path=test.txt)")

    def test_dont_ask_denies_no_rule(self):
        """S7: DONT_ASK mode denies tools with no matching rules."""
        gate = PermissionGate(rules=[
            PermissionRule("read_file", "allow"),
        ])
        gate.mode = PermissionMode.DONT_ASK
        assert not gate.check(Permission.WRITE, "write_file(path=test.txt)")

    def test_dont_ask_deny_overrides_allow(self):
        """S7: DONT_ASK mode respects deny over allow."""
        gate = PermissionGate(rules=[
            PermissionRule("write_file", "allow"),
            PermissionRule("write_file", "deny"),
        ])
        gate.mode = PermissionMode.DONT_ASK
        assert not gate.check(Permission.WRITE, "write_file(path=test.txt)")

    def test_dont_ask_shell_deny_no_rules(self):
        """S7: DONT_ASK mode denies shell commands without allow rules."""
        gate = PermissionGate()
        gate.mode = PermissionMode.DONT_ASK
        assert not gate.check(Permission.WRITE, "run_command(npm install)")

    def test_dont_ask_shell_allowed_by_rule(self):
        """S7: DONT_ASK mode allows shell commands matching allow rules."""
        gate = PermissionGate(rules=[
            PermissionRule("run_command:*", "allow"),
        ])
        gate.mode = PermissionMode.DONT_ASK
        assert gate.check(Permission.WRITE, "run_command(npm install)")


# ============================================================================
# S7: BYPASS permission mode
# ============================================================================

class TestBypassMode:
    """S7: BYPASS mode approves everything except dangerous rm -rf."""

    def test_bypass_approves_write(self):
        """S7: BYPASS mode approves file writes."""
        gate = PermissionGate()
        gate.mode = PermissionMode.BYPASS
        assert gate.check(Permission.WRITE, "write_file(path=test.txt)")

    def test_bypass_approves_shell(self):
        """S7: BYPASS mode approves shell commands."""
        gate = PermissionGate()
        gate.mode = PermissionMode.BYPASS
        assert gate.check(Permission.WRITE, "run_command(npm install)")

    def test_bypass_approves_destructive(self):
        """S7: BYPASS mode approves destructive operations."""
        gate = PermissionGate()
        gate.mode = PermissionMode.BYPASS
        assert gate.check(Permission.DESTRUCTIVE, "run_command(rm file.txt)")

    def test_bypass_blocks_rm_rf_root(self):
        """S7: BYPASS mode blocks rm -rf /."""
        gate = PermissionGate()
        gate.mode = PermissionMode.BYPASS
        assert not gate.check(Permission.WRITE, "run_command(rm -rf /)")

    def test_bypass_blocks_rm_rf_tilde(self):
        """S7: BYPASS mode blocks rm -rf ~."""
        gate = PermissionGate()
        gate.mode = PermissionMode.BYPASS
        assert not gate.check(Permission.WRITE, "run_command(rm -rf ~)")

    def test_bypass_blocks_rm_rf_root_trailing_space(self):
        """S7: BYPASS mode blocks rm -rf / even with trailing space."""
        gate = PermissionGate()
        gate.mode = PermissionMode.BYPASS
        assert not gate.check(Permission.WRITE, "run_command(rm -rf / )")

    def test_bypass_allows_normal_rm(self):
        """S7: BYPASS mode allows rm on non-root paths."""
        gate = PermissionGate()
        gate.mode = PermissionMode.BYPASS
        assert gate.check(Permission.WRITE, "run_command(rm -rf tmp/test)")

    def test_bypass_still_blocks_protected_paths(self):
        """BYPASS mode still blocks writes to critical protected paths."""
        gate = PermissionGate()
        gate.mode = PermissionMode.BYPASS
        assert not gate.check(Permission.WRITE, "write_file(path=.env)")
        assert not gate.check(Permission.WRITE, "write_file(path=.git/config)")
