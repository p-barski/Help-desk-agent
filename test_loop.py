import json

import pytest

from backends import AgentBackend, ToolCall
from main import AGENT_LOOP_MAX_ITERATIONS, run_agent


class FakeBackend(AgentBackend):
    def __init__(self, responses: list[tuple]):
        # each response: (content, [ToolCall, ...])
        self.responses = list(responses)
        self.seen_messages = []  # snapshot of messages at each chat() call

    def chat(self, messages, tools):
        self.seen_messages.append(list(messages))  # copy: the loop mutates the list
        content, calls = self.responses.pop(0)
        return {"role": "assistant", "content": content}, content, calls

    def tool_message(self, call, result):
        return {"role": "tool", "name": call.name, "content": json.dumps(result)}

    @property
    def calls_made(self) -> int:
        return len(self.seen_messages)


def call(name, **args):
    return ToolCall(id=None, name=name, args=args)


def test_returns_final_answer_without_tools():
    backend = FakeBackend([("Hello!", [])])

    assert run_agent("hi", {}, backend) == "Hello!"
    assert backend.calls_made == 1


def test_executes_tool_and_feeds_result_back():
    seen = []

    def get_booking(booking_id):
        seen.append(booking_id)
        return {"status": "confirmed"}

    backend = FakeBackend(
        [
            ("", [call("get_booking", booking_id="B1")]),
            ("Your booking is confirmed.", []),
        ]
    )

    answer = run_agent("status of B1?", {"get_booking": get_booking}, backend)

    assert answer == "Your booking is confirmed."
    assert seen == ["B1"]
    # the 2nd chat() call must have seen the tool result
    last_msg = backend.seen_messages[1][-1]
    assert last_msg["role"] == "tool"
    assert json.loads(last_msg["content"]) == {"status": "confirmed"}


def test_multiple_tool_calls_in_one_response():
    tools = {"1st tool": lambda: {"v": 1}, "2nd tool": lambda: {"v": 2}}
    backend = FakeBackend(
        [
            ("", [call("1st tool"), call("2nd tool")]),
            ("done", []),
        ]
    )

    run_agent("question", tools, backend)

    tool_names = []
    for msgs in backend.seen_messages[1]:
        if msgs["role"] == "tool":
            tool_names.append(msgs["name"])
    assert tool_names == ["1st tool", "2nd tool"]


def test_unknown_tool_returns_error_and_loop_continues():
    expected_response = "sorry"
    backend = FakeBackend(
        [
            ("", [call("does_not_exist")]),
            (expected_response, []),
        ]
    )

    assert run_agent("question", {}, backend) == expected_response
    tool_msg = backend.seen_messages[1][-1]
    assert json.loads(tool_msg["content"]) == {"error": "Unknown tool"}


@pytest.mark.parametrize(
    "exc, expected",
    [
        (TypeError("bad arg"), "Invalid tool arguments: bad arg"),
        (ValueError("bad value"), "Invalid tool arguments: bad value"),
        (RuntimeError("boom"), "Tool execution failed"),
    ],
)
def test_tool_exceptions_become_error_results(exc, expected):
    def broken():
        raise exc

    backend = FakeBackend([("", [call("broken")]), ("ok", [])])

    run_agent("q", {"broken": broken}, backend)

    tool_msg = backend.seen_messages[1][-1]
    assert json.loads(tool_msg["content"]) == {"error": expected}


def test_stops_after_max_iterations():
    # backend never gives a final answer
    backend = FakeBackend([("", [call("noop")])] * (AGENT_LOOP_MAX_ITERATIONS + 5))

    answer = run_agent("question", {"noop": lambda: {}}, backend)

    assert backend.calls_made == AGENT_LOOP_MAX_ITERATIONS
    assert answer == "I couldn't complete the request. Please try again."
