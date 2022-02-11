# Conexión a postgres
import psycopg2
# Leer archivos
import yaml
import psycopg2.sql as sql
# Leer el secret en formato Json
import logging
# Validation yaml
from jsonschema import validate, ValidationError

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def execute_query(
    connection, sql: str, params: dict = None
):
    try:
        cur = connection.cursor()
        cur.execute(sql, params)
        logger.info('The script was succesfully executed')
    except psycopg2.Error as e:
        logger.error('An exception ocurred while executing script: ' + str(e))
        raise e


def change_schema(connection, schema: str):
    try:
        connection.cursor().execute(
            sql.SQL("SET search_path TO {schema};").format(
                schema=sql.Identifier(schema)
            )
        )
    except psycopg2.Error as e:
        logger.error('An exception ocurred changing schema: ' + str(e))
        raise e

def read_content_script(
    connection,
    file: str, params=None
):
    try:
        with open(file, 'r') as myfile:
            query = myfile.read()
            logger.info(f'Executing script {myfile.name}')
            execute_query(connection, query, params)
    except FileNotFoundError as e:
        logger.error(
            'El directorio de ejecucion debe contener el archivo run-description.yaml')
        raise e


def read_run_description_file() -> dict:
    try:
        file = open('run-description.yml')
        schema = {
            # "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "Schema for execution scripts",
            "type": "object",
            "properties": {
                "directories": {
                    "type": "object",
                    "properties": {
                        "patternProperties": {
                            "^.*$": {
                                "type": "object",
                                "properties": {
                                    "schema": {"type": "string"},
                                    "childs": {"type": "array"}
                                }
                            }
                        },
                    },
                },
                "run": {
                    "type": "object"
                },
            },
            "required": [
                "directories",
                "run"
            ]
        }
        data = yaml.load(file, Loader=yaml.FullLoader)
        r = validate(data, schema)
        return data
    except FileNotFoundError as e:
        logger.error(
            'El directorio de ejecucion debe contener el archivo run-description.yaml')
        raise e
    except ValidationError as e:
        logger.error(
            'La estructura suministrada en run-description.yaml no es valida: ' + str(e))
        raise e
