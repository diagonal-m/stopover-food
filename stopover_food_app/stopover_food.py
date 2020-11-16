"""
路線、乗車駅、降車駅を受け取り、区間内すべての飲食店情報(ver1はラーメンのみ)を取得して返すクラスを配置するモジュール
"""
import re
import pandas as pd
import numpy as np
import psycopg2
from Levenshtein import distance as levenshtein

from . import guruanvi
from .consts import GURUNAVI_KEY, DATABASE
from .functions import RomanaizeST

from typing import Tuple

CATEGORY_DICT = {'ra-men': 'ラーメン', 'cafe': 'カフェ'}


class StopoverFood(RomanaizeST):
    """
    下車飯クラス
    """
    def __init__(self, line: str, start_station: str, end_station: str, keyword: str, range_: int = 3):
        """
        初期化メソッド

        @param line: 路線名 e.g.) '東急東横線'
        @param start_station: 乗車駅 e.g.) '横浜'
        @param end_station: 降車駅 e.g.) '自由が丘'
        @param keyword: 検索キーワード default='ラーメン'
        @param range_: 緯度・経度からの検索範囲(1: 300m, 2: 500m, 3: 1000m, 4: 2000m, 5: 3000m) default=3
        """
        super().__init__()
        self.line = line
        self.start_station = start_station.replace('駅', '')
        self.end_station = end_station.replace('駅', '')
        self.df = None
        self.api_params = {'key': GURUNAVI_KEY, 'lat': None, 'lng': None,
                           'range': range_, 'keyword': CATEGORY_DICT[keyword], 'station': None}

    def _get_station_df(self) -> None:
        """
        「路線番号」、「駅番号」、「路線名」、「駅名」、「緯度」、「経度」の駅情報データを
        データフレームとして読み込む(とりあえずCSVファイルから)
        """
        self.df = pd.read_csv('./station_data/station.csv', encoding='cp932')

    def _get_station_df_db(self) -> None:
        """
        「路線番号」、「駅番号」、「路線名」、「駅名」、「緯度」、「経度」の駅情報データを
        データフレームとして読み込む(とりあえずCSVファイルから)
        """
        with psycopg2.connect(**DATABASE) as conn:
            sql = "select * from station_info;"
            df = pd.read_sql(sql, conn)
            df.index = df['index']
        self.df = df

    def _validation_line(self) -> Tuple[bool, str]:
        """
        路線名が駅情報データに含まれるものかどうかを確認するメソッド

        @return: 路線名が正しいか否かのbool値
        """
        is_validated = True
        message = '合格'
        line_list = self.df['line_name'].to_list()

        if not(self.line in line_list):
            return False, f'{self.line}は正しい路線名ではありません、正式名称で入力してください'

        return is_validated, message

    def _any_chance_line(self) -> str:
        """
        レーベンシュタイン距離が近い路線名を3つ返す

        @return: 追加メッセージ  e.g.) もしかして...〇〇？
        """
        roman_lines = list(self.df['line_name_roman'].unique())
        lines = list(self.df['line_name'].unique())
        partial_matches = [line for line in lines if self.line in line]
        if len(partial_matches) > 0:
            return f'。もしかして...{".".join(partial_matches[:3])}?'
        inputed_line_roman = self.romanaize(self.line)[0]
        dists = [levenshtein(inputed_line_roman, roman_line) for roman_line in roman_lines]
        idx = sorted(range(len(dists)), key=lambda x: dists[x])[:3]
        chance_line = [lines[i] for i in idx]

        return f'。もしかして...{",".join(chance_line)}?'

    def _validated_station(self) -> tuple:
        """
        乗車駅と降車駅が指定された路線内に存在するかを確認するメソッド

        @return: 指定された路線内に存在するか否かのbool値
        """
        is_validated = True
        message = '合格'
        error_station = ''
        df = self.df.copy()
        start_and_end = [self.start_station, self.end_station]
        stations_on_line = df[df['line_name'] == self.line]['station_name'].to_list()

        for station in start_and_end:
            if not (station in stations_on_line):
                return False, f'{station}は{self.line}の駅ではありません', station

        return is_validated, message, error_station

    def _any_chance_station(self, station_name: str) -> str:
        """
        レーベンシュタイン距離が最も近い駅名を返す

        @return: 追加メッセージ  e.g.) もしかして...〇〇？
        """
        roman_stations = self.df[self.df['line_name'] == self.line]['station_name_roman'].to_list()
        stations = self.df[self.df['line_name'] == self.line]['station_name'].to_list()
        inputed_station_roman = self.romanaize(station_name)[0]
        dists = [levenshtein(inputed_station_roman, roman_station) for roman_station in roman_stations]
        idx = sorted(range(len(dists)), key=lambda x: dists[x])[:3]
        chance_station = [stations[i] for i in idx]

        return f'。もしかして...{",".join(chance_station)}?'

    def _get_section_stations(self) -> list:
        """
        乗車駅と降車駅の区間内の駅の緯度・経度のタプルのリストを返す

        @return: [(緯度, 経度), (緯度, 経度), ..., (緯度, 経度)]
        """
        section = self.df[self.df['line_name'] == self.line]
        station_nums = (
            section[section['station_name'] == self.start_station].index.values[0],
            section[section['station_name'] == self.end_station].index.values[0]
        )
        start, end = min(station_nums), max(station_nums)

        # 環状線対策
        if self.line in ['JR山手線', '大阪環状線']:
            lon_lat_1 = section.query('@start <= index <= @end')[['lon', 'lat', 'station_name']]
            lon_lat_2 = section.query('@start >= index or index >= @end')[['lon', 'lat', 'station_name']]
            lon_lat = lon_lat_1 if (lon_lat_1.shape[0] < lon_lat_2.shape[0]) else lon_lat_2
        else:
            lon_lat = section.query('@start <= index <= @end')[['lon', 'lat', 'station_name']]

        stations = [tuple(s[1:]) for s in lon_lat.itertuples()]

        # 乗車駅 → 降車駅順になるように返す
        return stations[::-1] if np.argmax(station_nums) == 0 else stations

    def _exec_gurunavi_api(self, station_list: list) -> list:
        """
        ぐるなびAPIから緯度・経度をキーに飲食店情報を取得する
        @param station_list: 駅の(緯度・経度)のリスト
        @return: 飲食点情報のリスト
        """
        food_list = list()
        for lon, lat, station in station_list:
            self.api_params['lat'], self.api_params['lng'], self.api_params['station'] = lat, lon, station
            food_list.extend(guruanvi.guruanvi_api(self.api_params))

        return food_list

    def stopover_food(self) -> tuple:
        """
        下車飯クラスのメインメソッド

        @return:
        """
        food_list = list()
        food_dict_list = list()

        # self._get_station_df()
        self._get_station_df_db()  # 駅情報のデータフレームを取得
        # 路線名バリデーション
        is_validated, message = self._validation_line()
        if not is_validated:
            plus_message = self._any_chance_line()
            return food_list, message + plus_message

        # 駅名バリデーション
        is_validated, message, error_station = self._validated_station()
        if not is_validated:
            plus_message = self._any_chance_station(error_station)
            return food_list, message + plus_message

        # 区間内の全駅の緯度・経度のリスト
        stations = self._get_section_stations()

        # ぐるなびAPIから飲食点情報のリストを取得
        food_list = self._exec_gurunavi_api(stations)

        # 店舗が存在しないとき
        if len(food_list) == 0:
            return food_dict_list, "指定された条件の店舗が存在しません"

        for food in food_list:
            food_dict_list.append({
                "title": food[0],
                "pr_text": food[9] if len(food[9]) < 48 else food[9][:48] + '...',
                "category": food[11],  # e.g.) ラーメン
                "url": food[1],
                "img": food[10],
                "address": f'住所: {food[2][9:]}',
                "tel": f'TEL: {food[3]}',
                "station": food[12] + ": " + str(int(food[13])) + 'm' if food[13] <= 1000 else food[12],
                "open_time": f'OPEN: {food[4] if food[4] != food[9] else ""}'  # pr文が入ってることがあるのでその対策
            })

        food_dict = dict()
        for food in food_dict_list:
            if food['title'] in food_dict:
                food_dict[food['title']]['station'] += f" {food['station']}"
                continue
            food_dict[food['title']] = food

        return list(food_dict.values()), message


if __name__ == '__main__':
    sf = StopoverFood('ブルーライ', '上大岡', '港南中央')
    foods = sf.stopover_food()[0]
    for f in foods:
        print(f'{f[0]}: {f[7]}: {f[1]}')
