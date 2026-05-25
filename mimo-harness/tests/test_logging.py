"""Tests for structured logging (TraceLogger)."""

import io
import os
import re
import json
import logging
import pytest
from unittest.mock import patch, MagicMock
from mimo_harness.logging_utils import TraceLogger


@pytest.fixture(autouse=True)
def clean_logger():
    """Ensure the mimo-harness logger is clean before each test."""
    logger = logging.getLogger("mimo-harness")
    logger.handlers.clear()
    yield
    logger.handlers.clear()


class TestTraceLogger:
    def test_trace_logger_init(self):
        logger = TraceLogger()
        assert len(logger.session_id) == 8
        assert logger.step == 0

    def test_trace_logger_session_id_format(self):
        logger = TraceLogger()
        # 8 hex chars = 4 bytes = secrets.token_hex(4)
        assert re.match(r'^[0-9a-f]{8}$', logger.session_id)

    def test_trace_logger_info(self):
        logger = TraceLogger()
        with patch.object(logger.logger, 'info') as mock_info:
            logger.info("test info message")
            mock_info.assert_called_once_with("test info message")

    def test_trace_logger_error(self):
        logger = TraceLogger()
        with patch.object(logger.logger, 'error') as mock_error:
            exc = ValueError("test error")
            logger.error("something failed", exc=exc)
            mock_error.assert_called_once()
            call_args = mock_error.call_args
            assert "something failed" in call_args[0][0]
            assert call_args[1].get('exc_info') is exc

    def test_trace_logger_trace(self):
        logger = TraceLogger()
        with patch.object(logger.logger, 'debug') as mock_debug:
            logger.trace("test_event", {"key": "value"})
            mock_debug.assert_called_once()
            msg = mock_debug.call_args[0][0]
            assert "[TRACE]" in msg
            assert "test_event" in msg
            assert "key" in msg
        assert logger.step == 1

    def test_trace_logger_tool_call(self):
        logger = TraceLogger()
        with patch.object(logger.logger, 'debug') as mock_debug:
            logger.tool_call("read_file", {"path": "/tmp/test"}, result="hello world")
            mock_debug.assert_called_once()
            msg = mock_debug.call_args[0][0]
            assert "tool_call" in msg
            assert "read_file" in msg
            assert "11" in msg  # len("hello world") == 11

    def test_trace_logger_session_summary(self):
        logger = TraceLogger()
        with patch.object(logger.logger, 'debug') as mock_debug:
            logger.session_summary({"steps": 3, "duration": 1.5})
            mock_debug.assert_called_once()
            msg = mock_debug.call_args[0][0]
            assert "session_complete" in msg
            assert "steps" in msg

    def test_trace_logger_step_increment(self):
        logger = TraceLogger()
        assert logger.step == 0
        logger.trace("event1")
        assert logger.step == 1
        logger.trace("event2")
        assert logger.step == 2
        logger.trace("event3")
        assert logger.step == 3

    def test_trace_logger_with_log_file(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        logger = TraceLogger(log_file=log_file)
        # The file handler should be created
        file_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) >= 1
        # Write something and check the file
        logger.info("log to file")
        logger.trace("file_event")
        # Flush handlers
        for h in logger.logger.handlers:
            h.flush()
        assert os.path.exists(log_file)
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "log to file" in content
        assert "file_event" in content

    def test_trace_logger_verbose(self):
        logger = TraceLogger(verbose=True)
        for handler in logger.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                assert handler.level == logging.DEBUG
                break
        else:
            pytest.fail("No stream handler found")

    def test_trace_logger_non_verbose(self):
        logger = TraceLogger(verbose=False)
        for handler in logger.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                assert handler.level == logging.INFO
                break
        else:
            pytest.fail("No stream handler found")
