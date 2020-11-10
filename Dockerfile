FROM python:3.8.2

ENV PYTHONUNBUFFERED 1
# デフォルトの locale `C` を `C.UTF-8` に変更する
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# タイムゾーンを日本時間に変更
ENV TZ Asia/Tokyo

# /tmpにappとdockerをコピー
COPY . /tmp

# 相対パスの基準ディレクトリ
WORKDIR /tmp
RUN apt-get update && apt-get install -y \
    libmecab-dev mecab-ipadic-utf8 vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# MeCab
WORKDIR /tmp
RUN git clone https://github.com/taku910/mecab.git
WORKDIR /tmp/mecab/mecab
RUN ./configure  --enable-utf8-only \
  && make \
  && make check \
  && make install \
  && ldconfig

# MeCab ipadic
WORKDIR /tmp/mecab/mecab-ipadic
RUN ./configure --with-charset=utf8 \
  && make \
  &&make install

WORKDIR /tmp
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt