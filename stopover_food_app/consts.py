"""
定数配置モジュール
"""
import environ

env = environ.Env()

env.read_env('.env')

GURUNAVI_KEY = env('GURUNAVI_KEY')

MAX_WAIT_TIME = 10
WAIT_TIME = 0.5

