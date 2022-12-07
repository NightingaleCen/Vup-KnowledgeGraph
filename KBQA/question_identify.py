
import logging

from py2neo import Graph

import word_tagging



class QASystem(object):
    def __init__(self):
        # self.graph = Graph(host="localhost", http_port=7474,
        #                    user="neo4j", password="zmfneo4j")
        url = "http://localhost:7474"
        username = "neo4j"
        password = input("Please input your neo4j password: ")
        self.graph = Graph(url, auth=(username, password), name="neo4j")
        self.cut = word_tagging.Tagger()
        self.answers = None
        self.type = 0

    def named_entity_recognition(self, word_list):  # 命名实体识别
        entity_list = []
        entity = ["moe", "vup", "group", "video","ni"]
        ask_list = []
        ask = ["askmoe", "askvup", "askgroup","askni"]
        proper_list = []
        proper = ['moe_link', 'bio', 'picture', 'hair_color', 'iris_color', 'followers', 'gender', 'bilibili_link'
            , 'link', 'title', 'views',"official_vid","relative_vid"]

        for i in word_list:
            if i.pos in entity:
                entity_list.append(i)
            if i.pos in ask:
                ask_list.append(i)
            if i.pos in proper:
                proper_list.append(i)


        if len(entity_list) == 2:
            self.type = 3
        elif len(entity_list) == 1:
            if len(ask_list) == 1:
                self.type = 2
            elif len(proper_list) == 1:
                self.type = 1
        else:
            self.type = 0

        return entity_list, ask_list,proper_list


    def parse_question(self, question):
        word_list = self.cut.get_word_objects(question)

        self.question_factor = {}
        self.question_factor['entity'],self.question_factor['ask'],self.question_factor['proper'] = self.named_entity_recognition(
            word_list) # 遍历其中是否含有vup
        self.answers = None
        # print("len(entity)",len(self.question_factor['entity']))
        # print("len(ask)", len(self.question_factor['ask']))
        # print("len(proper)", len(self.question_factor['proper']))


    def query_answer(self):
        query = ''
        #print("问题类型是：",self.type)
        global relation
        if self.type == 3: # 是否问题
            if self.question_factor['entity'][0].pos == 'vup':
                if self.question_factor['entity'][1].pos == 'group':
                    relation = 'belongTo'
                if self.question_factor['entity'][1].pos == 'moe':
                    relation = 'hasMoe'
                if self.question_factor['entity'][1].pos == 'video':
                    relation = 'hasPopularVideo'

            if self.question_factor['entity'][0].pos == 'group':
                if self.question_factor['entity'][1].pos == 'vup':
                    relation = 'hasVtuber'
                if self.question_factor['entity'][1].pos == 'video':
                    relation = 'hasPopularVideo'

            if self.question_factor['entity'][0].pos == 'moe':
                if self.question_factor['entity'][1].pos == 'vup':
                    relation = 'MoeBelongTo'
            if self.question_factor['entity'][0].pos == 'video':
                if self.question_factor['entity'][1].pos == 'vup':
                    relation = 'isRelativeToVtuber'
                if self.question_factor['entity'][1].pos == 'group':
                    relation = 'isRelativeToGroup'

            query = f"match (a)-[r:{relation}]-(b) " \
                    f"where a.name='{self.question_factor['entity'][0].token}' " \
                    f"return b.name"
            print("query:",query)
            if query:
                self.answers = []
                for answer in self.graph.run(query).data():
                    self.answers.append(list(answer.values())[0])
                if len(self.answers) == 0 or not self.answers[0]:
                    self.answers = None
                else:
                    if self.question_factor['entity'][1].token in self.answers:
                        print("猜对啦")
                        self.answers = True
                    else:
                        self.answers = False
                        print("猜错了")
        elif self.type == 2:
            if self.question_factor['entity'][0].pos == 'vup':
                if self.question_factor['ask'][0].pos == 'askgroup':
                    relation = 'belongTo'
                if self.question_factor['ask'][0].pos == 'askmoe':
                    relation = 'hasMoe'
                if self.question_factor['ask'][0].pos == 'askvideo':
                    relation = 'hasPopularVideo'
                if self.question_factor['ask'][0].pos == 'askni':
                    relation = 'hasNickname'

            if self.question_factor['entity'][0].pos == 'group':
                if self.question_factor['ask'][0].pos == 'askvup':
                    relation = 'hasVtuber'
                if self.question_factor['ask'][0].pos == 'askvideo':
                    relation = 'hasPopularVideo'
            if self.question_factor['entity'][0].pos == 'moe':
                if self.question_factor['ask'][0].pos == 'askvup':
                    relation = 'MoeBelongTo'
            if self.question_factor['entity'][0].pos == 'video':
                if self.question_factor['ask'][0].pos == 'askvup':
                    relation = 'isRelativeToVtuber'
                if self.question_factor['ask'][0].pos == 'askgroup':
                    relation = 'isRelativeToGroup'

            query = f"match (a)-[r:{relation}]-(b) " \
                    f"where a.name='{self.question_factor['entity'][0].token}' " \
                    f"return b.name"
            print("query:", query)
            if query:
                self.answers = []
                for answer in self.graph.run(query).data():
                    self.answers.append(list(answer.values())[0])
                if len(self.answers) == 0 or not self.answers[0]:
                    self.answers = None
        elif self.type == 1:
            if len(self.question_factor['proper'])>=1:

                query = f"match (e) " \
                        f"where e.name='{self.question_factor['entity'][0].token}' " \
                        f"return e.{self.question_factor['proper'][0].pos}"

                print("query:", query)
                print("ans:", self.graph.run(query).data())
                if query:
                    self.answers = []
                    for answer in self.graph.run(query).data():
                        self.answers.append(list(answer.values())[0])
                    if len(self.answers) == 0 or not self.answers[0]:
                        self.answers = None

        return self.answers




    def main(self):

        while True:
            question = input("问题：")
            if question == '退出' or question.startswith('q'):
                break
            print('问题：{}'.format(question))
            self.parse_question(question)
            answers = self.query_answer()
            if answers == True or answers == False:
                if answers == True:
                    print("是的!")
                else:
                    print("不是~")
            elif answers:
                print('回答：{}'.format(answers))
            else:
                print('回答：抱歉，没有找到答案')

        # while True:
        #     question = input('问题：')

        # for question in test_question_stream:
        #     if question == '退出' or question.startswith('q'):
        #         break
        #     print('问题：{}'.format(question))
        #     self.parse_question(question)
        #     answers = self.query_answer()
        #     if answers:
        #         print('回答：{}'.format(answers))
        #     else:
        #         print('回答：抱歉，没有找到答案')


if __name__ == '__main__':
    qa = QASystem()
    qa.main()