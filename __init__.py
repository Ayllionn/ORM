import json
import sqlite3
import types

class DB:
    def __init__(self, path, name):
        self.db = sqlite3.connect(f"{path}/{name}.db")
        self.c = self.db.cursor()

    def convert_type(self, typ):
        type_mapping = {
            int: "INTEGER",
            bool: "INTEGER",
            float: "REAL",
            str: "TEXT",
            list: "TEXT",
            dict: "TEXT",
        }
        if type_mapping.get(type(typ), "TEXT") is None:
            raise ValueError(f'{typ} not in [{" - ".join(type_mapping.keys())}]')
        return type_mapping.get(typ, "TEXT")

    def create_table(self, table_name, auto_increment=True, **columns):
        id_column = "id INTEGER PRIMARY KEY AUTOINCREMENT" if auto_increment else "id INTEGER"
        column_definitions = ', '.join(f'{name} {self.convert_type(typ)}' for name, typ in columns.items())
        self.c.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} ({id_column}, {column_definitions})"
        )

    def get_all_by_table(self, table):
        self.c.execute(f"SELECT * FROM {table}")
        return self.c.fetchall()

    def get_all_by_column(self, table, column, value):
        self.c.execute(f"SELECT * FROM {table} WHERE {column} = ?", (value,))
        return self.c.fetchall()

    def get_one_by_id(self, table, value):
        self.c.execute(f"SELECT * FROM {table} WHERE id = ?", (value,))
        return self.c.fetchone()

    def create_data(self, table_name, **data):
        serialized_data = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in data.items()}
        columns = ', '.join(serialized_data.keys())
        values = ', '.join(['?' for _ in serialized_data.values()])

        self.c.execute(
            f"INSERT INTO {table_name} ({columns}) VALUES ({values})",
            tuple(serialized_data.values())
        )
        self.db.commit()

        dt = self.get_one_by_id(table_name, self.c.lastrowid)
        if dt is None:
            dt = self.get_one_by_id(table_name, data.get("id"))
        return dt

    def delete_data(self, table_name, record_id):
        self.c.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
        self.db.commit()

    def update_data(self, table_name, record_id, **data):
        serialized_data = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in data.items()}
        set_values = ', '.join(f"{key} = ?" for key in serialized_data.keys())
        values = tuple(serialized_data.values())

        self.c.execute(f"UPDATE {table_name} SET {set_values} WHERE id = ?", (*values, record_id))
        self.db.commit()

"""
________________________________________________________________________________________________________________________
"""

valid_attr = [
    int, float,
    str,
    list, dict, tuple
]

class Object:
    def __init__(self, schema, orm, **kwargs):
        object.__setattr__(self, 'attr', [i for i in vars(schema) if i.startswith('_')
                                          is False and i.startswith('__')
                                          is False and getattr(schema, i) in valid_attr])

        object.__setattr__(self, '__orm', orm)
        object.__setattr__(self, '__table', schema.__name__)
        object.__setattr__(self, '__schema', schema)

        for k, v in kwargs.items():
            if vars(schema).get(k) is None:
                raise ValueError(
                    f"{k} n'existe pas dans [{'-'.join([i for i in vars(schema) if i.startswith('_') is False and i.startswith('__') is False])}]")
            elif getattr(schema, k) != type(v):
                try:
                    v = json.loads(v)
                except:
                    raise ValueError(
                        f'{k}:{v} : type {type(v)} != {getattr(schema, k)}'
                    )

            object.__setattr__(self, k, v)


        for func in dir(schema):
            if func.startswith("__") is False or func.startswith('_') is False:
                if callable(getattr(schema, func)) and func not in vars(self):
                    setattr(self, func, types.MethodType(getattr(schema, func), self))

    def get_table(self):
        return object.__getattribute__(self, '__table')

    def get(self, id):
        return object.__getattribute__(self, "__orm").get_by_id(object.__getattribute__(self, "__table"), id)

    def get_collumn(self, collumn, value):
        return self.__orm.get_by_collum(self.get_table(), collumn, value)

    def create(self, **kwargs):
        return object.__getattribute__(self, "__orm").create_data(object.__getattribute__(self, "__table"), **kwargs)

    def get_all(self, **kwargs):
        return object.__getattribute__(self, "__orm").get_all_by_table(object.__getattribute__(self, "__table"))

    def delete(self):
        object.__getattribute__(self, "__orm").db.delete_data(object.__getattribute__(self, "__table"), self.id)

    def save(self):
        object.__getattribute__(self, "__orm").db.update_data(object.__getattribute__(self, "__table"),
                                                              self.id,
                                                              **{k:v for k, v in zip(
                                                                  object.__getattribute__(self, "attr"),
                                                                  [object.__getattribute__(self, i) for i in object.__getattribute__(self, "attr")]
                                                              )})

    def __setattr__(self, key, value):
        if key in self.attr:
            if type(value) != object.__getattribute__(self.__getattribute__('__schema'), key):
                raise ValueError(f'{value} : type '
                                 f'{type(value)} != {object.__getattribute__(self.__getattribute__("__schema"), key)}')
            object.__getattribute__(self, "__orm").db.update_data(object.__getattribute__(self, "__table"), self.id, **{key:value})
        object.__setattr__(self, key, value)

    def __str__(self):
        return str({k:v for k,v in vars(self).items() if k.startswith('__') is False and k.startswith('_') is False and callable(v) is False})

    def __int__(self):
        return self.id

class Table:
    def __init__(self, orm, table):
        self.orm = orm
        self.table = table

    def get(self, id) -> Object:
        return self.orm.get_by_id(self.table, id)

    def get_collumn(self, collumn, value) -> Object:
        return self.orm.get_by_collum(self.table, collumn, value)

    def get_all(self) -> list[Object]:
        return self.orm.get_all_by_table(self.table)

    def create(self, **kwargs) -> object:
        return self.orm.create_data(self.table, **kwargs)

class ORM:
    def __init__(self, path, name):
        self.db = DB(path, name)
        self.tables = []
        self._objs = {}

    def schema(self, obj):
        self.tables.append(obj.__name__)
        attr = {k: v for k, v in vars(obj).items() if k.startswith("_") is False and v in valid_attr}
        if attr.get("id") is None:
            self.db.create_table(obj.__name__, auto_increment=True, **attr)
            attr = {"id":int, **attr}
            setattr(obj, "id", int)
        else:
            copy = attr.copy()
            copy.pop("id")
            self.db.create_table(obj.__name__, auto_increment=False, **copy)

        self._objs.update({
            obj.__name__: [
                obj, attr
            ]
        })

        return self.get_table(obj.__name__)

    def _mapper(self, table, data) -> Object:
        return Object(
            self._objs.get(table)[0], self, **{
                k: v for k, v in zip(self._objs.get(table)[1], data)
            }
        )

    def get_table(self, table) -> Table:
        if table not in self.tables:
            raise KeyError(table)

        return Table(self, table)

    def create_data(self, table, **kwargs) -> Object:
        data = self.db.create_data(table, **kwargs)
        return self._mapper(table, data)

    def get_by_id(self, table, id) -> Object:
        data = self.db.get_one_by_id(table, id)
        return self._mapper(table, data)

    def get_all_by_table(self, table) -> list[Object]:
        return [self._mapper(table, data) for data in self.db.get_all_by_table(table)]

    def get_by_collum(self, table, collumn, value) -> list[Object]:
        return [self._mapper(table, data) for data in self.db.get_all_by_column(table=table, column=collumn, value=value)]
