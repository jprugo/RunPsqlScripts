# RunPsqlScripts

Library for python 3 that allows to execute queries for PostgreSQL according to the load definition

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the library.

```bash
pip install RunPsqlScripts
```

## Usage

```powershell
python -m RunPsqlScripts [-l] --secret "{host: localhost, port: 5432, database: postgres, username: postgres, password: runscripts}" --filter "sprint=21" --param "telefono=1234567"
```

## Short flags

```
    [-l] run only the last record inside run-description.yml
```

## Long flags

```
    [--secret] data for establish the psycopg2 connection
    [--filters] filters that select within the "run" property the values ​​that satisfy the condition
    [--dot-env-path] read params from dot env file
    [--param] argument to be replaced inside sql scripts
```

## Requirements

- You need to add a file named **run-description.yml** in the path where you run the script to specify which of the scripts according to the given names will run. The structure of the file is as follows:

```yaml
directories:
    ScriptsTables:
        schema: public #util
        childs:
            # Hosted directories where the script is executed
            - Install
            - Uninstall
    ScriptsInserts:
        schema: public #util
        childs:
            # Hosted directories where the script is executed
            - Install
            - Uninstall
run:
    2022-01-11 09:39:
        sprint: '21'
        lote: '10'
        # folders
        ScriptsTables:
            Install:
                - install.sql
            Uninstall:
                - uninstall.sql
        ScriptsInserts:
            Install:
                - insert.sql
            Uninstall:
                - uninstall.sql
    2022-01-11 10:39:
        sprint: '22'
        lote: '11'
        # folders
        # ScriptsTables:
        #     Install:
        #         - install.sql
        #     Uninstall:
        #         - uninstall.sql
        ScriptsInserts:
            Install:
                - insert.sql
```

## Folder directory

For the previously defined yaml in the directory where it is executed, it must have the following structure:

```bash
└───ScriptTables
    ├───Install
    │       install.sql
    │
    └───Uninstall
            uninstall.sql
└───ScriptInserts
    ├───Instalacion
    │       install.sql
    │
    └───Desinstalacion
            uninstall.sql
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
