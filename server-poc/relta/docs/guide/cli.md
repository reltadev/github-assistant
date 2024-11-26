# CLI

The Relta CLI is a command line interface for setting up and managing Relta in your project. It is not intended to be invoked in a deployment of Relta. The Relta CLI can be run with `relta` when a Python environment with Relta installed is active.

```bash
$ relta
...
chat      Create a chat on a DataSource for testing and demo purposes.
create    Create a new DataSource, optionally specifying a name (--name).
delete    Delete a DataSource
deploy    Deploy the semantic layer for a DataSource, which copies the data from the source that is relevant to the semantic layer.
layer     Print the semantic layer for a DataSource
list      List all DataSources
propose   Generate a semantic layer for a DataSource.
wizard    Conversational TUI for setting up a semantic layer for a DataSource
```

The Relta CLI provides documentation for commands within the CLI. For example, run `relta create` to see the documentation for the `create` command.

## Relta Wizard

The Relta Wizard is a TUI that offers a conversational way to set up a SemanticLayer for a DataSource. It is invoked with `relta wizard {datasource_name}`.

It provides a chat interface for interacting with a semantic agent and a view of the current semantic layer with diffs that you can approve or reject.

The diffs are provided using `ndiff` from the `difflib` standard library. To read this diff:

- Lines starting with `- ` indicate lines that were removed
- Lines starting with `+ ` indicate lines that were added
- Lines starting with `? ` provide hints about where changes occurred within lines
- Lines without any prefix indicate unchanged lines

You can approve or reject the diff which saves or reverts the semantic layer by pressing `a` or `r` respectively.
