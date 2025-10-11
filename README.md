# `ai`

Command-line AI actor with essential tooling, backed by a local LMStudio.


## Installation

Clone this repository and install with uv:

```bash
git clone <repo-url> ai
cd ai
uv sync
```

### Requirements:

- [`uv`](https://docs.astral.sh/uv/) to manage dependencies
- [LMStudio](https://lmstudio.ai/) running locally to provide inference
- [`rg`](https://github.com/BurntSushi/ripgrep) in your `PATH` for file search
- `KAGI_API_KEY` in your environment for web search/summary


## Usage

Act using tools:
```bash
uv run ai act "is this working?"
```

Act with additional piped data:
```bash
seq 10 | uv run ai act "how many numbers in the following sequence?"
```

Act with a custom model:
```bash
uv run ai act --model "openai/gpt-oss-20b" "you are my favorite model"
```

Respond without using tools:
```bash
uv run ai ask "what is the meaning of life?"
```

Ask with a custom model:
```bash
uv run ai ask --model "openai/gpt-oss-20b" "explain quantum computing"
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

### Web
- **web_search**: search the web using Kagi
- **web_fetch_summary**: fetch and summarize content from URLs

### Shell
- **shell**: execute shell commands (with interactive permission system)

All file system operations are restricted to the current working directory for safety.
