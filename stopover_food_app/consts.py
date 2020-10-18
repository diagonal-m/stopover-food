"""
定数配置モジュール
"""
import environ

env = environ.Env()

env.read_env('.env')

GURUNAVI_KEY = env('GURUNAVI_KEY')
MECAB_NUM = int(env('MECAB_NUM'))  # 環境依存定数

MAX_WAIT_TIME = 10
WAIT_TIME = 0.5

