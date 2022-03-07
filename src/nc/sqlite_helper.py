import json
import sqlite3
import os
from tkinter import filedialog


class SQL_helper:
    db = "database.db"

    file = filedialog.askopenfilename()
    target_directory = filedialog.askdirectory()
    backend = f"{target_directory}/backend"
    os.mkdir(f"{target_directory}/backend")

    @classmethod
    def create_tables(self):
        with open(self.file, mode="r") as jsonfile:
            sql_dict: dict = json.load(jsonfile)
        with sqlite3.connect(self.db) as database:
            cursor = database.cursor()
            for table, table_prop in sql_dict.items():
                fields = table_prop.get("fields")
                fields = [f"{field.replace('::', ' ')}" for field in fields]
                fields = ",".join(fields)
                sql = f"CREATE TABLE IF NOT EXISTS {table}({fields})"
                print(sql)
                cursor.execute(sql)
                database.commit()

    @classmethod
    def create_models(self):

        with open("db_connection.py", mode="w") as conn_file:
            conn_file.write(
                """import sqlite3

class DB_Connection():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()"""
            )

        with open(self.file, mode="r") as jsonfile:
            sql_dict: dict = json.load(jsonfile)
            tables = list(sql_dict.keys())
            for table in tables:
                relations = sql_dict.get(table).get("relations")
                relates = sql_dict.get(table).get("relates")
                if relates:
                    t1, t2 = relates.split(">>")
                fields = sql_dict.get(table).get("fields")
                types = [field.split("::")[1] for field in fields]
                fields = [field.split("::")[0] for field in fields]
                fields_parameter = [
                    f"{field}=None" for field in fields if field != "id"
                ]
                fields_parameter = ",".join(fields_parameter)
                fields_select_parameter = [f"{field}=None" for field in fields]
                fields_select_parameter = ",".join(fields_select_parameter)

                model = f"""
from .db_connection import DB_Connection
from .pool import Pool"""
                if relates:
                    model = f"""{model}
from {t1} import {t1}
from {t2} import {t2}"""

                model = f"""{model}
class {table}(DB_Connection):
    fields = {fields}

    class {table}_object():
        '''You can add customized sql call in this class'''
        def __init__(self, cursor,{fields_select_parameter}):
            self.cursor = cursor
            self.id = None"""

                for parameter in fields:
                    model = f"""{model}
            self.{parameter} = {parameter}"""

                # ---

                if relations:
                    for relation in relations:
                        tab, relation_table = relation.split(">>")
                        model = f"""{model}

            
        def get_{tab}(self):
            sql = 'SELECT {tab}_id FROM {relation_table} WHERE {table}_id = '+str(self.id)
            print(sql)
            self.cursor.execute(sql)
            print(self.cursor.fetchall())"""

                model = f"""{model}

    child_class = {table}_object
    
    @classmethod
    def insert(self, {fields_parameter}):
        sql = 'INSERT INTO {table} ('
        values = []"""

                # ---

                for field, field_type in zip(fields, types):
                    if field != "id":
                        if "integer" in field_type or "real" in field_type:
                            model = f"""{model}
                            
        if {field}:
            sql = sql+f'{field},'
            values.append(str({field}))"""

                        # ---

                        else:
                            model = f"""{model}
        
        if {field}:
            sql = sql+f'{field},'
            value = ""+"'"+{field}+"'"
            values.append(value)"""

                        # ---

                model = f"""{model}
        
        values = ','.join(values)
        sql = sql[:len(sql)-1]+') VALUES ('+values+')'
        print(sql)
        self.cursor.execute(sql)
        self.connection.commit()
        
    @classmethod
    def select(self, {fields_select_parameter}):
        sql = 'SELECT * FROM {table} WHERE '
        conditions = []"""

                if "id" in fields:
                    model = f"""{model}
                    
        if id:
            sql = sql+'id='+str(id)
            
        else:"""
                else:
                    model = f"""{model}
        
        if True:"""

                for field, field_type in zip(fields, types):
                    if field != "id":
                        if "integer" in field_type or "real" in field_type:
                            model = f"""{model}
            if {field}:
                conditions.append('{field}='+str({field}))"""
                        else:
                            model = f"""{model}
            if {field}:
                conditions.append('{field}='+"'"+{field}+"'")"""

                model = f"""{model}
                
            conditions = ' AND '.join(conditions)
            sql = sql+conditions
        print(sql)
        self.cursor.execute(sql)
        objects = self.cursor.fetchall()
        children = []
        for obj in objects:
            children.append(self.child_class(self.cursor, *obj))
        return children"""

                if relates:
                    t1, t2 = relates.split(">>")
                    model = f"""{model}
    @classmethod
    def get_{t1}_from_{t2}_id(self, {t2}_id):
        sql = 'SELECT * FROM {table} WHERE {t2}_id='
        sql = sql+str({t2}_id)
        print(sql)
        self.cursor.execute(sql)
        objects = self.cursor.fetchall()
        print(objects)
        objects = [{t1}.select(id=obj[0]) for obj in objects]
        return objects 
        """

                with open(f"{table}.py", mode="w") as testfile:
                    testfile.write(model)

    @classmethod
    def create_pool(self):
        with open(self.file, mode="r") as jsonfile:
            sql_dict: dict = json.load(jsonfile)
            tables = list(sql_dict.keys())
            pool = """
            
class Pool():"""
            for table in tables:
                relations = sql_dict.get(table).get("relations")
                relates = sql_dict.get(table).get("relates")
                if relates:
                    t1, t2 = relates.split(">>")
                fields = sql_dict.get(table).get("fields")
                types = [field.split("::")[1] for field in fields]
                fields = [field.split("::")[0] for field in fields]
                fields_parameter = [
                    f"{field} = None" for field in fields if field != "id"
                ]
                fields_parameter = ",".join(fields_parameter)
                fields_select_parameter = [f"{field}=None" for field in fields]
                fields_select_parameter = ",".join(fields_select_parameter)

                pool = f"""{pool}

    #-- {table.upper()} --#

    class {table}_object():
        '''You can add customized sql call in this class'''
        def __init__(self, cursor, {fields_select_parameter}):
            self.cursor = cursor
            self.nome = None
            self.id = None"""

                for parameter in fields:
                    pool = f"""{pool}
            self.{parameter} = {parameter}"""

                pool = f"""{pool}
                

        def __str__(self):
            if self.nome:
                return self.nome
            elif self.id:
                return "Nome non disponibile, ID="+str(self.id)
            else:
                return "Nome o ID non disponibili."
        
        def __repr__(self):
            if self.nome:
                return self.nome
            elif self.id:
                return "Nome non disponibile, ID="+str(self.id)
            else:
                return "Nome o ID non disponibili."
        
        def update(self, {fields_parameter}):
            sql = 'UPDATE {table} SET '
            parameters = []"""

                for parameter in fields:
                    if parameter != "id":
                        pool = f"""{pool}
                
            if {parameter}:
                parameters.append('{parameter}='+"'"+str({parameter})+"'")
                self.{parameter} = {parameter}"""

                pool = f"""{pool}
            
            parameters = ",".join(parameters)
            sql = sql+parameters+' WHERE id = '+str(self.id)
            print(sql)
            self.cursor.execute(sql)
            self.cursor.connection.commit()"""

                if relations:
                    for relation in relations:
                        tab, relation_table = relation.split(">>")
                        pool = f"""{pool}

        
        def get_{tab}_objects(self):
            sql = 'SELECT {tab}_id FROM {relation_table} WHERE {table}_id = '+str(self.id)
            print(sql)
            self.cursor.execute(sql)
            objects = self.cursor.fetchall()
            ids = [obj[0] for obj in objects]
            {tab}_objects = []
            for id in ids:
                sql2 = 'SELECT * FROM {tab} WHERE id='+str(id)
                print(sql2)
                self.cursor.execute(sql2)
                values = self.cursor.fetchall()[0]
                {tab}_objects.append(Pool.{tab}_object(self.cursor, *values))
            
            return {tab}_objects"""

                with open("pool.py", mode="w") as poolfile:
                    poolfile.write(pool)

    @classmethod
    def create_models2(self):
        os.chdir(self.backend)
        os.system("touch __init__.py")
        with open("db_connection.py", mode="w") as conn_file:
            conn_file.write(
                """import sqlite3

class DB_Connection():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()"""
            )

        with open(self.file, mode="r") as jsonfile:
            sql_dict: dict = json.load(jsonfile)
            tables = list(sql_dict.keys())
            for table in tables:
                relations = sql_dict.get(table).get("relations")
                relates = sql_dict.get(table).get("relates")
                if relates:
                    t1, t2 = relates.split(">>")
                fields = sql_dict.get(table).get("fields")
                types = [field.split("::")[1] for field in fields]
                fields = [field.split("::")[0] for field in fields]
                fields_parameter = [
                    f"{field}=None" for field in fields if field != "id"
                ]
                fields_parameter = ",".join(fields_parameter)
                fields_select_parameter = [f"{field}=None" for field in fields]
                fields_select_parameter = ",".join(fields_select_parameter)

                model = f"""from .db_connection import DB_Connection
from .pool import Pool"""

                if relates:
                    model = f"""{model}
from .{t1} import {t1}
from .{t2} import {t2}"""

                model = f"""{model}
class {table}(DB_Connection):
    fields = {fields}
    child_class = Pool.{table}_object
    
    @classmethod
    def insert(self, {fields_parameter}):
        sql = 'INSERT INTO {table} ('
        values = []"""

                # ---

                for field, field_type in zip(fields, types):
                    if field != "id":
                        if "integer" in field_type or "real" in field_type:
                            model = f"""{model}
                            
        if {field}:
            sql = sql+f'{field},'
            values.append(str({field}))"""

                        # ---

                        else:
                            model = f"""{model}
        
        if {field}:
            sql = sql+f'{field},'
            value = ""+"'"+{field}+"'"
            values.append(value)"""

                        # ---

                model = f"""{model}
        
        values = ','.join(values)
        sql = sql[:len(sql)-1]+') VALUES ('+values+')'
        print(sql)
        self.cursor.execute(sql)
        self.connection.commit()
        
    @classmethod
    def select(self, {fields_select_parameter}):
        sql = 'SELECT * FROM {table} WHERE '
        conditions = []"""

                if "id" in fields:
                    model = f"""{model}
                    
        if id:
            sql = sql+'id='+str(id)
            
        else:"""
                else:
                    model = f"""{model}
        
        if True:"""

                for field, field_type in zip(fields, types):
                    if field != "id":
                        if "integer" in field_type or "real" in field_type:
                            model = f"""{model}
            if {field}:
                conditions.append('{field}='+str({field}))"""
                        else:
                            model = f"""{model}
            if {field}:
                conditions.append('{field}='+"'"+{field}+"'")"""

                model = f"""{model}
                
            conditions = ' AND '.join(conditions)
            sql = sql+conditions
        print(sql)
        self.cursor.execute(sql)
        objects = self.cursor.fetchall()
        children = []
        for obj in objects:
            children.append(self.child_class(self.cursor, *obj))
        return children"""

                with open(f"{table}.py", mode="w") as testfile:
                    testfile.write(model)
