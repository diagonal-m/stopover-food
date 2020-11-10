"""
駅データ.jpクローリングスクリプト用定数配置モジュール
"""
import os
from urllib.parse import urljoin
import environ

BASE_DIR = environ.Path(__file__) - 2

env = environ.Env()

env.read_env(os.path.join(BASE_DIR, '.env'))
MECAB_NUM = int(env('MECAB_NUM'))  # 環境依存定数

WAIT_TIME = 1

CSV_STATION = "../station_data/station.csv"
HEADERS = ['line_cd', 'station_cd', 'line_name', 'line_name_roman', 'station_name', 'station_name_roman', 'lat', 'lon']

BASE_URL = "https://www.ekidata.jp/"
DL_PAGE_URL = urljoin(BASE_URL, "dl/?p=1")  # ダウンロードURL記載ページ
DL_URL = "dl"

LOGIN_INFO = {
    'login': '1',
    'p': '0',
    'ac': env('MAIL'),
    'ps': env('PW')
}  # ログインに必要な情報

DATABASE = {
    "dbname": env('DBNAME'),
    "host": env('DB_HOST'),
    "user": env('DB_USER'),
    "password": env('DB_PASSWORD'),
    "port": env('DB_PORT')
}
