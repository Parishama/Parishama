#!/usr/bin/env python3
import argparse
from pathlib import Path

from intent_model import RuleBasedIntentModel
from knowledge_base import KnowledgeBase
from app_store import ApplicationStore


EXAMPLES = [
    "hi",
    "where can I find a charging station near me?",
    "how much does it cost to charge an EV?",
    "what are the technical requirements for chargers?",
    "how to apply to set up an ev charging station?",
    "status of APP-123456",
    "update APP-123456: contractor selected and equipment ordered",
]


def run_cli():
    parser = argparse.ArgumentParser(description="Sample EV gov chatbot model")
    parser.add_argument("query", nargs="*", help="User query text; if empty, runs examples")
    parser.add_argument("--data", dest="data_dir", default=str(Path(__file__).resolve().parents[1] / "data"))
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    kb = KnowledgeBase(data_dir / "faq.json")
    store = ApplicationStore(data_dir / "applications.json")
    model = RuleBasedIntentModel()

    inputs = [" ".join(args.query)] if args.query else EXAMPLES

    for text in inputs:
        result = model.classify(text)
        intent = result["intent"]
        slots = result.get("slots", {})
        print(f"\nUSER: {text}")
        print(f"INTENT: {intent} (conf={result['confidence']}) slots={slots}")

        handled = False

        # FAQ intents
        answer = kb.answer_for_intent(intent)
        if answer:
            print(f"BOT: {answer}")
            handled = True

        # Status check
        if intent == "status_check" and "app_id" in slots:
            status = store.status_of(slots["app_id"])
            if status:
                print(f"BOT: Application {slots['app_id']} status: {status}")
            else:
                print(f"BOT: I couldn't find application {slots['app_id']}. Please check the ID.")
            handled = True

        # Progress update
        if intent == "progress_update" and "app_id" in slots and "message" in slots:
            try:
                store.add_progress(slots["app_id"], slots["message"])
                print(f"BOT: Progress noted for {slots['app_id']}: {slots['message']}")
                handled = True
            except KeyError:
                print(f"BOT: I couldn't find application {slots['app_id']}. Please check the ID.")
                handled = True

        if intent == "greeting":
            print("BOT: Hello! I can help with EV charging info and applications.")
            handled = True
        if intent == "goodbye":
            print("BOT: Goodbye! Drive electric!")
            handled = True
        if intent == "help":
            print("BOT: Ask me about finding chargers, costs, incentives, how to apply, or application status like 'status of APP-123456'.")
            handled = True

        if not handled:
            print("BOT: I'm not sure. Try rephrasing or ask for help.")


if __name__ == "__main__":
    run_cli()
