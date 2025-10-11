# `ai`

Command-line AI actor with essential tooling, backed by a local LMStudio.


## Installation

Clone this repository and either run with `uv`, or place a wrapper that calls `uv` in your `PATH`:

```bash
git clone git@github.com:slezica/ai-cli.git
```

Command (or wrapper script):

```
uv run --directory /path/to/repo ai
```

On first run, `uv` will automatically install dependencies on a managed virtualenv.

#### Requirements:

- [`uv`](https://docs.astral.sh/uv/) to manage dependencies
- [LMStudio](https://lmstudio.ai/) running locally to provide inference
- [`rg`](https://github.com/BurntSushi/ripgrep) in your `PATH` for file search
- `KAGI_API_KEY` in your environment for web search/summary


## Usage

Assuming a wrapper called `ai` in your `PATH`:

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

Respond without using tools:
```bash
ai ask "what is the meaning of life?"
```

Ask with a custom model:
```bash
ai ask --model "openai/gpt-oss-20b" "explain quantum computing"
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

