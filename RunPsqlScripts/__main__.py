# binaries
from getopt import getopt
import sys
import re
import os
import platform
from dotenv import load_dotenv
# custom
from RunPsqlScripts.RunPsqlScripts import change_schema, psycopg2, read_run_description_file, logger, ValidationError, read_content_script, colored


def main():
    # Se obtienen los argumentos proporcionados en el comando
    argv = sys.argv[1:]

    # Variables nulas de ejecucion
    secret = None
    run_description_data = None

    # Variables por defecto
    dot_env_path = None

    # executio variables
    execute_last = False
    execute_all = False

    force = False

    params = {}
    filters = {}

    # se hace uso del modulo get opt para mandejar los argumentos pasados al script
    try:
        opts, args = getopt(
            argv,
            shortopts='laf',
            longopts=[
                "param=",
                "secret=",
                "filter=",
                "dot-env-path="
            ]
        )
    except Exception as e:
        logger.info(colored('An exception ocurred: ' + str(e), 'red'))
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
                    colored(
                        f'Se ha suministrado un formato incorrecto para la propiedad secret (revisar la documentacion) str({e})',
                        'red'
                    )
                )
                sys.exit()

        elif opt in ['--filter']:
            regex = re.search(r"([A-Za-z0-9]+)=([A-Za-z0-9]+)", arg)
            try:
                prop_name = regex.group(1).strip()
                value = regex.group(2).strip()
                # logger.info(
                #     colored(f'filtering by: {prop_name} = {value}', 'yellow')
                # )
                if (prop_name in filters):
                    logger.info(
                        colored(f'Overwritting property to filter: {prop_name} ({filters[prop_name]} -> {value})', 'magenta'))
                filters[prop_name] = value
            except AttributeError:
                logger.error(
                    'Filters must be specified in the following way: "property=value"')
                sys.exit()
        elif opt in ['--dot-env-path']:
            dot_env_path = arg
            logger.info(
                colored(f'Getting .env data from : {dot_env_path}', 'yellow')
            )
            load_dotenv()
            params = os.environ
        # Short flags
        elif opt in ['-l']:
            # sea discriminante del tipo de cargue
            execute_last = True
        elif opt in ['-a']:
            execute_all = True
        elif opt in ['-f']:
            force = True
        elif opt in ['--param']:
            regex = re.search(r"([A-Za-z0-9]+)=([A-Za-z0-9]+)", arg)
            try:
                key = regex.group(1).strip()
                value = regex.group(2).strip()
                if key in params:
                    logger.info(
                        colored(f"Overwriting param: '{key}'", 'magenta'))
                params[key] = value
            except AttributeError:
                logger.error(
                    colored(
                        f'Params must be specified in the following way: "param=value"',
                        'red'
                    )
                )
                sys.exit()

    # Si no se especifica secreto de conexion se interrumpe la ejecucion
    if secret is None:
        logger.error(
            colored("You must specify the secret in order to connect database", 'red'))
        sys.exit(2)

    # Se valida el schema suministrado dentro del archivo run-description.yaml
    try:
        run_description_data = read_run_description_file()
    except (FileNotFoundError, ValidationError) as e:
        sys.exit(2)

    if execute_last == False and execute_all == False:
        if len(filters) == 0:
            raise AttributeError(
                'Filters are specified as follows --filter "name=value"')
    elif execute_all == True and not force:
        raise Exception("Please use -f to force execution of all elements inside run")

    try:
        CONNECTION = psycopg2.connect(**secret)
    except psycopg2.Error as e:
        logger.exception(
            colored(
                "An error ocurred while connecting to the database " + str(e), 'red')
        )
        sys.exit(2)

    working_directory = os.getcwd()

    init(
        connection=CONNECTION,
        working_directory=working_directory,
        filters=filters,
        run_description_data=run_description_data,
        params=params,
        execute_last=execute_last,
        execute_all= execute_all
    )

    logger.info(colored('The work was finished succesfully', 'green'))

    CONNECTION.close()


def filterDict(mainDicts, filterDict):
    # return [x for x in mainDicts if not filterDict.items() - x[1].items()]
    dict = {}
    for x, y in mainDicts.items():
        if all(k in y and y[k] == v for k, v in filterDict.items()):
            dict[x] = y
    return dict


def init(
    connection,
    working_directory: str,
    filters: dict,
    run_description_data: dict = None,
    params: dict = None,
    execute_last: bool = False,
    execute_all: bool = False
):
    directories = run_description_data['directories']

    run = run_description_data['run']

    if(execute_last and not bool(filters)):
        key = list(run.keys())[-1]
        executions = {key: run[key]}
    elif (execute_all == True):
        executions = run    
    else:
        executions = filterDict(run, filters)
        if(execute_last):
            key = list(executions.keys())[-1]
            executions = {key: run[key]}

    for exec_key, exec_value in executions.items():

        logger.info(colored('Iterating over: ' + exec_key, 'yellow'))
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
                            run[exec_key][directories_key][folder]
                        )
                    )
                except KeyError as e:
                    scripts = []
                    # logger.info(
                    #     colored(
                    #         f"""The key {str(e)} has not been defined inside '{exec_key}' at the level of 'run'""",
                    #         'yellow'
                    #     )
                    # )
                else:
                    try:
                        change_schema(
                            connection=connection,
                            schema=directories_values['schema']
                        )
                    except:
                        logger.info(
                            colored(
                                f"""no schema specified, queries will be executed within public schema""",
                                'yellow'
                            )
                        )

                    start_execution(
                        connection=connection,
                        script_paths=scripts,
                        params=params,
                    )


def start_execution(
    connection,
    script_paths: list,
    params: dict = None,
):

    for script_path in script_paths:
        read_content_script(
            connection=connection,
            file=script_path,
            params=params
        )


if __name__ == "__main__":
    main()
