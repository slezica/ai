#!/usr/bin/env python3

# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "kagiapi>=0.2.1",
#     "lmstudio>=1.5.0",
# ]
# ///
"""
Command-line AI actor with essential tooling, backed by a local LMStudio.
"""

__version__ = '0.1.0'
__author__ = "Santiago Lezica"

import os
import sys
import traceback
import argparse
import textwrap
import subprocess
import shlex
import stat as stat_module
from pathlib import Path
from functools import wraps
import lmstudio as lms
import kagiapi as kagi


WD = os.getcwd()


def main():
    parser = argparse.ArgumentParser(description="Chat with LM Studio models")
    subparsers = parser.add_subparsers(dest='command', required=True, help="Command to run")

    act_parser = subparsers.add_parser('act', help="Act using tools")
    act_parser.add_argument('prompt', nargs='?', help="Prompt text", default="")
    act_parser.add_argument('--model', default='openai/gpt-oss-20b', help="Custom model to use")
    act_parser.add_argument('--draft', help="Draft model to use for speculative decoding")

    ask_parser = subparsers.add_parser('ask', help="Respond without using tools")
    ask_parser.add_argument('prompt', nargs='?', help="Prompt text", default="")
    ask_parser.add_argument('--model', default='openai/gpt-oss-20b', help="Custom model to use")
    ask_parser.add_argument('--draft', help="Draft model to use for speculative decoding")

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

    if args.command == 'ask':
        respond(model, prompt, config)
    else:
        act(model, prompt, config)


# --------------------------------------------------------------------------------------------------
# Helpers

def tooldef(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            print('!', func.__name__, kwargs)
            return func(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            return f"Error: {str(e) or repr(e)}"

    return wrapper


class ToolError(Exception):
    message = "" # override

    def __init__(self, **kwargs):
        self.details = kwargs
        super().__init__("Error: " + self.message.format(**kwargs))

class PathDoesNotExist(ToolError):
    message = "path '{path}' does not exist"

class PathIsNotDirectory(ToolError):
    message = "path '{path}' is not a directory"

class PathIsNotFile(ToolError):
    message = "path '{path}' is not a file"

class PathOutsideWorkDir(ToolError):
    message = "path '{path}' is outside working directory '{wd}'"

class InvalidUrl(ToolError):
    message = "url {url} is not valid"

class MissingOrEmpty(ToolError):
    message = "{name} cannot be missing or empty"

class CommandDenied(ToolError):
    message = "command '{command}' denied"

class CommandForbidden(ToolError):
    message = "command '{command}' is forbidden"

class FailedReplace(Exception):
    pass

# --------------------------------------------------------------------------------------------------
# Shell

shell_allowed = []
shell_forbidden = []


@tooldef
def shell(command: str, arguments: list[str]):
    """
    Run a shell command with arguments.

    Arguments:
        command  : the command to execute
        arguments: list of arguments to pass to the command

    Returns the mixed stdout/stderr output.
    """

    if command not in shell_allowed:
        if command in shell_forbidden:
            raise CommandForbidden(command=command)

        # Ask for permission
        print(f"\nAllow command '{command}'?", file=sys.stderr)
        print("  [Y] Yes | [N] No | [A] Always | [X]Never", file=sys.stderr)

        response = input("> ").strip().upper()

        if response == 'A': # always
            shell_allowed.append(command)

        elif response == 'Y': # yes, this time
            pass

        elif response == 'N': # not, not this time
            raise CommandDenied(command=command)

        elif response == 'X': # never
            shell_forbidden.append(command)
            raise CommandDenied(command=command)

        else: # no by default
            raise CommandDenied(command=command)

    result = subprocess.run(
        [command] + arguments,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    output = result.stdout if result.stdout.strip() else "(no output)"

    if result.returncode != 0:
        return f"Error (exit code {result.returncode}):\n{output}"

    return f"Success (exit code 0):\n{output}"


# --------------------------------------------------------------------------------------------------
# File-system

@tooldef
def fs_pwd() -> str:
    """
    Get the current working directory.

    Returns the absolute path of the current working directory.
    """
    return WD


@tooldef
def fs_stat(path: str) -> str:
    """
    Get information about a file or directory.

    Arguments:
        path: the path to the file or directory

    Returns attributes including size, created time, modified time, accessed time, type ('f', 'd' or 'l') and permissions.
    """

    p = Path(path)
    if not is_inside(p, WD): raise PathOutsideWorkDir(path=path, wd=WD)
    if not p.exists(): raise PathDoesNotExist(path=path)

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

    Arguments:
        path : the path to the file
        start: the line number to start from (inclusive), defaults to 0
        end  : the line number to end at (inclusive), defaults to -1 (last line)

    Both start and end can be negative to count from the end, where -1 is the last line.
    Returns the lines as read.
    """

    p = Path(path)
    if not is_inside(p, WD): raise PathOutsideWorkDir(path=path, wd=WD)
    if not p.exists(): raise PathDoesNotExist(path=path)
    if not p.is_file(): raise PathIsNotFile(path=path)

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
def fs_write(path: str, content: str, mode: str = 'w') -> str:
    """
    Write content to a file using the specified mode.

    Arguments:
        path   : the path to the file
        content: the content to write
        mode   : file mode - 'w' (write/overwrite), 'w+' (write/read), 'a' (append), 'a+' (append/read), etc.

    Returns a success message.
    """

    p = Path(path)
    if not is_inside(p, WD): raise PathOutsideWorkDir(path=path, wd=WD)

    with open(p, mode) as f:
        f.write(content)

    return f"Successfully wrote {len(content)} characters to {path} (mode: {mode})"


@tooldef
def fs_list(path: str = ".") -> str:
    """
    List files and directories in the given directory path.

    Arguments:
        path: the directory path to list, defaults to current directory

    Returns a table with columns: size, type ('f', 'd' or 'l'), and name.
    """

    p = Path(path)
    if not is_inside(p, WD): raise PathOutsideWorkDir(path=path, wd=WD)
    if not p.exists(): raise PathDoesNotExist(path=path)
    if not p.is_dir(): raise PathIsNotDirectory(path=path)

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

    Arguments:
        path   : the path to search in
        pattern: the regex pattern to search for

    Returns matching lines in <file>:<line>:<content> format.
    """

    p = Path(path)
    if not is_inside(p, WD): raise PathOutsideWorkDir(path=path, wd=WD)
    if not p.exists(): raise PathDoesNotExist(path=path)

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


@tooldef
def fs_replace(path: str, old_string: str, new_string: str, replace_all: bool = False) -> None:
    """
    Replace occurences of a string in a file for a new string. Good for precise edits.

    Arguments:
        path       : the path to the file.
        old_string : the string to find and replace
        new_string : the replacement string
        replace_all: a boolean indicating whether to replace all occurences (true) or just the first (false)

    Returns nothing if successful, an error if not.
    """
    try:
        with open(path) as f:
            content = f.read()
    except Exception as e:
        raise FailedReplace(f"Error reading file: {str(e)}")

    if len(old_string) == 0:
        raise FailedReplace("old_string must be a non-empty string")

    if len(new_string) == 0:
        raise FailedReplace("new_string must be a non-empty string")

    if old_string == new_string:
        raise FailedReplace("new_string must be different from old_string")

    count = content.count(old_string)

    if count == 0:
        raise FailedReplace("old_string not found in content")

    if replace_all:
        updated_content = content.replace(old_string, new_string)
    else:
        updated_content = content.replace(old_string, new_string, 1)

    try:
        with open(path, 'w') as f:
            f.write(updated_content)
    except Exception as e:
        raise FailedReplace(f"Error writing file: {str(e)}")


def is_inside(path, root):
    try:
        Path(path).absolute().relative_to(Path(root).absolute())
        Path(path).resolve().relative_to(Path(root).resolve())
  
        return True
  
    except (ValueError, RuntimeError, OSError):
        return False

# --------------------------------------------------------------------------------------------------
# Kagi Search (adapted from kagimcp)

kagi_client = kagi.KagiClient(os.getenv('KAGI_API_KEY'))


@tooldef
def web_search(query: str) -> str:
    """
    Fetch web results based on a query.

    Arguments:
        query: the search query

    Use for general search and when the user explicitly tells you to 'search' for results/information.
    Returns numbered results that can be referred to by number.
    """

    if not query: raise MissingOrEmpty(name="query")

    result = kagi_client.search(query)
    answer = format_results(query, result)

    return answer


@tooldef
def web_fetch_summary(url: str) -> str:
    """
    Fetch web summarized content from a URL.

    Arguments:
        url: the URL to fetch and summarize

    Works with any document type (text webpage, video, audio, etc.)
    Returns a summary of the content.
    """
    if not url: raise InvalidUrl(url=url)

    answer = kagi_client.summarize(
        url             = url,
        engine          = "cecil",
        summary_type    = "summary",
        target_language = "EN",
    )["data"]["output"]

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


def act(model: lms.LLM, prompt, config):
    chat = lms.Chat(prompt)

    model.act(
        chat,
        [
            web_search,
            web_fetch_summary,
            # shell,
            fs_stat,
            fs_read,
            fs_write,
            fs_list,
            fs_search,
            fs_pwd
        ],
        on_prediction_fragment = lambda f, index: print(f.content, end=""),
        on_message = chat.append
    )

    print()


# --------------------------------------------------------------------------------------------------
# Go!

if __name__ == "__main__":
    main()
