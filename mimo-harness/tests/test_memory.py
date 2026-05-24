"""Tests for the memory system (Ch6 patterns)."""

import pytest
import os
import tempfile
from mimo_harness.memory import (
    MemoryType, MemoryEntry, MemoryStore,
    MEMORY_INDEX_MAX_LINES, MEMORY_INDEX_MAX_BYTES,
)


class TestMemoryType:
    def test_four_types(self):
        assert MemoryType.USER.value == "user"
        assert MemoryType.FEEDBACK.value == "feedback"
        assert MemoryType.PROJECT.value == "project"
        assert MemoryType.REFERENCE.value == "reference"


class TestMemoryStore:
    def test_ensure_dir(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        store.ensure_dir()
        assert os.path.exists(store.memory_dir)

    def test_save_and_load(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        filepath = store.save_memory(
            name="test-memory",
            memory_type=MemoryType.USER,
            description="Test user memory",
            content="User is a senior Python developer",
        )
        assert os.path.exists(filepath)

        # Check frontmatter
        with open(filepath, "r") as f:
            content = f.read()
        assert "name: test-memory" in content
        assert "type: user" in content
        assert "User is a senior Python developer" in content

    def test_index_updated(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        store.save_memory(
            name="memory-1",
            memory_type=MemoryType.USER,
            description="First memory",
            content="Content 1",
        )
        store.save_memory(
            name="memory-2",
            memory_type=MemoryType.FEEDBACK,
            description="Second memory",
            content="Content 2",
        )

        index = store.load_index()
        assert "memory-1" in index
        assert "memory-2" in index

    def test_list_memories(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        store.save_memory(
            name="user-pref",
            memory_type=MemoryType.USER,
            description="User preferences",
            content="Prefers dark mode",
        )
        store.save_memory(
            name="project-state",
            memory_type=MemoryType.PROJECT,
            description="Project decision",
            content="Using event-driven architecture",
        )

        memories = store.list_memories()
        assert len(memories) == 2
        types = {m.memory_type for m in memories}
        assert MemoryType.USER in types
        assert MemoryType.PROJECT in types

    def test_delete_memory(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        store.save_memory(
            name="to-delete",
            memory_type=MemoryType.REFERENCE,
            description="Will be deleted",
            content="Temporary link",
        )
        assert store.delete_memory("to-delete")
        assert len(store.list_memories()) == 0

    def test_delete_nonexistent(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        assert not store.delete_memory("nonexistent")

    def test_validate_memory_stale_dates(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        entry = MemoryEntry(
            name="test",
            description="test",
            memory_type=MemoryType.PROJECT,
            content="Meeting next Thursday about the deadline",
        )
        warnings = store.validate_memory(entry)
        assert any("relative dates" in w.lower() for w in warnings)

    def test_validate_memory_missing_file_ref(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        entry = MemoryEntry(
            name="test",
            description="test",
            memory_type=MemoryType.PROJECT,
            content="The config is at file: /nonexistent/path/config.json",
        )
        warnings = store.validate_memory(entry)
        assert any("may not exist" in w.lower() for w in warnings)

    def test_validate_memory_ok(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        entry = MemoryEntry(
            name="test",
            description="test",
            memory_type=MemoryType.USER,
            content="User prefers TypeScript over JavaScript",
        )
        warnings = store.validate_memory(entry)
        assert len(warnings) == 0

    def test_path_security(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        # Path validation should reject paths outside memory dir
        err = store._validate_path("../../etc/passwd")
        assert err is not None

    def test_path_security_null_bytes(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        err = store._validate_path("foo\0.txt")
        assert err is not None

    def test_index_line_limit(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        # Create many memories to test line limit
        for i in range(250):
            store.save_memory(
                name=f"memory-{i:03d}",
                memory_type=MemoryType.PROJECT,
                description=f"Memory number {i}",
                content=f"Content {i}",
            )

        index = store.load_index()
        lines = index.strip().split("\n")
        # Should be capped at ~200 entries + header
        assert len(lines) <= MEMORY_INDEX_MAX_LINES + 3  # header + entries + truncation note

    def test_load_empty_index(self, tmp_path):
        store = MemoryStore(str(tmp_path))
        assert store.load_index() == ""
