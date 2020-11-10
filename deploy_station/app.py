"""
駅データ.jpから駅データと路線データをダウンロード→結合→ファイル出力するスクリプト
とりあえず手動定期実行
"""
from time import sleep
from tempfile import NamedTemporaryFile

import requests
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2

from functions import RomanaizeST
from consts import WAIT_TIME, CSV_STATION, HEADERS, BASE_URL, DL_PAGE_URL, DL_URL, LOGIN_INFO, DATABASE

from typing import Tuple


def login(url: str) -> requests.sessions.Session:
    """
    URLに対してPOSTのリクエストとログインに必要な情報を投げて、得られたsessionを返す
    ログイン状態はsessionで保持している

    @param url: URL e.g.) "https://www.ekidata.jp/dl/?p=1"
    @return: session(requests.sessions.Session)
    """
    session = requests.Session()
    res = session.post(url, data=LOGIN_INFO)
    sleep(WAIT_TIME)
    if res.status_code != 200:
        raise RuntimeError("ログインに失敗しました")

    return session


def get_soup(url: str, session: requests.sessions.Session) -> BeautifulSoup:
    """
    対象ページをクローリングし、soupの型で返す

    @param url: URL e.g.) "https://www.ekidata.jp/dl/?p=1"
    @param session: session(requests.sessions.Session)
    @return: BeautifulSoup
    """
    res = session.get(url)
    sleep(WAIT_TIME)
    soup = BeautifulSoup(res.content, "html.parser")
    return soup


def fetch_download_urls(soup: BeautifulSoup) -> Tuple[str, str]:
    """
    ダウンロードページのsoupを受け取り、「路線データ」と「駅データ」の最新CSVファイルの
    ダウンロードリンクを取得して返す関数

    @param soup: BeautifulSoup
    @return: (路線データダウンロードリンク, 駅データダウンロードリンク)
    """
    # 無料データダウンロードのテーブル
    table = soup.find('table', class_='list02')
    tr_list = table.find_all('tr')

    line_href = tr_list[3].find('a').attrs['href'][1:]  # e.g.)  '/f.php?t=3&d=20200619'
    station_href = tr_list[5].find('a').attrs['href'][1:]  # e.g.) '/f.php?t=5&d=20200619'

    line_dl_url = BASE_URL + DL_URL + line_href
    station_dl_url = BASE_URL + DL_URL + station_href

    return line_dl_url, station_dl_url


def dl_csv_file(file_path: str, dl_url: str, session: requests.sessions.Session) -> None:
    """
    file_pathにCSVファイルをダウンロードする

    @param file_path: DLするファイルのフルパス
    @param dl_url: ファイルダウンロードURL e.g.) "https://www.ekidata.jp/dl/f.php?t=5&d=20190405"
    @param session: session(requests.sessions.Session)
    """
    res = session.get(dl_url, stream=True)
    sleep(WAIT_TIME)

    if res.status_code != 200:
        raise RuntimeError("ダウンロードに失敗しました")

    with open(file_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=1024):
            f.write(chunk)


def validation_line(df: pd.DataFrame) -> None:
    """
    ダウンロードした路線データのCSVファイルの形式が想定外であったらRuntimeError

    @param df: 路線データのデータフレーム
    """
    expected_column_num = 13
    needed_headers = {'line_cd', 'line_name'}

    if not df.shape[1] == expected_column_num:
        raise RuntimeError(f"路線データの列数が{expected_column_num}ではありません")

    if not needed_headers.issubset(set(df.columns)):
        raise RuntimeError("路線データの路線番号、路線名の形式が変更されています")

    if df.empty:
        raise RuntimeError("路線データが空です")


def validation_station(df: pd.DataFrame) -> None:
    """
    ダウンロードした駅データのCSVファイルの形式が想定外であったらRuntimeError

    @param df: 駅データのデータフレーム
    """
    expected_column_num = 15
    needed_headers = {'station_name', 'line_cd', 'lon', 'lat', 'close_ymd'}

    if not df.shape[1] == expected_column_num:
        raise RuntimeError(f"路線データの列数が{expected_column_num}ではありません")

    if not needed_headers.issubset(set(df.columns)):
        raise RuntimeError("路線データの駅名、路線番号、緯度・経度、閉駅日時の形式が変更されています")

    if df.empty:
        raise RuntimeError("路線データが空です")


def preprocess_line(df: pd.DataFrame) -> pd.DataFrame:
    """
    路線データのデータフレームに対する前処理関数
    前処理済みデータフレームを返す

    @param df: 路線データのデータフレーム
    @return: 前処理済みデータフレーム
    """
    line_cd, line_name, line_name_roman = 'line_cd', 'line_name', 'line_name_roman'
    # 路線名の()内の文字列を削除する  e.g.) 'JR函館本線(函館～長万部)' → 'JR函館本線'
    df[line_name] = df[line_name].str.replace(r'\(.+?\)', '', regex=True)

    line_names = df[line_name].to_list()
    rs = RomanaizeST()
    df[line_name_roman] = [rs.romanaize(line)[0].replace("'", "") for line in line_names]

    return df[[line_cd, line_name, line_name_roman]]


def preprocess_station(df: pd.DataFrame) -> pd.DataFrame:
    """
    駅データのデータフレームに対する前処理関数
    前処理済みデータフレームを返す

    @param df: 駅データのデータフレーム
    @return: 前処理済みデータフレーム
    """
    roman = 'station_name_roman'
    headers = ['station_cd', 'station_name', roman, 'line_cd', 'lon', 'lat']

    # 閉駅済みの駅を削除
    df = df[df.close_ymd == '0000-00-00']

    station_names = df['station_name'].to_list()
    rs = RomanaizeST()
    df[roman] = [rs.romanaize(station)[0].replace("'", "") for station in station_names]

    return df[headers]


def create_table(df: pd.DataFrame) -> None:
    """
    前処理済みのデータフレームを元にテーブルを作成する

    @param df: 前処理済みのデータフレーム
    """
    table_name = 'station_info'

    with psycopg2.connect(**DATABASE) as conn:
        cur = conn.cursor()
        drop_sql = "DROP TABLE IF EXISTS {};"
        create_sql = """
            CREATE TABLE {} (
                index INTEGER,
                line_cd  INTEGER,
                station_cd  INTEGER,
                line_name  VARCHAR (250),
                line_name_roman VARCHAR (250),
                station_name VARCHAR (250),
                station_name_roman VARCHAR (250),
                lat NUMERIC,
                lon NUMERIC
            );
            """
        cur.execute(drop_sql.format(table_name))
        cur.execute(create_sql.format(table_name))
    with psycopg2.connect(**DATABASE) as conn:
        cur = conn.cursor()
        sql = "INSERT INTO {} VALUES {}"
        for line in df.itertuples():
            cur.execute(sql.format(table_name, tuple(line)))


def main():
    """
    メインスクリプト
    """
    session = login(DL_PAGE_URL)
    soup = get_soup(DL_PAGE_URL, session)

    line_dl_link, station_dl_link = fetch_download_urls(soup)

    # CSVファイルのダウンロード
    tmpfile_line = NamedTemporaryFile()
    tmpfile_station = NamedTemporaryFile()
    dl_csv_file(tmpfile_line.name, line_dl_link, session)
    dl_csv_file(tmpfile_station.name, station_dl_link, session)

    # データフレームとして読み込む
    line_df = pd.read_csv(tmpfile_line.name)
    station_df = pd.read_csv(tmpfile_station.name)

    # バリデーション
    validation_line(line_df)
    validation_station(station_df)

    # 前処理
    line_df = preprocess_line(line_df)
    station_df = preprocess_station(station_df)

    # line_cdをキーに結合
    line_station = pd.merge(station_df, line_df, on='line_cd')

    # テーブル作成
    create_table(line_station[HEADERS])

    # csvファイルとして出力
    # line_station[HEADERS].to_csv(CSV_STATION, encoding='cp932', index=False)


if __name__ == '__main__':
    main()
