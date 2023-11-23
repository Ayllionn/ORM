import json
import traceback
import sqlite3
import datetime

"""
        class MODEL:
        -> Représente une donnée précise dans la table vous pouvez modifié l'objet et après le sauvegardé. Get un autre object qui appartient a la même table etc...
            def table(self):
            -> permet d'otbtenir la table de la base de données'

            create(self, **kwargs):
            -> permet de créer une nouvelle ligne dans la table

            get(self, id):
            -> permet de récupérer une ligne de la table

            delete(self):
            -> permet de supprimer une ligne de la table

            update(self):
            -> permet de mettre à jour une ligne de la table
"""



class DB:
    def __init__(self, path, name):
        self.db = sqlite3.connect(f"{path}/{name}.db")
        self.c = self.db.cursor()

    def convert_type(self, typ):
        if typ == int or typ == bool or typ == ID:
            return "INTEGER"
        elif typ == float:
            return "FLOAT"
        elif typ == str or typ == list or typ == dict or typ == tuple:
            return "TEXT"
        else:
            return "TEXT"

    def create_table(self, _name, **kwargs):
        self.c.execute(
            f"CREATE TABLE IF NOT EXISTS {_name} ("
            f"  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            f"  {','.join([f'{k} {self.convert_type(v)}' for k, v in kwargs.items()])}"
            f")"
        )

    def create_table_without_id(self, _name, **kwargs):
        self.c.execute(
            f"CREATE TABLE IF NOT EXISTS {_name} ("
            f"  {','.join([f'{k} {self.convert_type(v)}' for k, v in kwargs.items()])}"
            f")"
        )

    def get_all_by_table(self, table):
        self.c.execute(f"SELECT * FROM {table}")
        return self.c.fetchall()

    def get_one_by_id(self, table, value):
        self.c.execute(f"SELECT * FROM {table} WHERE id = ?", (value,))
        return self.c.fetchone()

    def create_data(self, table_name, **kwargs):
        serialized_data = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in kwargs.items()}

        columns = ', '.join(serialized_data.keys())
        values = ', '.join(['?' for _ in serialized_data.values()])

        self.c.execute(
            f"INSERT INTO {table_name} "
            f"({columns}) "
            f"VALUES ({values})",
            tuple(serialized_data.values())
        )
        self.db.commit()

        last_row_id = self.c.lastrowid

        return self.get_one_by_id(table_name, last_row_id)

    def delete_data(self, table_name, id):
        self.c.execute(f"DELETE FROM {table_name} WHERE id = ?", (id,))
        self.db.commit()

    def update_data(self, table_name, id_value, **kwargs):
        serialized_data = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in kwargs.items()}
        set_values = ', '.join([f"{key} = ?" for key in serialized_data.keys()])
        values = tuple(serialized_data.values())

        self.c.execute(f"UPDATE {table_name} SET {set_values} WHERE id = ?", (*values, id_value))
        self.db.commit()

"""
________________________________________________________________________________________________________________________
"""

class DateTimeNow:
    def set(self):
        return datetime.datetime.now()

    def get(self, *args):
        return f"{datetime.datetime.now().day}-{datetime.datetime.now().month}-{datetime.datetime.now().year} " \
               f"{datetime.datetime.now().hour}:{datetime.datetime.now().minute}:{datetime.datetime.now().second}"


class ID:
    pass


class ORM:
    def __init__(self, name:str, path="."):
        self._models = {}
        self.tables = []
        self.db = DB(path, name)

    def get_table(self, table_name:str):
        if table_name in self.tables:
            return self._models[table_name]()
        else:
            raise Exception(f"La table {table_name} n'existe pas")

    def get_all_by_table(self, table_name):
        return self.db.get_all_by_table(table_name)

    def get_value_by_id(self, table_name, id_value):
        return self._models[table_name](**{k: v for k, v in zip(self._models[table_name]()._collums_names,
                                                                 self.db.get_one_by_id(table_name, id_value))})

    def get_table_obj(self, table_name):
        return self._models.get(table_name)()

    def Model(self, obj):
        auto_id = False
        master_orm = self
        attributes = vars(obj)
        temp = {}
        collums_names = []

        for attr_name, attr_value in attributes.items():
            try:
                if attr_name.startswith("__"):
                    continue
                if attr_value not in [int, float, str, bool, dict, list, tuple, DateTimeNow, ID]:
                    raise ValueError("Votre modèle ne peut comprendre que des valeurs de type : [int, float, str, "
                                     "bool, dict, list, tuple, DateTimeNow, ID]")
                if attr_value == ID:
                    auto_id = True
                temp[attr_name] = attr_value
                collums_names.append(attr_name)
            except:
                traceback.print_exc()

        if auto_id is False:
            self.db.create_table(obj.__name__, **temp)
        else:
            self.db.create_table_without_id(obj.__name__, **temp)

        class MODEL:
            def __init__(self, *args, **kwargs):
                self._db = master_orm
                self._collums_names = collums_names.copy()
                self._table = obj.__name__
                self._auto_id = auto_id
                self._getted = False

                for attr_name, attr_value in kwargs.items():
                    self._getted = True
                    try:
                        setattr(self, attr_name, json.loads(attr_value))
                    except:
                        setattr(self, attr_name, attr_value)

                try:
                    self._collums_names.remove("id")
                except:
                    pass
                finally:
                    self._collums_names.insert(0, "id")

            def table(self):
                return self._table

            def create(self, **kwargs):
                collums_names = self._collums_names.copy()
                if not self._auto_id:
                    collums_names.remove("id")

                if len(kwargs.keys()) != len(collums_names):
                    raise ValueError(f"Suffisamment de valeurs (\n"
                                     f"\t{' / '.join([i for i in kwargs.keys()])},\n"
                                     f"\t{' / '.join(collums_names)}"
                                     f")")

                for k in kwargs.keys():
                    if k not in collums_names:
                        raise ValueError(f"{k} not in {self._collums_names}")

                return MODEL(**{k: v for k, v in zip(self._collums_names, self._db.db.create_data(table_name=self._table, **kwargs))})

            def get(self, id_value):
                try:
                    return MODEL(**{k: v for k, v in zip(self._collums_names, self._db.get_one_by_id(self._table, id_value))})
                except:
                    return None

            def delete(self):
                if self._getted:
                    self._db.db.delete_data(self._table, self.id)
                else:
                    raise ValueError("Object not getted")

            def update(self):
                if self._getted:
                    temp = {}
                    attr = vars(self)
                    for k, v in attr.items():
                        if k.startswith('_') or k.startswith('__'):
                            continue
                        else:
                            temp.update({k:v})
                    temp.pop("id", None)
                    self._db.db.update_data(self._table, self.id, **temp)
                else:
                    raise ValueError("Object not getted")

        self._models.update({obj.__name__: MODEL})
        self.tables.append(obj.__name__)
        return MODEL