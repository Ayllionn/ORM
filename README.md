# ORM SQLITE

permet de faire simplement de la base de donnée SQL

exemple :
```pyton
from ORM import ORM, ID, DateTimeNow

orm = ORM(name="test", path="./ORM") #création de l'ORM et connection a la Base de Données

#création d'une table avec un modèle
@orm.Model
class Test:
    #il est possible d'ajouté la ligne `id = ID` cela provoquerai le fait que l'id doit être ajouté manuellement quand nous entrons une donnée
    name = str
    test_list = list

    create_at = DateTimeNow #pour les date rien n'est pris en charge concrétement c est juste pour anticipé les mise a jour et aussi évité l'import de datetime dans le code why not hein

#permet de get un object corréspondant a votre model qui comprend les méthode de gestion de la table (comme tout les autre object renvoyé par la table)
test_instance = orm.get_table("Test")

data1 = test_instance.create(
    name="Maurice",
    test_list=["Cath", 18, "Gab", 14],
    create_at=DateTimeNow.get_str()
)
#simulation d'un ajout dynamique
data2 = test_instance.create(
    **{
        "name":"Gab",
        "test_list":["18.26", 18.24],
        "create_at":DateTimeNow.get_str()
    }
)
#nous allons simmulé le fait que data2 était deja dans la db et que nous n'avons que sont id
data2 = data2.id

#get une donné grace a son id
data2 = test_instance.get(data2)
print("OBJ 1 :::\n")
print(
    f"""{data1.name} ({data1.id}) :
    \t{data1.test_list}
    \t{data1.create_at}
"""
)

print("OBJ 2 :::\n")
for i in data2.attr():
    print(i+" :", getattr(data2, i))
```
