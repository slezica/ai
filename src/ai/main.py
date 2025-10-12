#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "kagiapi>=0.2.1",
#   "lmstudio>=1.5.0",
#   "markdownify>=1.2.0",
#   "readabilipy>=0.3.0",
#   "requests>=2.32.5",
# ]
# ///

"""
Command-line AI actor with essential tooling, backed by a local LMStudio.
"""

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
import readabilipy
import markdownify
import requests


WD = os.getcwd()


def main():
    parser = argparse.ArgumentParser(description="Chat with LM Studio models")
    subparsers = parser.add_subparsers(dest='command', required=True, help="Command to run")

    act_parser = subparsers.add_parser('act', help="Act using tools")
    act_parser.add_argument('prompt', nargs='?', help="Prompt text", default="")
    act_parser.add_argument('--model', default='qwen/qwen3-30b-a3b-2507', help="Custom model to use")
    act_parser.add_argument('--no-sandbox', action='store_true', help="Disable sandbox (runs sandboxed by default)")

    ask_parser = subparsers.add_parser('ask', help="Respond without using tools")
    ask_parser.add_argument('prompt', nargs='?', help="Prompt text", default="")
    ask_parser.add_argument('--model', default='openai/gpt-oss-20b', help="Custom model to use")
    ask_parser.add_argument('--no-sandbox', action='store_true', help="Disable sandbox (runs sandboxed by default)")

    args = parser.parse_args()

    if not args.no_sandbox:
        sandbox_exec() # never returns

    arg_prompt = args.prompt or ""
    stdin_prompt = sys.stdin.read().strip() if not sys.stdin.isatty() else ''

    prompt = f"{arg_prompt}\n\n{stdin_prompt}".strip()

    if not prompt:
        sys.exit(1)

    model = lms.llm(args.model)

    config = {} # hmm

    if args.command == 'ask':
        respond(model, prompt, config)
    else:
        act(model, prompt, config)


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
            web_fetch,
            web_fetch_summary,
            fs_stat,
            fs_read,
            fs_write,
            fs_list,
            fs_search,
            fs_replace,
            fs_mkdir,
            fs_rm,
            fs_pwd,
            shell,
        ],
        on_prediction_fragment = lambda f, index: print(f.content, end=""),
        on_message = chat.append
    )

    print()


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

class PathAlreadyExists(ToolError):
    message = "path '{path}' already exists"

class UnsupportedMimeType(ToolError):
    message = "fetched mime type '{type}' is not supported"

class ResponseTooLong(ToolError):
    message = "fetched text was over the limit of {max} characters"

class RequestFailed(ToolError):
    message = "HTTP request failed: {error}"


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

    p = resolve(path)
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

    p = resolve(path)
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

    p = resolve(path)

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

    p = resolve(path)
    if not p.exists(): raise PathDoesNotExist(path=path)
    if not p.is_dir(): raise PathIsNotDirectory(path=path)

    entries = []
    for item in sorted(p.iterdir(), key=lambda x: x.name):
        try:
            stats = item.stat()
        except:
            continue # could be a broken symlink or a restricted file, for example

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

    p = resolve(path)
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
def fs_rm(path: str) -> str:
    """
    Remove a file or directory at the given path.

    Arguments:
        path: the path to the file or directory to remove

    For directories, recursively deletes all contents after user confirmation.
    Returns a success message.
    """

    p = resolve(path)
    if not p.exists(): raise PathDoesNotExist(path=path)

    if p.is_dir():
        # Require confirmation for directory deletion
        print(f"\nDelete directory '{path}' and all its contents?", file=sys.stderr)
        print("  [Y] Yes | [N] No", file=sys.stderr)

        response = input("> ").strip().upper()

        if response != 'Y':
            raise CommandDenied(command=f"rm {path}")

        # Recursively delete directory
        import shutil
        shutil.rmtree(p)
        return f"Successfully deleted directory {path} and all its contents"

    else:
        # Delete file without confirmation
        p.unlink()
        return f"Successfully deleted file {path}"


@tooldef
def fs_mkdir(path: str) -> str:
    """
    Create a directory at the given path.

    Arguments:
        path: the path to the directory to create

    Creates parent directories as needed (like mkdir -p).
    Returns a success message.
    """

    p = resolve(path)
    if p.exists(): raise PathAlreadyExists(path=path)

    p.mkdir(parents=True, exist_ok=False)

    return f"Successfully created directory at {path}"


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


def resolve(path_str):
    path = Path(path_str)
    root = Path(WD).resolve()

    if path.is_absolute():
        path = path.resolve()
    else:
        path = (root / path).resolve()

    if not path.is_relative_to(root):
        raise PathOutsideWorkDir(path=path_str, wd=WD)

    return path

# --------------------------------------------------------------------------------------------------
# Kagi Search (adapted from kagimcp)

kagi_client = kagi.KagiClient(os.getenv('KAGI_API_KEY'))

web_fetch_types = ['text/plain', 'text/html', 'application/json', 'application/xml', 'text/xml']
web_fetch_max_size = 10_000_000
web_fetch_max_text_length = 100_000

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
def web_fetch(url: str) -> str:
    """
    Fetch web content from a URL.

    Arguments:
        url: the URL to fetch

    Returns a plain-text representation of the content, if possible.
    """
    try:
       with requests.get(url, stream=True) as r:
            content_type = r.headers.get('content-type', '').split(';')[0].strip()

            if content_type not in web_fetch_types:
                raise UnsupportedMimeType(type=content_type)

            total = 0
            data = bytearray()

            for chunk in r.iter_content(chunk_size=8192):
                total += len(chunk)
                if total > web_fetch_max_size:
                    raise ResponseTooLong(max=web_fetch_max_text_length)

                data.extend(chunk)

            text = data.decode(r.encoding or 'utf-8', errors="replace")

            if content_type == 'text/html':
                readable = readabilipy.simple_json_from_html_string(text, use_readability=True)
                text = markdownify.markdownify(readable['content'] or "", heading_style=markdownify.ATX)
            
            if len(text) > web_fetch_max_text_length:
                raise ResponseTooLong(max=web_fetch_max_text_length)

            return text

    except Exception as e:
        raise RequestFailed(error=str(e))


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
# Sandbox

SANDBOX_PROFILE = '''
(version 1)

;; deny everything by default
(deny default)

;; allow reading files from anywhere on host
(allow file-read*)

;; allow exec/fork (children inherit policy)
(allow process-exec)
(allow process-fork)

;; allow signals to self
(allow signal (target self))

;; allow read access to system information
(allow sysctl-read
  (sysctl-name "hw.activecpu") (sysctl-name "hw.busfrequency_compat")
  (sysctl-name "hw.byteorder") (sysctl-name "hw.cacheconfig")
  (sysctl-name "hw.cachelinesize_compat") (sysctl-name "hw.cpufamily")
  (sysctl-name "hw.cpufrequency_compat") (sysctl-name "hw.cputype")
  (sysctl-name "hw.l1dcachesize_compat") (sysctl-name "hw.l1icachesize_compat")
  (sysctl-name "hw.l2cachesize_compat") (sysctl-name "hw.l3cachesize_compat")
  (sysctl-name "hw.logicalcpu_max") (sysctl-name "hw.machine")
  (sysctl-name "hw.ncpu") (sysctl-name "hw.nperflevels")
  (sysctl-name "hw.optional.arm.FEAT_BF16") (sysctl-name "hw.optional.arm.FEAT_DotProd")
  (sysctl-name "hw.optional.arm.FEAT_FCMA") (sysctl-name "hw.optional.arm.FEAT_FHM")
  (sysctl-name "hw.optional.arm.FEAT_FP16") (sysctl-name "hw.optional.arm.FEAT_I8MM")
  (sysctl-name "hw.optional.arm.FEAT_JSCVT") (sysctl-name "hw.optional.arm.FEAT_LSE")
  (sysctl-name "hw.optional.arm.FEAT_RDM") (sysctl-name "hw.optional.arm.FEAT_SHA512")
  (sysctl-name "hw.optional.armv8_2_sha512") (sysctl-name "hw.packages")
  (sysctl-name "hw.pagesize_compat") (sysctl-name "hw.physicalcpu_max")
  (sysctl-name "hw.tbfrequency_compat") (sysctl-name "hw.vectorunit")
  (sysctl-name "kern.hostname") (sysctl-name "kern.maxfilesperproc")
  (sysctl-name "kern.osproductversion") (sysctl-name "kern.osrelease")
  (sysctl-name "kern.ostype") (sysctl-name "kern.osvariant_status")
  (sysctl-name "kern.osversion") (sysctl-name "kern.secure_kernel")
  (sysctl-name "kern.usrstack64") (sysctl-name "kern.version")
  (sysctl-name "sysctl.proc_cputype") (sysctl-name-prefix "hw.perflevel"))

;; allow writes to specific paths
(allow file-write*
  (subpath (param "CWD"))
  (subpath (string-append (param "HOME") "/.cache"))
  (subpath (string-append (param "HOME") "/.gitconfig"))
  (literal "/dev/stdout") (literal "/dev/stderr") (literal "/dev/null"))

;; allow communication with system services
(allow mach-lookup
  (global-name "com.apple.sysmond")
  (global-name "com.apple.SystemConfiguration.configd"))

;; allow system configuration access
(allow system-info)

;; enable terminal access
(allow file-ioctl (regex #"^/dev/tty.*"))

;; allow outbound network traffic
(allow network-outbound)
'''

def sandbox_exec():
    # Pass through all args and add --no-sandbox at the end:
    args = sys.argv[1:] + ['--no-sandbox']

    # Get CWD and HOME for sandbox profile:
    cwd = os.getcwd()
    home = os.path.expanduser('~')

    # Build sandbox-exec command:
    cmd = [
        'sandbox-exec',
        '-D', f'CWD={cwd}',
        '-D', f'HOME={home}',
        '-p', SANDBOX_PROFILE,
        sys.executable, '-m', 'ai.main'
    ] + args

    # Replace current process:
    os.execvp('sandbox-exec', cmd)


# --------------------------------------------------------------------------------------------------
# Go!

if __name__ == "__main__":
    main()
