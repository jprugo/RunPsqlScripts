# RunPsqlScripts

Library for python 3 that allows to execute queries for PostgreSQL according to the load definition

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the library.

```bash
pip install RunPsqlScripts
```

## Usage

```powershell
python -m RunPsqlScripts [-l] --secret "{host: localhost, port: 5432, database: postgres, username: postgres, password: runscripts}" --filter "sprint=21"
```

## Short flags

```
    [-l] run only the last record inside run-description.yaml
```

## Long flags

```
    [--secret] data for establish the psycopg2 connection
    [--filters] filters that select within the "run" property the values ​​that satisfy the condition
    [--use-dotenv] read params from dot env file
    [--args1] argument to be replaced inside sql scripts
```

## Requirements

- You need to add a file named **run-description.yaml** in the path where you run the script to specify which of the scripts according to the given names will run. The structure of the file is as follows:

```yaml
directories:
    ScriptTables:
        schema: ods
        childs:
            # Hosted directories where the script is executed
            - Install
            - Uninstall
    ScriptTables2:
        schema: ods
        childs:
            - *
run:
    2022-01-11 09:39:
        # Custom property to filter
        sprint: 21
        lote: 10
        ScriptTables:
            - Script_create_table_cros_ods_creditoHistorico.sql
    2022-01-11 10:39:
        sprint: 21
        lote: 10
        ScriptTables:
            - Script_create_table_cros_ods_creditoHistorico.sql
        ScriptTables2:
            - Script_create_table_cros_ods_creditoHistorico.sql
```

## Folder directory

For the previously defined yaml in the directory where it is executed, it must have the following structure:

```bash
└───ScriptTables
    ├───Install
    │       create_table_test.sql
    │
    └───Uninstall
            delete_table_name_1.sql
└───ScriptTables2
    ├───Instalacion
    │       create_table_test.sql
    │
    └───Desinstalacion
            delete_table_name_1.sql
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
