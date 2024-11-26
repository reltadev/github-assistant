# Relta

## Getting Started

Relta suggests the following environment variables to be set:

| Environment Variable | Purpose                  | Required? |
| -------------------- | ------------------------ | --------- |
| OPENAI_API_KEY       | LLM Models used by Relta | Yes       |
| LOGFIRE_TOKEN        | Logfire for logging      | No        |
| LANGCHAIN_API_KEY    | LangSmith for tracing    | No        |
| LANGCHAIN_TRACING_V2 | LangSmith for tracing    | No        |

These can be set in a `.env` file or passed in a `Configuration` object when initializing the Client. If you are doing LangSmith tracing, please use a method to load those variables into your environment, such as `python-dotenv`.

```py
# Optionally, for LangSmith tracing, load in environment variables including LANGCHAIN_API_KEY and LANGCHAIN_TRACING_V2 from a `.env` file.
from dotenv import load_dotenv
load_dotenv()

import relta
rc = relta.Client() # sets up Relta files in-repo. must be ran before other Relta functions. optionally pass in a Configuration object.
source = rc.create_datasource("../data/users.csv") # attaches to a file, Postgres URI, etc.
                                                   # also exposes {get,delete}_datasource

source.semantic_layer.propose([
    "What's the YoY trend of user signups?",
    "What percent of users signed in last week?",
    "Give me the 5 users that signed in the most."
])

source.deploy()

chat = rc.create_chat(source) # creates a new thread talking to `source`
resp = chat.prompt("Give me the list of users that signed in yesterday")

print(resp.text)
```

You can also try this out using the developer CLI:

```bash
$ relta create --name users ../data/users.csv
$ relta propose users
# ?: What's the YoY trend of user signups?
# ?: What percent of users signed in last week?
# ?: Give me the 5 users that signed in the most.
$ relta deploy users
$ relta chat users
# ?: Give me the list of users that signed in yesterday
```

## 🔪 Rough Edges

- Use only one Relta Client for a given Python Process.
- `DataSource` objects cannot be modified after creation by the user.

## Contributing

### Developer Setup

You will need Python 3.9 and Poetry 1.5.1 installed. For example:

```sh
$ # install python 3.9 via pyenv, pipx for poetry
$ brew install pyenv pipx
$ pyenv install 3.9
$ pyenv local 3.9
$ # install poetry and set up environment
$ pipx install poetry==1.5.1 # you will have merge conflicts using other versions of poetry
$ poetry env use 3.9
$ poetry install
$ poetry run pre-commit install # install pre-commit hooks for formatting and linting
```

If you would like tab completions for Poetry, go to [this link](https://python-poetry.org/docs/#enable-tab-completion-for-bash-fish-or-zsh).

#### Documentation

<!-- To run documentation locally, you need to have [d2](https://d2lang.com/) installed. For example:

```sh
$ brew install d2
``` -->

Preview documentation locally with `poetry run mkdocs serve`. We use [Google style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).
