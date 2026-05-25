"""Tests for task tools - CRUD operations, thread safety, status transitions."""

import json
import threading
import pytest
from mimo_harness.tools.task_tools import (
    Task, TaskStore, task_create, task_get, task_list,
    task_update, task_delete, get_tools, _task_store,
)


class TestTaskDataclass:
    """Test Task dataclass defaults."""

    def test_task_defaults(self):
        t = Task(id="1", subject="test")
        assert t.id == "1"
        assert t.subject == "test"
        assert t.description == ""
        assert t.status == "pending"
        assert t.active_form == ""
        assert t.owner == ""
        assert t.created_at > 0
        assert t.metadata == {}
        assert t.blocks == []
        assert t.blocked_by == []

    def test_task_custom_values(self):
        t = Task(
            id="42",
            subject="Fix bug",
            description="A critical bug",
            status="in_progress",
            active_form="Fixing the bug",
            owner="alice",
            metadata={"priority": "high"},
        )
        assert t.id == "42"
        assert t.status == "in_progress"
        assert t.owner == "alice"
        assert t.metadata["priority"] == "high"


class TestTaskStore:
    """Test TaskStore CRUD operations."""

    def _fresh_store(self):
        """Create a fresh TaskStore for isolated tests."""
        return TaskStore()

    def test_create_task(self):
        store = self._fresh_store()
        task = store.create(subject="Test task", description="A test")
        assert task.id == "1"
        assert task.subject == "Test task"
        assert task.description == "A test"
        assert task.status == "pending"

    def test_create_multiple_tasks_increment_ids(self):
        store = self._fresh_store()
        t1 = store.create(subject="First")
        t2 = store.create(subject="Second")
        t3 = store.create(subject="Third")
        assert t1.id == "1"
        assert t2.id == "2"
        assert t3.id == "3"

    def test_get_existing_task(self):
        store = self._fresh_store()
        created = store.create(subject="Find me")
        found = store.get("1")
        assert found is created
        assert found.subject == "Find me"

    def test_get_nonexistent_task(self):
        store = self._fresh_store()
        assert store.get("999") is None

    def test_list_all_excludes_deleted(self):
        store = self._fresh_store()
        store.create(subject="Active")
        store.create(subject="Also active")
        store.create(subject="To be deleted")
        store.delete("3")

        tasks = store.list_all()
        assert len(tasks) == 2
        subjects = [t.subject for t in tasks]
        assert "Active" in subjects
        assert "Also active" in subjects
        assert "To be deleted" not in subjects

    def test_list_all_empty(self):
        store = self._fresh_store()
        assert store.list_all() == []

    def test_update_task(self):
        store = self._fresh_store()
        store.create(subject="Original")
        updated = store.update("1", subject="Updated", status="in_progress")
        assert updated is not None
        assert updated.subject == "Updated"
        assert updated.status == "in_progress"

    def test_update_nonexistent_task(self):
        store = self._fresh_store()
        result = store.update("999", subject="nope")
        assert result is None

    def test_update_ignores_unknown_attributes(self):
        store = self._fresh_store()
        store.create(subject="Test")
        updated = store.update("1", unknown_field="value")
        assert updated is not None
        assert not hasattr(updated, "unknown_field") or updated.unknown_field != "value"

    def test_delete_task(self):
        store = self._fresh_store()
        store.create(subject="Doomed")
        assert store.delete("1") is True
        # Task still exists in store but with deleted status
        task = store.get("1")
        assert task.status == "deleted"

    def test_delete_nonexistent_task(self):
        store = self._fresh_store()
        assert store.delete("999") is False


class TestTaskStoreThreadSafety:
    """Test thread safety of TaskStore."""

    def test_concurrent_creates(self):
        """Multiple threads creating tasks should not lose any."""
        store = TaskStore()
        n_threads = 10
        tasks_per_thread = 20
        created_ids = []
        lock = threading.Lock()

        def create_tasks(thread_idx):
            for i in range(tasks_per_thread):
                task = store.create(subject=f"Thread {thread_idx} Task {i}")
                with lock:
                    created_ids.append(task.id)

        threads = [threading.Thread(target=create_tasks, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All tasks should be created with unique IDs
        assert len(created_ids) == n_threads * tasks_per_thread
        assert len(set(created_ids)) == n_threads * tasks_per_thread
        assert len(store.list_all()) == n_threads * tasks_per_thread

    def test_concurrent_read_write(self):
        """Reading and writing concurrently should not raise."""
        store = TaskStore()
        # Pre-create some tasks
        for i in range(10):
            store.create(subject=f"Task {i}")

        errors = []

        def reader():
            try:
                for _ in range(50):
                    store.list_all()
                    store.get("1")
            except Exception as e:
                errors.append(e)

        def writer():
            try:
                for i in range(50):
                    store.create(subject=f"New task {i}")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=reader),
            threading.Thread(target=reader),
            threading.Thread(target=writer),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []


class TestTaskStatusTransitions:
    """Test task status transitions."""

    def test_pending_to_in_progress(self):
        store = TaskStore()
        store.create(subject="Work item")
        updated = store.update("1", status="in_progress")
        assert updated.status == "in_progress"

    def test_in_progress_to_completed(self):
        store = TaskStore()
        store.create(subject="Work item")
        store.update("1", status="in_progress")
        updated = store.update("1", status="completed")
        assert updated.status == "completed"

    def test_pending_to_deleted(self):
        store = TaskStore()
        store.create(subject="Unwanted")
        store.delete("1")
        task = store.get("1")
        assert task.status == "deleted"

    def test_completed_to_deleted(self):
        store = TaskStore()
        store.create(subject="Done item")
        store.update("1", status="completed")
        store.delete("1")
        task = store.get("1")
        assert task.status == "deleted"


class TestTaskToolFunctions:
    """Test the tool handler functions (task_create, task_get, etc.)."""

    def _reset_store(self):
        """Reset the global task store for test isolation."""
        _task_store._tasks.clear()
        _task_store._next_id = 1

    def setup_method(self):
        self._reset_store()

    def teardown_method(self):
        self._reset_store()

    def test_task_create(self):
        result = json.loads(task_create({"subject": "New task", "description": "Details"}))
        assert "id" in result
        assert result["subject"] == "New task"
        assert result["status"] == "pending"

    def test_task_create_with_active_form(self):
        result = json.loads(task_create({
            "subject": "Build feature",
            "activeForm": "Building the feature",
        }))
        assert result["subject"] == "Build feature"

    def test_task_get_existing(self):
        created = json.loads(task_create({"subject": "Get me"}))
        result = json.loads(task_get({"taskId": created["id"]}))
        assert result["subject"] == "Get me"
        assert result["status"] == "pending"
        assert "description" in result
        assert "blocks" in result
        assert "blockedBy" in result

    def test_task_get_nonexistent(self):
        result = json.loads(task_get({"taskId": "999"}))
        assert "error" in result

    def test_task_list_empty(self):
        result = json.loads(task_list({}))
        assert result == []

    def test_task_list_with_tasks(self):
        task_create({"subject": "Task A"})
        task_create({"subject": "Task B"})
        result = json.loads(task_list({}))
        assert len(result) == 2
        subjects = [t["subject"] for t in result]
        assert "Task A" in subjects
        assert "Task B" in subjects

    def test_task_list_excludes_deleted(self):
        t1 = json.loads(task_create({"subject": "Keep"}))
        t2 = json.loads(task_create({"subject": "Remove"}))
        task_delete({"taskId": t2["id"]})
        result = json.loads(task_list({}))
        assert len(result) == 1
        assert result[0]["subject"] == "Keep"

    def test_task_update_status(self):
        created = json.loads(task_create({"subject": "Update me"}))
        result = json.loads(task_update({
            "taskId": created["id"],
            "status": "completed",
        }))
        assert result["status"] == "completed"

    def test_task_update_subject(self):
        created = json.loads(task_create({"subject": "Old subject"}))
        result = json.loads(task_update({
            "taskId": created["id"],
            "subject": "New subject",
        }))
        assert result["id"] == created["id"]
        # Verify via get
        get_result = json.loads(task_get({"taskId": created["id"]}))
        assert get_result["subject"] == "New subject"

    def test_task_update_nonexistent(self):
        result = json.loads(task_update({"taskId": "999", "status": "completed"}))
        assert "error" in result

    def test_task_delete_existing(self):
        created = json.loads(task_create({"subject": "Delete me"}))
        result = json.loads(task_delete({"taskId": created["id"]}))
        assert result["status"] == "deleted"

    def test_task_delete_nonexistent(self):
        result = json.loads(task_delete({"taskId": "999"}))
        assert "error" in result


class TestTaskToolsGetTools:
    """Test get_tools() returns proper ToolDefs."""

    def test_returns_five_tools(self):
        tools = get_tools()
        assert len(tools) == 5

    def test_tool_names(self):
        tools = get_tools()
        names = [t.name for t in tools]
        assert "task_create" in names
        assert "task_get" in names
        assert "task_list" in names
        assert "task_update" in names
        assert "task_delete" in names

    def test_all_handlers_assigned(self):
        tools = get_tools()
        for tool in tools:
            assert tool.handler is not None
            assert callable(tool.handler)

    def test_task_get_is_concurrency_safe(self):
        tools = get_tools()
        task_get_tool = next(t for t in tools if t.name == "task_get")
        assert task_get_tool.is_concurrency_safe is True

    def test_task_list_is_concurrency_safe(self):
        tools = get_tools()
        task_list_tool = next(t for t in tools if t.name == "task_list")
        assert task_list_tool.is_concurrency_safe is True
