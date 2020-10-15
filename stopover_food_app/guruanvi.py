"""
ぐるなびAPIを用いて飲食店情報を取得する関数を配置するモジュール(Ver.1はラーメン専用)
"""
import re
from time import sleep
import requests
import json

from .consts import GURUNAVI_KEY

from typing import List

MAX_RETRY_COUNT = 3
WAIT_TIME = 1


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
    @return: ?
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
        # ラーメン以外のカテゴリーのものが検索結果に含まれるため、カテゴリーにラーメン関連キーワードを含む場合のみ抽出
        if re.search(r'ラーメン|らーめん|油そば|坦々麺|タンタン|たんたん|拉麺', shop_data['category']):
            shop_datas.append(
                [
                    shop_data["name"],  # 店舗名称
                    shop_data["url"],  # PCサイトURL
                    shop_data["address"],  # 住所
                    shop_data['tel'],  # 電話番号
                    shop_data['opentime'],  # 営業時間
                    shop_data['holiday'],  # 休業日
                    shop_data["budget"],  # 平均予算
                    shop_data['access']['station'],  # 駅名
                    shop_data['access']['walk'],  # 徒歩(分)
                    shop_data['pr']['pr_short'],  # PR文(短)
                    shop_data["image_url"]['shop_image1'],  # 店舗画像１のurl
                    shop_data['category'],  # カテゴリー
                    "ぐるなび"
                ]
            )
    return shop_datas


if __name__ == '__main__':
    gurunavi_params = {
        "key": GURUNAVI_KEY, "lat": 42.797984, "lng": 140.596107, "range": 3, 'keyword': 'ラーメン'
    }

    for i in guruanvi_api(gurunavi_params):
        print(i)


