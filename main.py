#!/usr/bin/env python3

import sys
import argparse
import lmstudio as lms
from pathlib import Path


def respond(model, prompt, config):
    prediction_stream = model.respond_stream(prompt, config=config)

    try:
        for fragment in prediction_stream:
            print(fragment.content, end="")
    except Exception as e:
        prediction_stream.cancel()
        raise e

    print()


def create_file(name: str, content: str):
    """Create a file with the given name and content."""
    dest_path = Path(name)
    if dest_path.exists():
        return "Error: File already exists."
    try:
        dest_path.write_text(content, encoding="utf-8")
    except Exception as exc:
        return "Error: {exc!r}"
    return "File created."


def act(model, prompt, config):
    chat = lms.Chat("You are a command-line AI agent that executes commands as requested by the user.")

    model.act(
        chat,
        [create_file],
        on_prediction_fragment = lambda f, index: print(f.content, end=""),
        on_message = chat.append
    )

    print()


def main():
    parser = argparse.ArgumentParser(description='Chat with LM Studio models')
    parser.add_argument('prompt', nargs='?', help='Prompt text')
    parser.add_argument('--model', default='qwen/qwen3-30b-a3b-2507', help='Model to use (default: qwen/qwen3-30b-a3b-2507)')
    parser.add_argument('--draft', help='Draft model to use for speculative decoding')
    parser.add_argument('--act', action='store_true', help='Use act API instead of respond_stream')
    args = parser.parse_args()

    stdin_text = sys.stdin.read().strip() if not sys.stdin.isatty() else ''

    prompt_parts = []
    if args.prompt:
        prompt_parts.append(args.prompt)
    if stdin_text:
        prompt_parts.append(stdin_text)

    prompt = '\n'.join(prompt_parts)
    if not prompt.strip():
        sys.exit(1)

    model = lms.llm(args.model)

    config = {
        'draftModel': args.draft or None
    }

    if args.act:
        act(model, prompt, config)
    else:
        respond(model, prompt, config)

if __name__ == "__main__":
    main()
