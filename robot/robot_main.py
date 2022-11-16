from bs4 import BeautifulSoup
from robot_utils import *
import requests
import sys
import asyncio
import json


async def process_individual_vups(main_page):
    # 处理个人势vup数据.
    individual_group = VupGroup("个人势", None)
    await individual_group.get_info()
    vup_groups["个人势"] = individual_group

    main_response = BeautifulSoup(main_page, "lxml")
    individual_table = main_response.find(
        "span", style=True, string="个人势／独立运营虚拟UP主").find_parent("tbody")
    individuals = individual_table.find_all("a")

    tasks = []
    for vup in individuals:

        status = 0 if vup.parent.name == "i" else 1
        if "页面不存在" in vup["title"]:
            link = None
        else:
            link = "https://zh.moegirl.org.cn{}".format(vup["href"])

        new_vup = Vup(vup.string, link, status, individual_group)
        individual_group.vups.append(new_vup)
        tasks.append(asyncio.create_task(new_vup.get_info()))
        if link is not None:
            await asyncio.sleep(3)

    await asyncio.gather(*tasks)


async def process_vup_groups(main_page):
    # 处理vup社团及相关vup数据.
    main_response = BeautifulSoup(main_page, "lxml")
    group_table = main_response.find(
        "span", style=True, string="虚拟UP主社团／事务所").find_parent("tbody").find_all("tr", recursive=False)[4].find("tbody")
    groups = group_table.find_all("a")

    for group in groups:
        if group.string != "[+]":
            if "页面不存在" in group["title"]:
                link = None
            else:
                link = "https://zh.moegirl.org.cn{}".format(group["href"])

            new_group = VupGroup(group.string, link)
            vup_groups[group.string] = new_group
            group_task = asyncio.create_task(new_group.get_info())

            # 获取该社团下各vup数据
            if group.next_sibling is not None and group.next_sibling.name == "sup":
                template_link = "https://zh.moegirl.org.cn{}".format(
                    group.next_sibling.a["href"])
                vup_task = asyncio.create_task(
                    new_group.get_vups(template_link))

            await asyncio.gather(group_task, vup_task)  # 同时只处理一个group避免429


async def get_data():

    # 获取萌娘百科虚拟主播中心页
    for i in range(MAX_TRIES):
        print("Fetching Vtuber center page...")
        main_response = requests.get(
            "https://zh.moegirl.org.cn/%E8%99%9A%E6%8B%9FUP%E4%B8%BB", "lxml",
            headers=HEADERS)
        if main_response.status_code == 200:
            print("Center page successfully fetched.")
            break
        print("Fetching failed, code {}.".format(main_response.status_code))
        if i == MAX_TRIES - 1:
            print("All attempts failed, aborting...")
            sys.exit(1)

    # 获取vup与社团数据
    individual_process = asyncio.create_task(
        process_individual_vups(main_response.text))
    group_process = asyncio.create_task(
        process_vup_groups(main_response.text))

    await asyncio.gather(individual_process, group_process)


vups = {}
vup_groups = {}
moe_set = MoeSet()
video_set = VideoSet()

if __name__ == "__main__":

    asyncio.run(get_data())

    # 实体对齐（可能需要重写确保已经转为个人势的vup所属得到更新）
    for group in vup_groups.keys():
        for vup in vup_groups[group].vups:
            vups[vup.name] = vup

    # 处理萌点
    for vup in vups.keys():
        for moe in vups[vup].moes:
            moe_set.add_moe(vups[vup], moe)

    # 处理视频
    for group in vup_groups.keys():
        video_set.add_video(vup_groups[group].official_vid, vup_groups[group])
        video_set.add_video(vup_groups[group].relative_vid, vup_groups[group])
        for vup in vup_groups[group].vups:
            video_set.add_video(vup.official_vid, vup)
            video_set.add_video(vup.relative_vid, vup)

    with open("../data/videos.json", "w") as f:
        json.dump(video_set.get_json_dict(), f, indent=4, ensure_ascii=False)

    with open("../data/moes.json", "w") as f:
        json.dump(moe_set.get_json_dict(), f, indent=4, ensure_ascii=False)

    with open("../data/vups.json", "w") as f:
        json.dump({name: vup.get_json_dict()
                  for name, vup in vups.items()}, f, indent=4, ensure_ascii=False)

    with open("../data/groups.json", "w") as f:
        json.dump({name: group.get_json_dict() for name,
                  group in vup_groups.items()}, f, indent=4, ensure_ascii=False)
