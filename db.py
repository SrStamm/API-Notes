from sqlmodel import Field, Session, SQLModel, create_engine, select, or_
from Models.db_models import Users, Tasks

sqlite_file_name = "C:\\Users\\Mirko Alexander\\Desktop\\Backend\\to-do\\DB\\database.sqlite"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True) # echo=True imprime todas las declaraciones SQL

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def create_users():
    user_1 = Users(username="mirko_dev", email="mirko@dev.com", age = 21, password="123456")
    user_2 = Users(username="moure_dev", email="moure@dev.com", age = 39, password="654321")
    user_3 = Users(username="dalto_dev", email="dalto@dev.com", age = 24, password="159753")

    # Se crea una sesion para interactuar con BD
    session = Session(engine)

    # Añade los datos a DB
    session.add(user_1)
    session.add(user_2)
    session.add(user_3)

    # Se guardan los cambios
    session.commit()


    print("Despues del commit, muestra IDs")
    print("Hero 1 ID:", user_1.id)
    print("Hero 2 ID:", user_2.id)
    print("Hero 3 ID:", user_3.id)

    print("Despues del commit, muestra names")
    print("Hero 1 name:", user_1.username)
    print("Hero 2 name:", user_2.username)
    print("Hero 3 name:", user_3.username)

    # Tambien se puede usar un objeto para refrescar los datos
    session.refresh(user_1)
    session.refresh(user_2)
    session.refresh(user_3)    

    # Se cierra la sesion
    session.close()

    # Otra forma de hacerlo es la siguiente:
    """
    with Session(engine) as session:
        session.add(hero_1)
        session.add(hero_2)
        session.add(hero_3)

        session.commit()

    """
    # De esta forma no importa si nos olvidamos de cerrar la sesion


def select_users():
    with Session(engine) as session:
        statement = select(Users.username, Users.age, Users.email).where(Users.age > 50)
        results = session.exec(statement)
        
        # Existen dos formas de mostrar los datos

        # Iterando la lista        
        for users in results:
            print(users)       
        
        # Devolviendo la lista completa
        users = results.all()
        print(users)

        # De esta forma se podria obtener el primer dato de BD
            # results.first()

        # Para obtener la informacion del usuario con id exacto
            #  session.get(<nombre_tabla>,<id>)
        
        # Para limitar la cantidad de resultados
            # select().limit(<cantidad>)

        # Para saltearte una cantidad de filas
            # select().offset(<cantidad>)


        with Session(engine) as session:
            user = session.get(Users, 1)
            print("Usuario: ", user)

        # forma resumida para executar:
        """
        results = session.exec(select(Users)).all()
        print(results)"""


def update_users():
    with Session(engine) as session:
        statement = select(Users).where(Users.username == "moure_dev")
        results = session.exec(statement)
        user = results.one()
        print(user)

        user.age = 80
        session.add(user)
        session.commit()
        session.refresh(user)
        print(user)


def create_tasks():
    with Session(engine) as session:
        task_1 = Tasks(text="Hola Mundo!")
        task_2 = Tasks(text="Hotel Trivago!")

        session.add(task_1)
        session.add(task_2)

        session.commit()


def read_tasks():
    with Session(engine) as session:
        statement = select(Tasks)
        results = session.exec(statement).all()
        print(results)


def main():
    create_db_and_tables()
    # create_users()
    select_users()
    update_users()
    # create_tasks()
    read_tasks()


if __name__ == "__main__":
    main()
