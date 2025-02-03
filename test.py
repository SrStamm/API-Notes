from passlib.context import CryptContext
import 

# Contexto de encriptacion 
crypt = CryptContext(schemes=["bcrypt"])

# Funcion que encripta la contraseña
def encrypt_password(password : str):
    password = password.encode()
    bash_password = crypt.hash(secret=password, scheme="bcrypt")    
    return print(bash_password)

f = encrypt_password("123456789")

print(f)