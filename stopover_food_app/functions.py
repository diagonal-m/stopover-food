"""
共通関数群を配置するモジュール
"""
import re

import MeCab
from pykakasi import kakasi


class RomanaizeST:
    """
    編集距離算出クラス
    """
    def __init__(self):
        """
        初期化メソッド
        """
        k = kakasi()
        k.setMode('K', 'a')
        self.conv = k.getConverter()
        self.tagger = MeCab.Tagger()

    def katakanize(self, text: str) -> str:
        """
        文字列をカタカナに変換する

        @return: カタカナ文字列
        """
        morphed = [re.split(r"[,\t\s\n]", w) for w in self.tagger.parse(text).split("\n")]
        morphed.remove([""])
        morphed.remove(["EOS"])
        k = [morph[-1] if morph[-1] != "*" else morph[0] for morph in morphed]

        return "".join(k)

    def romanaize(self, text: str) -> list:
        """
        カタカナ文字列をローマ字にして返す

        @return: ローマ字に変換済み文字列
        """
        katakana = self.katakanize(text)

        if type(katakana) == str:
            katakana = [katakana]

        return [self.conv.do(k) for k in katakana]


if __name__ == '__main__':
    rs = RomanaizeST()
    print(rs.romanaize("横浜"))
