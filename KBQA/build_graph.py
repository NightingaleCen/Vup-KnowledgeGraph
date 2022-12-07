# -*- coding: utf-8 -*-
import json
import time

from py2neo import Graph, Node, Relationship
from py2neo import NodeMatcher, RelationshipMatcher

# 连接Neo4j
url = "http://localhost:7474"
username = "neo4j"
password = input("Please input your neo4j password: ")
graph = Graph(url, auth=(username, password), name="neo4j")
print("neo4j info: {}".format(str(graph)))

def create_node(nodes, label):
    create_node_cnt = 0
    node_matcer = NodeMatcher(graph)
    for node in nodes:
        name = node
        find_node = node_matcer.match(label, name=name).first()
        if find_node is None:
            # attrs = {k: v for k, v in node.items() if k != "label"}
            print("node:",node)
            node = Node(label, **node)
            graph.create(node)
            create_node_cnt += 1
            print(f"create {create_node_cnt} nodes.")
        else:
            print("already have",node)
def create_relation (relations):
    # 创建关系
    node_matcer = NodeMatcher(graph)
    create_rel_cnt = 0
    relation_matcher = RelationshipMatcher(graph)
    for relation in relations:
        print(relation)
        s_node, s_label = relation["subject"], relation["subject_type"]
        e_node, e_label = relation["object"], relation["object_type"]
        rel = relation["predicate"]
        start_node = node_matcer.match(s_label, name=s_node).first()
        end_node = node_matcer.match(e_label, name=e_node).first()
        if start_node is not None and end_node is not None:
            r_type = relation_matcher.match([start_node, end_node], r_type=rel).first()
            if r_type is None:
                graph.create(Relationship(start_node, rel, end_node))
                create_rel_cnt += 1
                print(f"create {create_rel_cnt} relations.")

# 读取group数据
group_node = []
hasVtuber = {}
hasPopularVideo = {}
with open("./data/groups.json", 'r', encoding="utf-8") as fp:
    data = json.load(fp)  # 加载json文件
    for group in data:  # c1个人势+社团名
        group_list = {}
        for c in data[group]:
            if c == "vups":
                for vup in data[group][c]:
                    hasVtuber.setdefault(group, []).append(vup)
            elif c == "official_vid" and data[group][c]:
                group_list[c] = data[group][c]["BV"]
                hasPopularVideo.setdefault(group, []).append(data[group][c]["BV"])
            elif c == "relative_vid"and data[group][c]:
                group_list[c] = data[group][c]["BV"]
                hasPopularVideo.setdefault(group, []).append(data[group][c]["BV"])
            else:
                group_list[c] = data[group][c]
        group_node.append(group_list)
        # for c2 in data[c1]:  # c2 信息属性
        #     if c2 not in classify_list:
        #         classify_list.append(c2)
print("finish read groups")

# nodes = data_dict["nodes"]
# relations = data_dict["relations"]

# 创建group节点
create_node(group_node , "group")

# 读取vtuber数据
vtuber_node = []
ni_node =[]
belongTo = {}
hasMoe = {}
hasPopularVideo = {}
hasNickname = {}
with open("./data/vups.json", 'r', encoding="utf-8") as fp:
    data = json.load(fp)  # 加载json文件
    for vup in data:  # c1个人势+社团名
        vtuber_list = {}
        for c in data[vup]:
            if c == "group":
                vtuber_list[c] = data[vup][c]
                belongTo.setdefault(vup, []).append(data[vup][c])
            elif c == "moes":
                for moes in data[vup][c]:
                    hasMoe.setdefault(vup, []).append(moes)
            elif c == "official_vid" and data[vup][c]:
                vtuber_list[c] = data[vup][c]["BV"]
                hasPopularVideo.setdefault(vup, []).append(data[vup][c])
            elif c == "relative_vid" and data[vup][c]:
                vtuber_list[c] = data[vup][c]["BV"]
                hasPopularVideo.setdefault(vup, []).append(data[vup][c])
            elif c == "nickname":
                tem=["test1","test2"]
                if type(data[vup][c])==type(tem):
                    for ni in data[vup][c]:
                        ni_list={}
                        ni_list["name"]=ni
                        ni_node.append(ni_list)
                        hasNickname.setdefault(vup, []).append(ni)
                else:
                    ni_list = {}
                    ni_list["name"]=data[vup][c]
                    ni_node.append(ni_list)
                    hasNickname.setdefault(vup, []).append(data[vup][c])
            else:
                vtuber_list[c] = data[vup][c]
        vtuber_node.append(vtuber_list)
print("finish read vtuber")
# 创建vtuber节点
create_node(vtuber_node, "vtuber")


# 读取video数据
video_node = []

isRelativeToVtuber = {}
isRelativeToGroup = {}
with open("./data/videos.json", 'r', encoding="utf-8") as fp:
    data = json.load(fp)  # 加载json文件
    for video in data:  # c1个人势+社团名
        video_list = {}
        for c in data[video]:
            if c == "BV":
                video_list["name"] = data[video][c]
            if c == "relative_vup":
                for vup in data[video][c]:
                    isRelativeToVtuber.setdefault(video, []).append(vup)
            elif c == "relative_vup_group":
                for group in data[video][c]:
                    isRelativeToGroup.setdefault(video, []).append(group)
            else:
                video_list[c] = data[video][c]
        video_node.append(video_list)

print("finish read video")
# 创建video节点
create_node(video_node, "video")


# 读取moe数据
moe_node = []

MoeBelongTo = {}
with open("./data/moes.json", 'r', encoding="utf-8") as fp:
    data = json.load(fp)  # 加载json文件
    for moe in data:  # c1个人势+社团名
        moe_list = {}
        moe_list["name"] = moe
        for vup in data[moe]:
            MoeBelongTo.setdefault(moe, []).append(vup)
        moe_node.append(moe_list)
print("finish read moe")
# 创建moe节点
create_node(moe_node, "moe")


# 读取ni数据

print("finish read ni")
# 创建ni节点
create_node(ni_node, "ni")
print(ni_node)

# 创建关系
relations = []
# hasVtuber = {}
for group in hasVtuber.keys():
    if hasVtuber[group]:
        for vtuber in hasVtuber[group]:
            relation = {}
            relation["subject"] = group
            relation["subject_type"] = "group"
            relation["object"] = vtuber
            relation["object_type"] = "vtuber"
            relation["predicate"] = "hasVtuber"
            relations.append(relation)
# hasPopularVideo = {}
for group in hasPopularVideo.keys():
    if hasPopularVideo[group]:
        for video in hasPopularVideo[group]:
            relation = {}
            relation["subject"] = group
            relation["subject_type"] = "group"
            relation["object"] = video
            relation["object_type"] = "video"
            relation["predicate"] = "hasPopularVideo"
            relations.append(relation)
# belongTo = {}
for vtuber in belongTo.keys():
    if belongTo[vtuber]:
        for group in belongTo[vtuber]:
            relation = {}
            relation["subject"] = vtuber
            relation["subject_type"] = "vtuber"
            relation["object"] = group
            relation["object_type"] = "group"
            relation["predicate"] = "belongTo"
            relations.append(relation)
# hasMoe = {}
for vtuber in hasMoe.keys():
    for moe in hasMoe[vtuber]:
        relation = {}
        relation["subject"] = vtuber
        relation["subject_type"] = "vtuber"
        relation["object"] = moe
        relation["object_type"] = "moe"
        relation["predicate"] = "hasMoe"
        relations.append(relation)
# hasPopularVideo = {}
for vtuber in hasPopularVideo.keys():
    relation = {}
    relation["subject"] = vtuber
    relation["subject_type"] = "vtuber"
    relation["object"] = hasPopularVideo[vtuber]
    relation["object_type"] = "video"
    relation["predicate"] = "hasPopularVideo"
    relations.append(relation)
# isRelativeToVtuber = {}
for video in isRelativeToVtuber.keys():
    if isRelativeToVtuber[video]:
        for vtuber in isRelativeToVtuber[video]:
            relation = {}
            relation["subject"] = video
            relation["subject_type"] = "video"
            relation["object"] = vtuber
            relation["object_type"] = "vtuber"
            relation["predicate"] = "isRelativeToVtuber"
            relations.append(relation)
# isRelativeToGroup = {}
for video in isRelativeToGroup.keys():
    if isRelativeToGroup[video]:
        for group in isRelativeToGroup[video]:
            relation = {}
            relation["subject"] = video
            relation["subject_type"] = "video"
            relation["object"] = group
            relation["object_type"] = "group"
            relation["predicate"] = "isRelativeToGroup"
            relations.append(relation)
# MoeBelongTo = {}
for moe in MoeBelongTo.keys():
    if MoeBelongTo[moe]:
        for vtuber in MoeBelongTo[moe]:
            relation = {}
            relation["subject"] = moe
            relation["subject_type"] = "moe"
            relation["object"] = vtuber
            relation["object_type"] = "vtuber"
            relation["predicate"] = "MoeBelongTo"
            relations.append(relation)
# hasNickname= {}
for vtuber in hasNickname.keys():
    if hasNickname[vtuber]:
        for ni in hasNickname[vtuber]:
            relation = {}
            relation["subject"] = vtuber
            relation["subject_type"] = "vtuber"
            relation["object"] = ni
            relation["object_type"] = "ni"
            relation["predicate"] = "hasNickname"
            relations.append(relation)

create_relation (relations)

