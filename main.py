#!/usr/bin/env python3

import os
import sys
import argparse
import textwrap
import subprocess
import shlex
import stat as stat_module
from pathlib import Path
from functools import wraps
import lmstudio as lms
import kagiapi as kagi



def main():
    parser = argparse.ArgumentParser(description='Chat with LM Studio models')
    parser.add_argument('prompt', nargs='?', help="Prompt text", default="")
    parser.add_argument('--model', default='openai/gpt-oss-20b', help="Custom model to use")
    parser.add_argument('--draft', help="Draft model to use for speculative decoding")
    parser.add_argument('--talk', action='store_true', help="Respond without using tools")
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

    if args.talk:
        respond(model, prompt, config)
    else:
        act(model, prompt, config)


# --------------------------------------------------------------------------------------------------
# Helpers

def tooldef(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e, file=sys.stderr)
            return f"Error: {str(e) or repr(e)}"

    return wrapper

def is_inside(path, root):
  try:
      r_root = Path(root).resolve()

      Path(path).absolute().relative_to(r_root)
      Path(path).resolve().relative_to(r_root)

      return True

  except (ValueError, RuntimeError, OSError):
      return False

# --------------------------------------------------------------------------------------------------
# ffmpeg

@tooldef
def ffmpeg(args: str):
    """Run ffmpeg with the provided command-line args to inspect or manipulate video files."""
    result = subprocess.run(
        ["ffmpeg"] + shlex.split(args),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return f"Error: {result.stderr}"

    return f"Success: {result.stdout}"




# --------------------------------------------------------------------------------------------------
# File-system

@tooldef
def fs_stat(path: str) -> str:
    """
    Get information about a file or directory.
    Returns a list of attributes including size, created time, modified time, accessed time,
    type ('f', 'd' or 'l') and permissions.
    """
    p = Path(path)
    if not p.exists(): return f"Error: Path does not exist: {path}"

    stats = p.stat()

    file_type = (
        'l' if p.is_symlink() else
        'd' if p.is_dir() else
        'f' if p.is_file() else
        '?'
    )

    lines = [
        f"size: {stats.st_size}",
        f"created: {getattr(stats, 'st_birthtime', None)}",
        f"modified: {stats.st_mtime}",
        f"accessed: {stats.st_atime}",
        f"type: {file_type}",
        f"permissions: {oct(stats.st_mode)[-3:]}",
    ]

    return "\n".join(lines)


@tooldef
def fs_read(path: str, start: int = 0, end: int = -1) -> str:
    """
    Read lines from a file.
    If the optional `start` argument is provided, read from that line (inclusive).
    If the optional `end` argument is provided, read up to that line (inclusive).
    Both arguments can be negative to count from the end, where -1 is the last line.
    Returns the lines as read.
    """
    p = Path(path)
    if not p.exists(): return f"Error: Path does not exist: {path}"
    if not p.is_file(): return f"Error: Path is not a file: {path}"

    with open(p, 'r') as f:
        lines = f.readlines()

    if end == -1:
        sliced = lines[start:]
    elif end < -1:
        sliced = lines[start:len(lines) + 1 + end]
    else:
        sliced = lines[start:end + 1]

    return "".join(sliced)


@tooldef
def fs_list(path: str = ".") -> str:
    """
    List files and directories in the given directory path.
    Returns a table with columns: size, type ('f', 'd' or 'l'), and name.
    """
    p = Path(path)
    if not p.exists(): return f"Error: Path does not exist: {path}"
    if not p.is_dir(): return f"Error: Path is not a directory: {path}"

    entries = []
    for item in sorted(p.iterdir(), key=lambda x: x.name):
        stats = item.stat()
        size = stats.st_size

        file_type = (
            'l' if item.is_symlink() else
            'd' if item.is_dir() else
            'f' if item.is_file() else
            '?'
        )

        entries.append((size, file_type, item.name))

    if not entries:
        return ""

    lines = [
        f"{str(size).rjust(12)}  {file_type}  {name.ljust(50)}"
        for size, file_type, name in entries
    ]

    return "\n".join(lines)


@tooldef
def fs_search(path: str, pattern: str) -> str:
    """
    Search files for a regex pattern in the provided path.
    Returns matching lines in <file>:<line>:<content> format.
    """
    p = Path(path)
    if not p.exists(): return f"Error: Path does not exist: {path}"

    result = subprocess.run(
        ["rg", "--line-number", "--color", "never", pattern, str(p)],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return result.stdout
    elif result.returncode == 1:
        return ""  # No matches found
    else:
        return f"Error: {result.stderr}"




# --------------------------------------------------------------------------------------------------
# Kagi Search (adapted from kagimcp)

kagi_client = kagi.KagiClient(os.getenv('KAGI_API_KEY'))

@tooldef
def search(query: str) -> str:
    """
        Fetch web results based on a query.
        Use for general search and when the user explicitly tells you to 'search' for results/information.
        They are numbered, so that a user may be able to refer to a result by a specific number.
    """
    print('> SEARCH', query)

    if not query:
        return ""

    result = kagi_client.search(query)
    answer = format_results(query, result)

    print('< SEARCH', answer)
    return answer


@tooldef
def fetch_summary(url: str) -> str:
    """
        Fetch summarized content from a URL.
        Works with any document type (text webpage, video, audio, etc.)
    """
    print('> FETCH_SUMMARY', url)

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
            fs_stat,
            fs_read,
            fs_list,
            fs_search,
        ],
        on_prediction_fragment = lambda f, index: print(f.content, end=""),
        on_message = chat.append
    )

    print()


# --------------------------------------------------------------------------------------------------
# Go!

if __name__ == "__main__":
    main()
