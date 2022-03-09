# binaries
from getopt import getopt
import sys
import re
import os
import platform
from dotenv import load_dotenv
# custom
from RunPsqlScripts.RunPsqlScripts import change_schema, psycopg2, read_run_description_file, logger, ValidationError, read_content_script


def main():
    logger.info('Hello!')
    # Se obtienen los argumentos proporcionados en el comando
    argv = sys.argv[1:]

    # Variables nulas de ejecucion
    secret = None
    run_description_data = None

    # Variables por defecto
    dot_env_path = None

    execute_last = False
    filters = []
    params = {}

    # se hace uso del modulo get opt para mandejar los argumentos pasados al script
    try:
        opts, args = getopt(
            argv,
            shortopts='l',
            longopts=[
                "param ",
                "secret ",
                "filter ",
                "dot-env-path "
            ]
        )
    except Exception as e:
        logger.info('An exception ocurred: ' + str(e))
        sys.exit(2)

    for opt, arg in opts:
        # Mandatorio y transversal a parametros y tablas
        if opt in ['--secret']:
            secret = arg
            try:
                secret = {
                    'host': re.search(r"""(["']?host["']?:)([^[,}\]]+)""", secret).group(2).strip(),
                    'port': re.search(r"""(["']?port["']?:)([^[,}\]]+)""", secret).group(2).strip(),
                    'database': re.search(r"""(["']?database["']?:)([^[,}\]]+)""", secret).group(2).strip(),
                    'user': re.search(r"""(["']?username["']?:)([^[,}\]]+)""", secret).group(2).strip(),
                    'password': re.search(r"""(["']?password["']?:)([^[,}\]]+)""", secret).group(2).strip(),
                }
            except AttributeError as e:
                logger.error(
                    f'Se ha suministrado un formato incorrecto para la propiedad secret (revisar la documentacion) str({e})')
                sys.exit()

        elif opt in ['--filter']:
            filters.append(arg)
        elif opt in ['--dot-env-path']:
            dot_env_path = arg
            logger.info(f'Getting .env data from : {dot_env_path}')
            load_dotenv(dotenv_path=dot_env_path)
            params = os.environ
        # Short flags
        elif opt in ['-l']:
            # sea discriminante del tipo de cargue
            execute_last = True
        elif opt in ['--param']:
            key = opt.replace('-', '')
            if key in params:
                logger.info(f"Overwriting property: '{key}'")
            params[key] = arg

    # Si no se especifica secreto de conexion se interrumpe la ejecucion
    if secret is None:
        logger.info("You must specify the secret in order to connect database")
        sys.exit(2)

    # Se valida el schema suministrado dentro del archivo run-description.yaml
    try:
        run_description_data = read_run_description_file()
    except (FileNotFoundError, ValidationError) as e:
        sys.exit(2)

    if execute_last == False:
        if len(filters) == 0:
            raise AttributeError(
                'Filters are specified as follows --filter "name=value"')

    try:
        CONNECTION = psycopg2.connect(**secret)
    except psycopg2.Error as e:
        logger.exception(
            "An error ocurred while connecting to the database " + str(e))
        sys.exit(2)

    working_directory = os.getcwd()

    init(
        connection=CONNECTION,
        working_directory=working_directory,
        filters=filters,
        run_description_data=run_description_data,
        params=params,
        execute_last=execute_last
    )

    logger.info('The work was finished succesfully')

    CONNECTION.close()


def init(
    connection,
    working_directory: str,
    filters: list,
    run_description_data: dict = None,
    params: dict = None,
    execute_last: bool = False
):
    directories = run_description_data['directories']

    run = run_description_data['run']

    if(execute_last):
        executions = [list(run.items())[-1]]
    else:
        executions = list(
            filter(
                lambda x: validate_filters(filters, x) == True,
                run.items()
            )
        )

    for execution in executions:
        for directories_key, directories_values in directories.items():
            folders = directories_values["childs"]
            for folder in folders:
                #logger.info(f'Searching in folder {folder}')
                try:
                    SEPARATOR = "\\" if platform.platform() == "Windows" else "/"

                    scripts = list(
                        map(
                            lambda e:
                            f'{working_directory}{SEPARATOR}{directories_key}{SEPARATOR}{folder}{SEPARATOR}{e}',
                            run[execution[0]][directories_key][folder]
                        )
                    )
                except KeyError as e:
                    scripts = []
                    logger.error(
                        f"""The key {str(e)} has not been defined inside '{execution[0]}' at the level of 'run'""")

                start_execution(
                    connection=connection,
                    schema=directories_values['schema'],
                    script_paths=scripts,
                    params=params,
                )

                logger.info(
                    '_________________________________________________')


def validate_filters(
    filters: list,
    execution: dict
):
    valid = False
    for filter in filters:
        regex = re.search(r"([A-Za-z0-9]+)=([A-Za-z0-9]+)", filter)
        try:
            prop_name = regex.group(1).strip()
        except AttributeError:
            logger.error(
                'Filters must be specified in the following way: "property=value"')
            sys.exit()
        value = regex.group(2).strip()
        try:
            if execution[1][prop_name] == value:
                valid = True
            else:
                valid = False
        except KeyError as e:
            logger.error(
                f'All elements inside run must contain the property to filter {str(e)}')
            break

    return valid


def start_execution(
    connection,
    schema: str,
    script_paths: list,
    params: dict = None,
):
    change_schema(connection=connection, schema=schema)

    for script_path in script_paths:
        read_content_script(
            connection=connection,
            file=script_path,
            params=params
        )


if __name__ == "__main__":
    main()