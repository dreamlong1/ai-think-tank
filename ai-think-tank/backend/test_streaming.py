import asyncio
import json
import unittest
from unittest.mock import patch

from main import event_generator
from services.structured_llm import (
    ModelTimeoutError,
    ProviderInvocationError,
    StructuredOutputError,
)


async def collect_events(question: str):
    events = []
    async for event in event_generator(question):
        events.append(event)
    return events


async def raise_timeout(*args, **kwargs):
    if False:
        yield {}
    raise ModelTimeoutError("mock timeout")


async def raise_structured_error(*args, **kwargs):
    if False:
        yield {}
    raise StructuredOutputError("mock schema failure")


async def raise_provider_error(*args, **kwargs):
    if False:
        yield {}
    raise ProviderInvocationError("mock provider failure")


class StreamingErrorHandlingTests(unittest.TestCase):
    def test_streaming_returns_timeout_error_event(self):
        # 用 mock 异常替代真实模型调用，验证 SSE 错误事件是否能正常落到前端。
        with patch("main.graph_app.astream", side_effect=raise_timeout):
            events = asyncio.run(collect_events("测试问题"))

        self.assertEqual(events[0]["event"], "system_notice")
        self.assertEqual(events[1]["event"], "analysis_error")
        self.assertEqual(json.loads(events[1]["data"])["code"], "model_timeout")
        self.assertEqual(events[-1]["event"], "done")

    def test_streaming_returns_structured_output_error_event(self):
        # 结构化输出失败时，应映射为 analysis_error，而不是直接抛出到客户端。
        with patch("main.graph_app.astream", side_effect=raise_structured_error):
            events = asyncio.run(collect_events("测试问题"))

        self.assertEqual(events[1]["event"], "analysis_error")
        self.assertEqual(
            json.loads(events[1]["data"])["code"],
            "structured_output_error",
        )
        self.assertEqual(events[-1]["event"], "done")

    def test_streaming_returns_provider_error_event(self):
        # provider 调用失败也要收敛成可读的 SSE 错误提示。
        with patch("main.graph_app.astream", side_effect=raise_provider_error):
            events = asyncio.run(collect_events("测试问题"))

        self.assertEqual(events[1]["event"], "analysis_error")
        self.assertEqual(
            json.loads(events[1]["data"])["code"],
            "provider_invocation_error",
        )
        self.assertEqual(events[-1]["event"], "done")


if __name__ == "__main__":
    unittest.main()
