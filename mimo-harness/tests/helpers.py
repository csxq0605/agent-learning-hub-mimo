"""Shared test helpers for MiMo Harness tests."""

import json


class MockCompletions:
    """Track calls and return canned responses for testing."""
    def __init__(self, response_text):
        self.response_text = response_text
        self.call_count = 0
        self.last_messages = None

    def create(self, **kwargs):
        self.call_count += 1
        self.last_messages = kwargs.get("messages", [])
        msg = type("Msg", (), {"content": self.response_text})()
        choice = type("Choice", (), {"message": msg, "finish_reason": "stop"})()
        return type("Resp", (), {"choices": [choice]})()


class MockClient:
    """Mock OpenAI client for testing model-driven features."""
    def __init__(self, response_text):
        self.chat = type("Chat", (), {"completions": MockCompletions(response_text)})()
