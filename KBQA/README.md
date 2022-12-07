# vtuber-KBQA

## 文件说明

data 爬虫得到的四类实体的数据

word_data 内为jieba分词、词性标注和命名体识别的词典，mydict.txt由worddict_json2txt.py得到。由于jieba自定义词典必须为utf8格式的txt，因此手动把mydict.txt存为utf8格式的mydict8.txt。askdict8.txt和properdict8.txt为识别问题中询问实体和询问属性的词典。

word_tagging.py 为分词模块，在question_identify.py中会引用到。单独运行可以返回词性分类结果。

build_graph.py 为根据设定的关系的json数据的逻辑结构在neo4j中建立图。反复运行会产生重复的边，进行问答时会产生重复的结果。

question_identify.py为问答系统主函数，运行后输入问题可返回答案。

