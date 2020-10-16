"""
サイト側との橋渡し的スクリプト
"""
import sys
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader

from .stopover_food import StopoverFood


def index(request):
    """
    requestから路線、乗車駅、降車駅、カテゴリーを取得する

    @param request: requests
    @return: HttpResponse
    """
    # 指定した名前のテンプレートに対応したコンパイル済みのテンプレートを返す
    template = loader.get_template('stopover_food_app/index.html')
    error_template = loader.get_template('stopover_food_app/error.html')
    # index.htmlに渡す辞書
    context = {
        "data": list(),
        "pagecount": 0
    }
    # GET.__contains__('key): 指定のキーが設定されている場合にTrueを返す
    # line: 路線, start: 乗車駅, end: 降車駅, category: カテゴリーに対応する
    if (request.GET.__contains__('line') and request.GET.__contains__('start') and
            request.GET.__contains__('end') and request.GET.__contains__('category')):

        if '' in [request.GET['line'], request.GET['start'], request.GET['end']]:
            context["data"] = {'message': '未入力の項目があります'}
            return HttpResponse(error_template.render(context, request))

        sf = StopoverFood(request.GET['line'], request.GET['start'], request.GET['end'])
        data, message = sf.stopover_food()

        if len(data) == 0:
            context["data"] = {'message': message}
            return HttpResponse(error_template.render(context, request))

        context = {
            "data": data,
            "pagecount": len(data)
        }

    return HttpResponse(template.render(context, request))
