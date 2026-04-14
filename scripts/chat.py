from my_mcp_agent.agent import chat

def main() -> None:
    print("Personal agent. Type 'exit' to quit.\n")
    while True:
        user_message = input("You: ").strip()
        if user_message.lower() in {"exit", "quit"}:
            break
        result = chat(user_message)
        print(f"\nAgent: {result.reply}\n")
        if result.extracted:
            print(f"Extracted memory: {result.extracted.model_dump()}\n")

if __name__ == "__main__":
    main()
