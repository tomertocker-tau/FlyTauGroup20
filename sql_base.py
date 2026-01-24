from contextlib import contextmanager
import mysql.connector
from typing import Union, Dict, List, Tuple, Any

@contextmanager
def db_cur():
    '''

    :return: database cursor
    '''
    mydb = None
    cursor = None
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="flytau",
            autocommit=True
        )
        cursor = mydb.cursor(dictionary=True, buffered=True)
        yield cursor
    except mysql.connector.Error as err:
        raise err
    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()

def insert(table_name: str, data: Dict[str,Any]):
    '''
    execute sql command INSERT
    :param table_name: name of the table we want to insert to
    :param data: key=column name, value=value in that column
    :return:
    '''
    with db_cur() as cursor:
        keys = [k for k in data.keys()]
        cursor.execute(f"INSERT INTO {table_name} ({', '.join(keys)}) "
                     f"VALUES({', '.join([str(data[k]) for k in keys])})")

def delete(table_name: str, where: str):
    '''
    execute sql command DELETE
    :param table_name: name of the table we want to delete from
    :param where: condition on rows we want to delete
    :return:
    '''
    with db_cur() as cursor:
        cursor.execute(f"DELETE FROM {table_name} WHERE {where}")

def update(table_name: str, data: Dict[str,str], where: str = None):
    with db_cur() as cursor:
        new_values_str_line = ', '.join(['='.join([k,v]) for k,v in data.items()])
        if where:
            cursor.execute(f"UPDATE {table_name} "
                           f"SET {new_values_str_line} "
                           f"WHERE {where}")
        else:
            cursor.execute(f"UPDATE {table_name} SET {new_values_str_line}")

def select(table_name: str,
           columns: List[str] = None,
           where: str =None,
           group_by:List[str]=None,
           having: str = None,
           cases: Dict[str,str]=None,
           join: Tuple[str, List[str]]=None,
           side_join: str=None,
           order_by: List[str] = None,
           order_type: str = ""):
    '''
    execute sql command SELECT
    :param table_name: name of the table we want to select from
    :param columns: columns we want to select (defaults to all columns)
    :param where: like WHERE in sql, condition on rows we want to select (defaults to no condition)
    :param group_by: like GROUP BY in sql, list of columns we want to group by (defaults to no group by)
    :param having: like HAVING in sql, condition on group_by (defaults to no condition)
    :param cases: like CASE in sql, column generated value depends on the case. key=condition, value=value if condition is true.
                    must include key "AS" which the value decides the name of the generated column.
                    if include key "ELSE" cases["ELSE"] gives the value if none of the conditions are followed
    :param join: like JOIN in sql, tuple of (table_name2, columns2) where table_name2 is the table to join
                    and columns2 is the list of columns to join on (defaults to no join)
    :param side_join: kind of join (RIGHT/LEFT/INNER). defaults to regular join
    :param order_by: like ORDER BY in sql, list of columns we want to order by them (defaults to no order by)
    :param order_type: kind of order_by (ASC/DESC). defaults to ASC (regular ORDER BY)
    :return: list of dictionaries. each dictionary represents one row in the table,
                each key represents column name, and each value represents value on that column.
    '''
    with db_cur() as cursor:
        query = get_select_query(table_name, columns, where, group_by, having, cases, join, side_join, order_by, order_type)
        cursor.execute(query)
    return cursor.fetchall()

def get_select_query(table_name: str,
                     columns: List[str] = None,
                     where: str =None,
                     group_by:List[str]=None,
                     having: str=None,
                     cases: Dict[str,str]=None,
                     join : Tuple[str,List[str]] = None,
                     side_join: str = "",
                     order_by: List[str] = None,
                     order_type: str = ""):
    '''
        :param table_name: name of the table we want to select from
        :param columns: columns we want to select (defaults to all columns)
        :param where: like WHERE in sql, condition on rows we want to select (defaults to no condition)
        :param group_by: like GROUP BY in sql, list of columns we want to group by (defaults to no group by)
        :param having: like HAVING in sql, condition on group_by (defaults to no condition)
        :param cases: like CASE in sql, column generated value depends on the case. key=condition, value=value if condition is true.
                        must include key "AS" which the value decides the name of the generated column.
                        if include key "ELSE" cases["ELSE"] gives the value if none of the conditions are followed
        :param join: like JOIN in sql, tuple of (table_name2, columns2) where table_name2 is the table to join
                        and columns2 is the list of columns to join on (defaults to no join)
        :param side_join: kind of join (RIGHT/LEFT/INNER). defaults to regular join
        :param order_by: like ORDER BY in sql, list of columns we want to order by them (defaults to no order by)
        :param order_type: kind of order_by (ASC/DESC). defaults to ASC (regular ORDER BY)
        :return: string of a fitting sql command
        '''
    if not columns:
        query = "SELECT "
        if cases:
            query += " CASE"
            for k, v in cases.items():
                if k in ["ELSE","AS"]:
                    continue
                query += f" WHEN {k} THEN {v}"
            elsecase = cases.get("ELSE")
            if elsecase:
                query += f" ELSE {elsecase}"
            query += f" END AS {cases['AS']}"
        else:
            query+= "*"
        query += f" FROM {table_name}"

    else:
        query = f"SELECT {', '.join(columns)}"
        if cases:
            query += ", CASE"
            for k, v in cases.items():
                if k in ["ELSE","AS"]:
                    continue
                query += f" WHEN {k} THEN {v}"
            elsecase = cases.get("ELSE")
            if elsecase:
                query += f" ELSE {elsecase}"
            query += f" END AS {cases['AS']}"
        query += f" FROM {table_name}"
    if join:
        real_table_name1 = table_name.split()[-1]
        real_table_name2 = join[0].split()[-1]
        if side_join:
            pass
        else:
            side_join = ""

        query += f" {side_join} JOIN {join[0]} ON {real_table_name2}.{join[1][0]} = {real_table_name1}.{join[1][0]}"
        for column in join[1][1:]:
            query += f" AND {real_table_name2}.{column} = {real_table_name1}.{column}"
    if where:
        query += f" WHERE {where}"
    if group_by:
        query += f" GROUP BY {','.join(group_by)}"
        if having:
            query += f" HAVING {having}"
    if order_by:
        query += f" ORDER BY {', '.join(order_by)}"
        query += f" {order_type}"
    return query
