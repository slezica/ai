# `ai`

Command-line AI actor with essential tooling, sandboxed, backed by a local LMStudio. Mostly an experiment.


## Installation

You can have `uv` manage your installation, or get `src/ai/main.py` and do it yourself.

**Managed**

Clone this repository and install it with `uv tool`.

```bash
git clone git@github.com:slezica/ai.git
cd ai
uv tool install .
```

**Manual**
Download `src/ai/main.py`, then add this alias or wrapper and call it `ai`:

```bash
uv run --script /path/to/main.py # uv will auto-manage dependencies
```

Alternatively, install dependencies yourself as listed in `pyproject.toml` and just run the script.


#### Requirements:

- [`uv`](https://docs.astral.sh/uv/) to manage dependencies
- [LMStudio](https://lmstudio.ai/) running locally to provide inference
- [`rg`](https://github.com/BurntSushi/ripgrep) in your `PATH` for file search
- `KAGI_API_KEY` in your environment for web search/summary


## Usage

Act using tools:
```bash
ai act "is this working?"
```

Act with additional piped data:
```bash
seq 10 | ai act "how many numbers in the following sequence?"
```

Act with a custom model:
```bash
ai act --model "openai/gpt-oss-20b" "you are my favorite model"
```

Ask without using tools:
```bash
ai ask "what is the meaning of life?"
```

Ask with a custom model:
```bash
ai ask --model "openai/gpt-oss-20b" "explain quantum computing"
```

### Sandbox

The script sandboxes itself using `sandbox-exec`, and has various restrictions. Most importantly, it can't write outside the current working directory.

You can disable this behavior with `--no-sandbox`.

```bash
ai act --no-sandbox "create a file in ../outside.txt"
```


## Tools Available

When using the `act` subcommand, the agent has access to:

### File System
- **fs_pwd**: get the current working directory
- **fs_stat**: get file/directory metadata (size, times, type, permissions)
- **fs_list**: list directory contents with size, type and name
- **fs_read**: read file contents with optional line ranges
- **fs_write**: write content to a file using specified mode (w, a, etc.)
- **fs_search**: search files by regex pattern using ripgrep
- **fs_replace**: replace occurrences of a string in a file (precise edits)
- **fs_mkdir**: create directories recursively
- **fs_rm**: remove files or directories (with confirmation for directories)

All file system operations are restricted to the current working directory.

### Web
- **web_search**: search the web using Kagi
- **web_fetch_summary**: fetch and summarize content from URLs

### Shell
- **shell**: execute shell commands (with interactive permission system)


# FAQ

Common questions from millions of users.

**Is this better than Claude Code?**

No, not at all. Not even close. It is private, if you want to see the bright side.

**What is it for then?**

I mostly use it to run commands I don't remember the flags for. Any reasonably-sized model
can do that quickly using basic tooling.

**Is it safe to use?**

It's sandboxed because it wasn't. Just be careful with your current working directory.


