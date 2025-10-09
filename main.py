#!/usr/bin/env python3

import os
import sys
import argparse
import textwrap
import subprocess
import shlex
import stat as stat_module
from pathlib import Path
import lmstudio as lms
import kagiapi as kagi


def main():
    parser = argparse.ArgumentParser(description='Chat with LM Studio models')
    parser.add_argument('prompt', nargs='?', help="Prompt text", default="")
    parser.add_argument('--model', default='openai/gpt-oss-20b', help="Custom model to use")
    parser.add_argument('--draft', help="Draft model to use for speculative decoding")
    parser.add_argument('--act', action='store_true', help="Use act instead of respond")
    args = parser.parse_args()

    arg_prompt = args.prompt or ""
    stdin_prompt = sys.stdin.read().strip() if not sys.stdin.isatty() else ''

    prompt = f"{arg_prompt}\n\n{stdin_prompt}".strip()

    if not prompt:
        sys.exit(1)

    model = lms.llm(args.model)

    config = {
        'draftModel': args.draft or None
    }

    if args.act:
        act(model, prompt, config)
    else:
        respond(model, prompt, config)


# --------------------------------------------------------------------------------------------------
# ffmpeg

def ffmpeg(args: str):
    """Run ffmpeg with the provided command-line args to inspect or manipulate video files."""
    try:
        result = subprocess.run(
            ["ffmpeg"] + shlex.split(args),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return f"Error: {result.stderr}"

        return f"Success: {result.stdout}"

    except Exception as exc:
        return f"Error: {exc!r}"




# --------------------------------------------------------------------------------------------------
# File-system

def stat(path: str) -> str:
    """Get information about a file or directory."""
    try:
        p = Path(path)
        if not p.exists():
            return f"Error: Path does not exist: {path}"

        stats = p.stat()

        lines = [
            f"size: {stats.st_size}",
            f"created: {getattr(stats, 'st_birthtime', None)}",
            f"modified: {stats.st_mtime}",
            f"accessed: {stats.st_atime}",
            f"isDirectory: {stat_module.S_ISDIR(stats.st_mode)}",
            f"isFile: {stat_module.S_ISREG(stats.st_mode)}",
            f"permissions: {oct(stats.st_mode)[-3:]}",
        ]

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e) or repr(e)}"


def read(path: str, start: int = 0, end: int = -1) -> str:
    """
    Read lines from a file.
    If the optional `start` argument is provided, read from that line (inclusive).
    If the optional `end` argument is provided, read up to that line (inclusive).
    Both arguments can be negative to count from the end, where -1 is the last line.
    """
    try:
        p = Path(path)
        if not p.exists():
            return f"Error: Path does not exist: {path}"

        if not p.is_file():
            return f"Error: Path is not a file: {path}"

        with open(p, 'r') as f:
            lines = f.readlines()

        if end == -1:
            sliced = lines[start:]
        elif end < -1:
            sliced = lines[start:len(lines) + 1 + end]
        else:
            sliced = lines[start:end + 1]

        return "".join(sliced)

    except Exception as e:
        return f"Error: {str(e) or repr(e)}"




# --------------------------------------------------------------------------------------------------
# Kagi Search (adapted from kagimcp)

kagi_client = kagi.KagiClient(os.getenv('KAGI_API_KEY'))

def search(query: str) -> str:
    """
        Fetch web results based on a query.
        Use for general search and when the user explicitly tells you to 'search' for results/information.
        They are numbered, so that a user may be able to refer to a result by a specific number.
    """
    print('> SEARCH', query)
    try:
        if not query:
            return ""

        result = kagi_client.search(query)
        answer = format_results(query, result)

        print('< SEARCH', answer)
        return answer

    except Exception as e:
        print(e, file=sys.stderr)
        return f"Error: {str(e) or repr(e)}"


def fetch_summary(url: str) -> str:
    """
        Fetch summarized content from a URL.
        Works with any document type (text webpage, video, audio, etc.)
    """
    print('> FETCH_SUMMARY', url)

    try:
        if not url:
            raise ValueError("Summarizer called with no URL.")

        answer = kagi_client.summarize(
            url             = url,
            engine          = "cecil",
            summary_type    = "summary",
            target_language = "EN",
        )["data"]["output"]

        print('< FETCH_SUMMARY', answer)
        return answer

    except Exception as e:
        print(e, file=sys.stderr)
        return f"Error: {str(e) or repr(e)}"


def format_results(query: str, response) -> str:
    template = textwrap.dedent("""
        {number}: {title}
        {url}
        Published Date: {published}
        {snippet}
    """).strip()

    # t == 0 is search result, t == 1 is related searches
    results = [result for result in response["data"] if result["t"] == 0]

    # published date is not always present
    results_formatted = [
        template.format(
            number    = number,
            title     = result["title"],
            url       = result["url"],
            published = result.get("published", "Not Available"),
            snippet   = result["snippet"],
        )
        for number, result in enumerate(results)
    ]

    return "\n\n".join(results_formatted)


# --------------------------------------------------------------------------------------------------
# LLM

def respond(model, prompt, config):
    prediction_stream = model.respond_stream(prompt, config=config)

    try:
        for fragment in prediction_stream:
            print(fragment.content, end="")
    except Exception as e:
        prediction_stream.cancel()
        raise e

    print()


def act(model, prompt, config):
    chat = lms.Chat(prompt)

    model.act(
        chat,
        [
            search,
            fetch_summary,
            ffmpeg,
            stat,
            read,
        ],
        on_prediction_fragment = lambda f, index: print(f.content, end=""),
        on_message = chat.append
    )

    print()


# --------------------------------------------------------------------------------------------------
# Go!

if __name__ == "__main__":
    main()
