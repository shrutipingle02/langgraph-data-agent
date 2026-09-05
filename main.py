from dotenv import load_dotenv
load_dotenv()

from agents.data_agent import data_agent
from langchain_core.messages import HumanMessage

if __name__ == "__main__":

    print("Data Agent. Ask a question about the database, or ask for an ETL job.")
    print("Ctrl+C to quit.\n")

    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not question:
            continue

        response = data_agent.invoke(
            {"messages": [HumanMessage(content=question)],
             "route_response": ""}
        )

        print(f"\n[routed to: {response['route_response']}]")
        print(response['messages'][-1].content, "\n")
