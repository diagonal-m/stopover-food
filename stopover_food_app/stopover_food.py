"""
路線、乗車駅、降車駅を受け取り、区間内すべての飲食店情報(ver1はラーメンのみ)を取得して返すクラスを配置するモジュール
"""
import pandas as pd
# from gurunavi import guruanvi_api

from . import guruanvi
from .consts import GURUNAVI_KEY


class StopoverFood:
    """
    下車飯クラス
    """
    def __init__(self, line: str, start_station: str, end_station: str, range_: int = 3, keyword: str = 'ラーメン'):
        """
        初期化メソッド

        @param line: 路線名 e.g.) '東急東横線'
        @param start_station: 乗車駅 e.g.) '横浜'
        @param end_station: 降車駅 e.g.) '自由が丘'
        @param range_: 緯度・経度からの検索範囲(1: 300m, 2: 500m, 3: 1000m, 4: 2000m, 5: 3000m) default=3
        @param keyword: 検索キーワード default='ラーメン'
        """
        self.line = line
        self.start_station = start_station.replace('駅', '')
        self.end_station = end_station.replace('駅', '')
        self.df = None
        self.api_params = {'key': GURUNAVI_KEY, 'lat': None, 'lng': None, 'range': range_, 'keyword': keyword}

    def _get_station_df(self) -> None:
        """
        「路線番号」、「駅番号」、「路線名」、「駅名」、「緯度」、「経度」の駅情報データを
        データフレームとして読み込む(とりあえずCSVファイルから)
        """
        self.df = pd.read_csv('./station_data/station.csv', encoding='cp932')

    def _validation_line(self) -> bool:
        """
        路線名が駅情報データに含まれるものかどうかを確認するメソッド

        @return: 路線名が正しいか否かのbool値
        """
        is_validated = False
        line_list = self.df['line_name'].to_list()

        if not(self.line in line_list):
            return True

        return is_validated

    def _validated_station(self) -> bool:
        """
        乗車駅と降車駅が指定された路線内に存在するかを確認するメソッド

        @return: 指定された路線内に存在するか否かのbool値
        """
        is_validated = False
        df = self.df.copy()
        start_and_end = {self.start_station, self.end_station}
        stations_on_line = set(df[df['line_name'] == self.line]['station_name'].to_list())

        if not start_and_end.issubset(stations_on_line):
            return True

        return is_validated

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
        if self.line == 'JR山手線':
            lon_lat_1 = section.query('@start <= index <= @end')[['lon', 'lat']]
            lon_lat_2 = section.query('@start >= index or index >= @end')[['lon', 'lat']]
            lon_lat = lon_lat_1 if (lon_lat_1.shape[0] < lon_lat_2.shape[0]) else lon_lat_2
        else:
            lon_lat = section.query('@start <= index <= @end')[['lon', 'lat']]

        return [tuple(s[1:]) for s in lon_lat.itertuples()]

    def _exec_gurunavi_api(self, station_list: list) -> list:
        """
        ぐるなびAPIから緯度・経度をキーに飲食店情報を取得する
        @param station_list: 駅の(緯度・経度)のリスト
        @return: 飲食点情報のリスト
        """
        food_list = list()
        for lon, lat in station_list:
            self.api_params['lat'], self.api_params['lng'] = lat, lon
            food_list.extend(guruanvi.guruanvi_api(self.api_params))

        return food_list

    def stopover_food(self) -> tuple:
        """
        下車飯クラスのメインメソッド

        @return:
        """
        food_list = list()
        food_dict_list = list()
        message = '合格'
        self._get_station_df()  # 駅情報のデータフレームを取得
        # 路線名バリデーション
        if self._validation_line():
            return food_list, f'{self.line}は正しい路線名ではありません、正式名称で入力してください'

        # 駅名バリデーション
        if self._validated_station():
            return food_list, f'指定された駅名が{self.line}に存在しません'

        stations = self._get_section_stations()

        food_list = self._exec_gurunavi_api(stations)

        # 店舗が存在しないとき
        if len(food_list) == 0:
            return food_dict_list, "指定された条件の店舗が存在しません"

        for food in food_list:
            food_dict_list.append({
                "title": food[0],
                "category": food[11],
                "url": food[1],
                "img": food[10],
                "station": f'{food[7]} {food[8]}分'  # 駅名 徒歩○分
            })

        return food_dict_list, message


if __name__ == '__main__':
    sf = StopoverFood('ブルーライン', '上大岡', '港南中央')
    foods = sf.stopover_food()[0]
    for f in foods:
        print(f'{f[0]}: {f[7]}: {f[1]}')
