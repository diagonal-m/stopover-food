"""
ぐるなびAPIを用いて飲食店情報を取得する関数を配置するモジュール(Ver.1はラーメン専用)
"""
import re
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from geopy.distance import geodesic
import requests
from bs4 import BeautifulSoup
import json

from .consts import GURUNAVI_KEY

from typing import List

MAX_RETRY_COUNT = 3
WAIT_TIME = 1
REGULAR_CATEGORY_DICT = {'ラーメン': r'ラーメン|らーめん|油そば|坦々麺|タンタン|たんたん|拉麺',
                         'カフェ': r'カフェ|喫茶店|コーヒー'}


def get_response(url: str) -> requests:
    """
    ぐるなびAPIにrequestsを送りレスポンスを返す関数
    status_codeが500のときはリトライ

    @param url: ぐるなびAPIのurl
    """
    response = None
    for retry in range(MAX_RETRY_COUNT):
        response = requests.get(url)
        if response.status_code == 500:
            sleep(WAIT_TIME)
            continue
        else:
            return response

    return response


def guruanvi_api(params: dict) -> List[list]:
    """
    ぐるなびAPIを用いて飲食店を検索する関数

    @param params: パラメータ辞書 e.g.) {"key": API key, "lat": 35.409, "lng": 139.596, "range": 3, 'keyword': 'ラーメン'}
    @return: 飲食店データリスト e.g.) [[店舗名称, 店舗URL, 住所, ..., 'ぐるなび'], [店舗名称, 店舗URL, ... ,'ぐるなび'], ...]
    """
    shop_datas = list()
    api_base = 'https://api.gnavi.co.jp/RestSearchAPI/v3/?'
    api_params = 'keyid={key}&latitude={lat}&longitude={lng}&range={range_}&freeword={keyword}&hit_per_page=100'
    url = api_base + api_params.format(
        key=params['key'],
        lat=params['lat'],
        lng=params['lng'],
        range_=params['range'],
        keyword=params['keyword']
    )
    response = get_response(url)

    # 指定された条件の店舗が存在しない
    if response.status_code == 404:
        return shop_datas

    result_list = json.loads(response.text)['rest']
    for shop_data in result_list:
        # キーワード以外のカテゴリーのものが検索結果に含まれるため、カテゴリーにキーワードの関連カテゴリーを含む場合のみ抽出
        if re.search(REGULAR_CATEGORY_DICT[params['keyword']], shop_data['category']):
            shop_datas.append(
                [
                    shop_data["name"],  # 0. 店舗名称
                    shop_data["url"],  # 1. PCサイトURL
                    shop_data["address"],  # 2. 住所
                    shop_data['tel'],  # 3. 電話番号
                    shop_data['opentime'],  # 4. 営業時間
                    shop_data['holiday'],  # 5. 休業日
                    shop_data["budget"],  # 6. 平均予算
                    shop_data['access']['station'],  # 7. 駅名
                    shop_data['access']['walk'],  # 8. 徒歩(分)
                    shop_data['pr']['pr_short'],  # 9. PR文(短)
                    shop_data["image_url"]['shop_image1'],  # 10. 店舗画像１のurl
                    shop_data['category'],  # 11. カテゴリー
                    params['station'] + '駅',  # 12. 駅名(固定)
                    geodesic((params['lat'], params['lng']), (shop_data['latitude'], shop_data['longitude'])).m,
                    "ぐるなび"
                ]
            )

    return shop_datas


def get_src(store_data) -> dict:
    """
    個別の店舗情報からscrタグを取得、店舗情報に追加して返す

    @param store_data: 店舗情報
    @return: 画像情報を追加した店舗情報
    """
    if store_data['url'] and store_data['img'] == '':
        try:
            response = requests.get(store_data['url'], timeout=(3.0, 3)).text
            sleep(0.5)
            soup = BeautifulSoup(response, 'html.parser')
            img = soup.find('div', id='motif-slider-main').find('img').attrs['src']
            store_data['img'] = img
            return store_data
        except Exception:
            return store_data
    else:
        return store_data


def get_img(data: list) -> list:
    """
    ぐるなびから画像をスクレイピングして飲食店情報に加える関数
    時間削減のため並列処理を実施

    @param data: 飲食店情報の辞書のリスト
    @return: 画像情報を加えた飲食店情報の辞書のリスト
    """
    with ThreadPoolExecutor(5) as e:
        ret = e.map(get_src, data)
    new_data = [r for r in ret]

    return new_data


if __name__ == '__main__':
    gurunavi_params = {
        "key": GURUNAVI_KEY, "lat": 42.797984, "lng": 140.596107, "range": 3, 'keyword': 'ラーメン'
    }

    for i in guruanvi_api(gurunavi_params):
        print(i)


