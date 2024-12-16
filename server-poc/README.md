#github-assistant backend 

The github-assistant backend exposes a set of APIs that allows users to:

1. Load GitHub data for different repos and load it into a Postgres database
2. Ask questions from the data in plain Enlgish'

The data pipelines are built using dlt and the source code is available in the `data_pipelines` folder. The text-to-SQL pieces are built with Relta and the semantic layer used can be found in the `semantic_layer` folder. All endpoints are implemented in the `server_poc` folder.

The Relta submodule is a Python library that can be used to build and deploy semantic layers that power natural language interfaces to relational data. If you are interested in accessing Relta please send an email to amir [at] relta.dev 