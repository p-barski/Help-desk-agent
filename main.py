import os

from dotenv import load_dotenv

from backends import AgentBackend, get_backend
from shop_data import ShopData
from tools import Tools

load_dotenv()
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3.5")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()  # or "openai"
AGENT_LOOP_MAX_ITERATIONS = 8

SYSTEM_PROMPT = """
You are a helpful customer support agent for CityWheels - bike rental shop.
Only answer questions that are about CityWheels.
Don't answer general questions that aren't about CityWheels bike rental shop.
Even if you know answer to a question that isn't about CityWheels, do not say it.

Use the available tools when a question requires shop data.
Never invent product prices, stock levels, order statuses,
or shipping information.

When the documents and bookings do not answer a question, or the question has 
nothing to do with CityWheels, say so and tell the customer to contact the staff.
If you cannot verify something, say so clearly.
Answer concisely and politely.
"""


def run_agent(
    question: str, tools: dict[str, callable], backend: AgentBackend = None
) -> str:
    backend = backend or get_backend(LLM_PROVIDER, MODEL_NAME)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for _ in range(AGENT_LOOP_MAX_ITERATIONS):
        assistant_message, content, tool_calls = backend.chat(messages, tools)
        messages.append(assistant_message)

        # No tool call == final answer
        if not tool_calls:
            return content

        for call in tool_calls:
            function = tools.get(call.name)

            if function is None:
                result = {"error": "Unknown tool"}
            else:
                try:
                    result = function(**call.args)
                except (TypeError, ValueError) as exc:
                    result = {"error": f"Invalid tool arguments: {exc}"}
                except Exception:
                    result = {"error": "Tool execution failed"}

            messages.append(backend.tool_message(call, result))

    return "I couldn't complete the request. Please try again."


def setup_tools() -> dict[str, callable]:
    shop_data = ShopData()
    tools = Tools(shop_data)
    return {
        "get_booking": tools.get_booking,
        "search_policies": tools.search_policies,
        "calculate_refund": tools.calculate_refund,
    }


def main():
    print(
        f"Shop assistant ({LLM_PROVIDER}: {MODEL_NAME}). Type 'exit' or 'quit' to exit."
    )
    tools = setup_tools()
    backend = get_backend(LLM_PROVIDER, MODEL_NAME)
    while True:
        try:
            question = input("\nYou: ").strip()
            if question.lower() in {"exit", "quit"}:
                break
            if not question:
                continue
            try:
                print("\nAssistant:", run_agent(question, tools, backend))
            except (KeyboardInterrupt, EOFError) as e:
                raise e
            except Exception as e:
                print(e)

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
