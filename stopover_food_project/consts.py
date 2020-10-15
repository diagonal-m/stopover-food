import environ

env = environ.Env()

env.read_env('.env')

KEY = env('KEY')
HOST = env('HOST')

