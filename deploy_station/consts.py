"""
駅データ.jpクローリングスクリプト用定数配置モジュール
"""
from urllib.parse import urljoin

WAIT_TIME = 1

CSV_STATION = "../station_data/station.csv"
HEADERS = ['line_cd', 'station_cd', 'line_name', 'line_name_roman', 'station_name', 'station_name_roman', 'lat', 'lon']

BASE_URL = "https://www.ekidata.jp/"
DL_PAGE_URL = urljoin(BASE_URL, "dl/?p=1")  # ダウンロードURL記載ページ
DL_URL = "dl"

LOGIN_INFO = {
    'login': '1',
    'p': '0',
    'ac': '',
    'ps': ''
}  # ログインに必要な情報
