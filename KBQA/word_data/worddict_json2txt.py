import json

class MyDict:
    def __init__(self):

        group_list,classify_list = self.data_transfer_groups('../data/groups.json')
        moes_list = self.data_transfer_moes('../data/moes.json')
        nickname_list,character_list,vups_list = self.data_transfer_vups('../data/vups.json')
        video_list = self.data_transfer_moes('../data/videos.json')


        with open("mydict.txt", "a",encoding = "GB2312",errors='ignore') as file:
            for i in group_list:
                file.write(str(i) + ' group' + "\n")
            for i in classify_list:
                file.write(str(i) + ' cl' + "\n")
            for i in vups_list:
                file.write(str(i) + ' vup' + "\n")
            for i in moes_list:
                file.write(str(i) + ' moe' + "\n")
            for i in nickname_list:
                file.write(str(i) + ' ni' + "\n")
            for i in character_list:
                file.write(str(i) + ' ch' + "\n")
            for i in video_list:
                file.write(str(i) + ' video' + "\n")
        file.close()


    def data_transfer_groups(self,json_path):
        group_list = []
        classify_list = []
        with open(json_path, 'r', encoding="utf-8") as fp:
            data = json.load(fp)  # 加载json文件
            for c1 in data:  # c1个人势+社团名
                group_list.append(c1)
                for c2 in data[c1]:  # c2 信息属性
                    if c2 not in classify_list:
                        classify_list.append(c2)
        return group_list,classify_list

    def data_transfer_moes(self,json_path):
        moes_list = []
        with open(json_path, 'r', encoding="utf-8") as fp:
            data = json.load(fp)  # 加载json文件
            for c1 in data:  # 属性
                moes_list.append(c1)
        return moes_list

    def data_transfer_vups(self,json_path):
        nickname_list = []
        character_list = []
        vups_list = []
        with open(json_path, 'r', encoding="utf-8") as fp:
            data = json.load(fp)  # 加载json文件
            for c1 in data:  # c1个人势+社团名
                vups_list.append(c1)
                for c2 in data[c1]:
                    if c2 == 'nickname':
                        for c3 in data[c1][c2]:
                            nickname_list.append(c3)
                    if c2 == "hair_color" or c2 == "iris_color":
                        if data[c1][c2] :
                            if data[c1][c2] not in character_list:
                                character_list.append(data[c1][c2])

        return nickname_list,character_list,vups_list


# TODO 用于测试
if __name__ == '__main__':
    MyDict()



