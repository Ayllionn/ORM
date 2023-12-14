# ORM SQLITE

permet de faire simplement de la base de donnée SQL

exemple : (ceci est un text en console pour voir rapidement se que l'on peut faire après libre cours a l'imagination)
```python
import datetime

from lib import ORM

# Création d'une base de données et création de l'objet qui va la gérer
data = ORM('.', "test")

# Définition des schémas

# Schéma pour les messages
@data.schema
class Message:
    content = str
    author_id = int
    author_name = str
    create_at = str

    def __str__(self):
        return self.content

    def __int__(self):
        return self.id

# Schéma pour les utilisateurs
@data.schema
class User:
    name = str
    email = str
    password = str
    age = int
    messages = list

    # Méthode pour envoyer un message
    def send_message(self, content):
        msg = data.create_data(
            'Message',
            content=content,
            author_id=self.id,
            author_name=self.name,
            create_at=str(datetime.datetime.now())
        )
        self.messages.append(int(msg))
        self.save()
        return msg

    # Méthode pour récupérer les messages de l'utilisateur
    def get_messages(self):
        return data.get_by_collum('Message', 'author_id', self.id)

    def __str__(self):
        return self.name

    def __int__(self):
        return self.id

# Récupération de la table des utilisateurs
users = data.get_table('User')

# Fonction pour la saisie utilisateur avec vérification des options
def inputer(question: str, options: list, type, show_options: bool = True):
    options = [str(i) for i in options]
    if show_options:
        entry = input(question + f" [{'/'.join(options)}]\n>")
    else:
        entry = input(question)
    if entry not in options:
        print(f"{entry} is not a valid")
        return inputer(question, options, type, show_options)
    return type(entry)

# Interactions utilisateur pour créer un utilisateur et envoyer des messages
if inputer("Voulez-vous créer un utilisateur ?", ['o', 'n'], str) == "o":
    user = users.create(
        name=input("Your name: "),
        email=input("Your email address: "),
        password=input('Your password: '),
        age=inputer('Your age:', [i for i in range(150)], int, False),
        messages=[]
    )
    if inputer('Voulez-vous envoyer des messages ?', ['o', 'n'], str) == "o":
        while True:
            user.send_message(input('Content: '))
            if inputer('Voulez-vous en renvoyer un ?', ["o", "n"], str) == "n":
                break
else:
    # Affichage des informations sur tous les utilisateurs
    for i in users.get_all():
        print(i.name, ":")
        print('\t age:', i.age)
        print('\t mail:', i.email)
        print("\t messages:")
        [print("\t\t", i2.content) for i2 in i.get_messages()]
        print('')

```
