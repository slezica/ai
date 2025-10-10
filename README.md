# `ai`

Command-line AI actor with essential tooling, backed by a local LMStudio.


## Installation

Take `main.py` with you, put it in your `PATH` under a name you like. I use `ai`.

### Requires:

- [`uv`](https://docs.astral.sh/uv/) to execute the script and manage dependencies.
- [LMStudio](https://lmstudio.ai/) running locally to provide inference.
- [`rg`](https://github.com/BurntSushi/ripgrep) in your `PATH` for file search.
- `KAGI_API_KEY` in your env for web search/summary.


## Usage

_Assuming `main.py` is in your `PATH` named `ai`_.

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

Act with speculative decoding:
```bash
ai act --model "large-model" --draft "small-model" "be nice to your smaller model"
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

When using the `act` subcommand, the agent has the following tools:

- **fs_pwd**: get the current working directory
- **fs_stat**: get file/directory metadata (size, times, type, permissions)
- **fs_list**: list directory contents with size, type and name
- **fs_read**: read file contents with optional line ranges
- **fs_write**: write content to a file using specified mode (w, a, etc.)
- **fs_search**: search files by regex pattern using ripgrep
- **fs_replace**: replace occurrences of a string in a file (precise edits)

Note: web search and shell execution tools are currently disabled in the code.
