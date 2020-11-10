import environ

env = environ.Env()

env.read_env('.env')

KEY = env('KEY')
HOST = env('HOST')

DATABASE = {
    "dbname": env('DBNAME'),
    "host": env('DB_HOST'),
    "user": env('DB_USER'),
    "password": env('DB_PASSWORD'),
    "port": env('DB_PORT')
}
