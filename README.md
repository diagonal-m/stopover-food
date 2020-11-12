# stopover-food

## 概要

　`路線名`と`路線内の駅名2つ`の入力と`飲食店カテゴリー`を選択して検索して検索することで区間内の選択したカテゴリーの飲食店情報をまとめて取得して表示するWebアプリケーションを「ぐるなびAPI」を利用してPythonでDjangoを用いて作成。



## ディレクトリ構成

```
stopover-food/
 ├── manage.py
 ├── Dockerfile
 ├── docker-compose.yml
 ├── requirements.txt
 ├── stopover_food_app/
 |    ├── migrations/
 |    |   └── __init__.py
 |    ├── templates/
 |    |   └── stopover_food_app/
 |    |       └── index.html
 |    ├── __init__.py
 |    ├── admin.py
 |    ├── apps.py
 |    ├── functions.py  # レーベンシュタイン距離算出用関数を配置するモジュール
 |    ├── stopover_food.py  # 下車飯メインスクリプト
 |    ├── gurunavi.py  # ぐるなびAPIを使うための関数を配置するモジュール
 |    ├── consts.py  # 定数配置用モジュール
 |    ├── models.py
 |    ├── tests.py
 |    ├── urls.py
 |    └── views.py  # サイト側との橋渡し的スクリプト
 ├── stopover_food_project/
 |    ├── __init__.py
 |    ├── asgi.py
 |    ├── settings.py
 |    ├── urls.py
 |    └── wsgi.py
 └── deploy_station/
      ├── app.py  # 駅データ.jpから路線・駅情報を取得してDB更新
      ├── functions.py
      └── consts.py
```



## 環境変数

```
GURUNAVI_KEY=******
MAIL=*****@*****
PW=*********
KEY=*******
HOST=***.***.****
DBNAME='postgres'
DB_HOST='db'
DB_USER='postgres'
DB_PASSWORD='postgres'
DB_PORT='5432'
```



## docker-composeで開発環境構築

```bash
$ pwd
hoge/stopover-food
$ docker-compose --build
$ docker-compose run --rm web python manage.py migrate
$ docker-compose up -d  # デタッチモードでコンテナ群を起動
$ docker-compose ps --service
db
web
$ docker-compose exec web /bin/bash
root@daea734b4f93:/tmp$ cd deploy_station
root@daea734b4f93:/tmp$ python app.py  # 駅情報をDBに格納
root@daea734b4f93:/tmp$ exit  # コンテナから出る
$ docker-compose up
```

http://localhost:8000/ 