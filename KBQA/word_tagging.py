# encoding=utf-8

"""

@file: word_tagging.py

@time: 2020/03/29

@desc: 定义Word类的结构；定义Tagger类，实现自然语言转为Word对象的方法。

"""
import jieba
import jieba.posseg as pseg


class Word(object):
    def __init__(self, token, pos):
        self.token = token
        self.pos = pos


class Tagger():
    def __init__(self, dict_paths=['./KBQA/word_data/mydict8.txt','./KBQA/word_data/askdict8.txt','./KBQA/word_data/properdict8.txt']):
        for p in dict_paths:
            jieba.load_userdict(p)
        jieba.suggest_freq((('萌娘主页')), True)
        jieba.suggest_freq(('热门视频'),True)
        jieba.suggest_freq(('官方视频'), True)
        jieba.suggest_freq(('相关视频'), True)
        jieba.suggest_freq(('b站链接'), True)


    @staticmethod
    def get_word_objects(sentence):
        # type: (str) -> list
        """
        把自然语言转为Word对象
        :param sentence:
        :return:
        """
        mydict = {}
        with open('./KBQA/word_data/mydict8.txt', encoding='utf-8') as f:
            for line in f:
                if len(line) >= 2:
                    mydict[line[0]] = line[1]

        askdict = {}
        with open('./KBQA/word_data/askdict8.txt', encoding='utf-8') as f:
            for line in f:
                line = line.split()
                if len(line) >= 2:
                    askdict[line[0]] = line[1]
        properdict = {}
        with open('./KBQA/word_data/properdict8.txt', encoding='utf-8') as f:
            for line in f:
                line = line.split()
                if len(line) >= 2:
                    properdict[line[0]] = line[1]


        wordlist = [Word(word, tag) for word, tag in pseg.cut(sentence)]


        for i in wordlist:
            if i.token in mydict.keys():
                i.pos = mydict[i.token]
            if i.token in askdict.keys():
                i.pos = askdict[i.token]
            if i.token in properdict.keys():
                i.pos = properdict[i.token]
        # for i in wordlist:
        #     print(i.token, i.pos)

        return wordlist




if __name__ == '__main__':
    tagger = Tagger()


    while True:
        s = input()
        for i in tagger.get_word_objects(s):
            print(i.token, i.pos)
