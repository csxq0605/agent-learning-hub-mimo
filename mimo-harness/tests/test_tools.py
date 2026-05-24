"""Tests for individual tools (Ch3 patterns)."""

import pytest
import json
import os
import tempfile
from mimo_harness.tools import file_ops, shell, code_exec, math_tools, web_tools


class TestFileOps:
    def test_read_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(file_ops, "_ALLOWED_WRITE_DIR", tmp_path)
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3\n")
        result = json.loads(file_ops.read_file({"path": str(f)}))
        assert result["total_lines"] == 3
        assert "line1" in result["content"]

    def test_read_file_with_offset(self, tmp_path, monkeypatch):
        monkeypatch.setattr(file_ops, "_ALLOWED_WRITE_DIR", tmp_path)
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3\n")
        result = json.loads(file_ops.read_file({"path": str(f), "offset": 1, "limit": 2}))
        assert "line2" in result["content"]
        assert "line1" not in result["content"]

    def test_read_nonexistent(self):
        result = json.loads(file_ops.read_file({"path": "/nonexistent/file.txt"}))
        assert "error" in result

    def test_write_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(file_ops, "_ALLOWED_WRITE_DIR", tmp_path)
        f = tmp_path / "output.txt"
        result = json.loads(file_ops.write_file({
            "path": str(f),
            "content": "hello world",
        }))
        assert result["status"] == "written"
        assert f.read_text() == "hello world"

    def test_write_file_path_validation(self):
        result = json.loads(file_ops.write_file({
            "path": "/etc/passwd",
            "content": "hack",
        }))
        assert "error" in result
        assert "outside" in result["error"]

    def test_edit_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(file_ops, "_ALLOWED_WRITE_DIR", tmp_path)
        f = tmp_path / "edit.txt"
        f.write_text("hello world")
        result = json.loads(file_ops.edit_file({
            "path": str(f),
            "old_text": "world",
            "new_text": "python",
        }))
        assert result["status"] == "edited"
        assert f.read_text() == "hello python"

    def test_edit_file_not_found_text(self, tmp_path, monkeypatch):
        monkeypatch.setattr(file_ops, "_ALLOWED_WRITE_DIR", tmp_path)
        f = tmp_path / "edit.txt"
        f.write_text("hello world")
        result = json.loads(file_ops.edit_file({
            "path": str(f),
            "old_text": "nonexistent",
            "new_text": "replacement",
        }))
        assert "error" in result

    def test_glob_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(file_ops, "_ALLOWED_WRITE_DIR", tmp_path)
        (tmp_path / "a.py").touch()
        (tmp_path / "b.py").touch()
        (tmp_path / "c.txt").touch()
        result = json.loads(file_ops.glob_files({
            "pattern": str(tmp_path / "*.py"),
        }))
        assert result["total"] == 2

    def test_grep_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(file_ops, "_ALLOWED_WRITE_DIR", tmp_path)
        f = tmp_path / "search.txt"
        f.write_text("hello world\nfoo bar\nhello again\n")
        result = json.loads(file_ops.grep_files({
            "pattern": "hello",
            "path": str(tmp_path),
        }))
        assert result["total"] == 2


class TestShell:
    def test_is_readonly(self):
        assert shell._is_readonly("ls -la")
        assert shell._is_readonly("git status")
        assert shell._is_readonly("cat file.txt")
        assert not shell._is_readonly("rm -rf /")
        assert not shell._is_readonly("npm install")

    def test_chaining_detection(self):
        assert not shell._is_readonly("ls; rm -rf /")
        assert not shell._is_readonly("cat file | grep pattern")
        assert not shell._is_readonly("echo `whoami`")
        assert not shell._is_readonly("echo $(whoami)")

    def test_run_command(self):
        result = json.loads(shell.run_command({"command": "echo hello"}))
        assert result["exit_code"] == 0
        assert "hello" in result["output"]


class TestCodeExec:
    def test_execute_python(self):
        result = json.loads(code_exec.execute_python({
            "code": "print(2 + 2)",
        }))
        assert result["exit_code"] == 0
        assert "4" in result["output"]

    def test_execute_python_error(self):
        result = json.loads(code_exec.execute_python({
            "code": "1/0",
        }))
        assert result["exit_code"] != 0
        assert "ZeroDivisionError" in result["output"]


class TestMathTools:
    def test_basic_math(self):
        result = json.loads(math_tools.calculator({"expression": "2 + 3 * 4"}))
        assert result["result"] == 14

    def test_functions(self):
        result = json.loads(math_tools.calculator({"expression": "sqrt(144)"}))
        assert result["result"] == 12.0

    def test_unsafe_eval_blocked(self):
        result = json.loads(math_tools.calculator({"expression": "__import__('os').system('ls')"}))
        assert "error" in result

    def test_trig(self):
        import math
        result = json.loads(math_tools.calculator({"expression": "sin(pi/2)"}))
        assert abs(result["result"] - 1.0) < 0.0001


class TestWebTools:
    def test_validate_url_safe(self):
        assert web_tools._validate_url("https://example.com") is None
        assert web_tools._validate_url("http://example.com") is None

    def test_validate_url_blocks_private(self):
        assert web_tools._validate_url("http://127.0.0.1") is not None
        assert web_tools._validate_url("http://localhost") is not None
        assert web_tools._validate_url("http://10.0.0.1") is not None

    def test_validate_url_blocks_non_http(self):
        assert web_tools._validate_url("ftp://example.com") is not None
        assert web_tools._validate_url("file:///etc/passwd") is not None
