"""
サイト側との橋渡し的スクリプト
"""
import sys
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader

from .stopover_food import StopoverFood
from .guruanvi import get_img


def index(request):
    """
    requestから路線、乗車駅、降車駅、カテゴリーを取得する

    @param request: requests
    @return: HttpResponse
    """
    # 指定した名前のテンプレートに対応したコンパイル済みのテンプレートを返す
    template = loader.get_template('stopover_food_app/index.html')
    # index.htmlに渡す辞書
    context = {
        "data": list(),
        "pagecount": 0,
        "message": ""
    }
    # GET.__contains__('key): 指定のキーが設定されている場合にTrueを返す
    # line: 路線, start: 乗車駅, end: 降車駅, category: カテゴリーに対応する
    if (request.GET.__contains__('line') and request.GET.__contains__('start') and
            request.GET.__contains__('end') and request.GET.__contains__('category')):

        # 飲食店情報取得
        sf = StopoverFood(request.GET['line'], request.GET['start'], request.GET['end'], request.GET['category'])
        data, message = sf.stopover_food()

        # 飲食店情報が取得できなかった場合エラーメッセージ送信
        if len(data) == 0:
            context["message"] = message
            return HttpResponse(template.render(context, request))

        # ページ数
        page_num = 15
        pagecount = int(len(data) / page_num)
        if len(data) / page_num - pagecount > 0:
            pagecount += 1

        # 2ページ目以降に遷移する場合
        if request.GET.__contains__('page'):
            page = int(request.GET['page']) - 1
            if page < 0:
                page = 0

            data = data[page * page_num: page * page_num + page_num]

        # 1ページ目
        else:
            data = data[0: page_num]

        data = get_img(data)
        context["data"] = data
        context["pagecount"] = pagecount

    return HttpResponse(template.render(context, request))
