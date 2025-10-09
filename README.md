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

Prompt the default model:
```bash
ai "is this working?"
```

Prompt the default model with additional piped data:
```bash
seq 10 | ai "how many numbers in the following sequence?"
```

Prompt a custom model:
```bash
ai --model "meta/llama-3-8b" "you are my favorite model, just so you know"
```

Use speculative decoding:
```bash
ai --model "large-model" --draft "small-model" "be nice to your smaller model"
```

Disable action and tooling, just respond:

```bash
ai --talk "what is the meaning of life?"
```


## Tools Available

Unless `--talk` is given, the agent has the following tools:

- **fs_list**: list directory contents with name, size and type
- **fs_stat**: get file/directory metadata (size, times, type, permissions)
- **fs_read**: read file contents with optional line ranges
- **fs_search** - search files by regex pattern using ripgrep
- **search** - web search via Kagi API
- **fetch_summary** - web page summary via Kagi API
- **ffmpeg** - permission to run ffmpeg commands for video inspection/manipulation
