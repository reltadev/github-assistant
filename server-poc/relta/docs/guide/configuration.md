# Configuration

Relta exposes configuration from the `relta.Configuration` class. The following parameters are key configuration options:

| Option             | Type | Default        | Description                                     |
| ------------------ | ---- | -------------- | ----------------------------------------------- |
| relta_dir_path     | Path | Path(".relta") | Main directory for Relta files                  |
| openai_key         | str  | -              | OpenAI API key (set via OPENAI_API_KEY)         |
| debug              | bool | False          | Enable debug mode (not fully implemented)       |
| github_token       | str  | ""             | GitHub token (set via GITHUB_TOKEN)             |
| github_repo        | str  | ""             | GitHub repository (set via GITHUB_REPO)         |
| github_base_branch | str  | ""             | GitHub base branch (set via GITHUB_BASE_BRANCH) |

The list of all configuration options is available in the [source code](#api-reference).

The typical setup is to store Relta-specific configuration in `pyproject.toml` in a `[tool.relta]` section and use a `.env` file for secrets like `OPENAI_API_KEY`.

## Configuration Source Priorities

The `relta.Configuration` object automatically populates from the following sources, in descending order of priority:

1. Passing in variables when initializing `relta.Configuration` to be passed into `relta.Client`
2. `relta.toml`
3. `pyproject.toml` in a `[tool.relta]` section
4. Environment variables, or a `.env` file
5. Default values

## API Reference

::: relta.config.Configuration
    options:
        show_root_toc_entry: false
