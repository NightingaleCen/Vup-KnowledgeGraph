from bs4 import BeautifulSoup
from bilibili_api import user, search
import re
from asyncio import CancelledError
import asyncio
import aiohttp

MAX_TRIES = 3
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"}


class VideoSet:
    def __init__(self) -> None:
        self.set = {}

    def add_video(self, vid, entity):
        '''
        将视频与相关实体添加至视频集中
        '''
        if vid is not None:
            try:
                self.set[vid.BV].add_relative_entity(entity)
            except BaseException:
                self.set[vid.BV] = vid
                self.set[vid.BV].add_relative_entity(entity)

    def get_json_dict(self):
        json_set = {}
        for BV, video in self.set.items():
            json_set[BV] = video.get_json_dict()
        return json_set


class MoeSet:
    def __init__(self) -> None:
        self.set = {}

    def add_moe(self, vup, moe):
        """
        将Vup添加至其萌点集中
        """
        try:
            self.set[moe].append(vup)
        except KeyError:
            self.set[moe] = [vup]

    def get_json_dict(self):
        json_set = {}
        for moe in self.set.keys():
            json_set[moe] = [vup.name for vup in self.set[moe]]
        return json_set


class BVideo:
    def __init__(self, BV, title, views) -> None:
        self.BV = BV
        self.link = "https://www.bilibili.com/video/" + BV
        self.title = title
        self.views = views
        self.relative_vup = []
        self.relative_vup_group = []

    def add_relative_entity(self, entity):
        if isinstance(entity, Vup):
            if entity not in self.relative_vup:
                self.relative_vup.append(entity)

        elif isinstance(entity, VupGroup):
            if entity not in self.relative_vup_group:
                self.relative_vup_group.append(entity)

    def get_json_dict(self):
        json_set = {}
        json_set["BV"] = self.BV
        json_set["link"] = self.link
        json_set["title"] = self.title
        json_set["views"] = self.views
        json_set["relative_vup"] = [vup.name for vup in self.relative_vup]
        json_set["relative_vup_group"] = [
            group.name for group in self.relative_vup_group]
        return json_set


class VupGroup:
    def __init__(self, name, link) -> None:
        self.name = name
        self.moe_link = link
        self.vups = []

    async def get_info(self):
        if self.moe_link is not None:
            print("Getting data of {}...".format(self.name))
            get_group = asyncio.create_task(get_page(self.moe_link))
            group_response = await get_group

            group_response = BeautifulSoup(group_response, "lxml")

            # 获取简介
            try:
                self.bio = ""
                for tag in group_response.find(
                        "div", class_="mw-parser-output").find_all(True, recursive=False):
                    if tag.name == "h2" or tag.name == "h3":
                        break
                    if tag.name == "p" and tag.find(
                            "script") is None and tag.find(
                            "style") is None and tag.string != "\n": # TODO:这种诡异的写法很可能需要重写...
                        self.bio += clean_data(tag) + "\n"
                self.bio = self.bio.rstrip()
            except BaseException:
                self.bio = None

            # 获取萌娘百科头图链接
            try:
                info = group_response.find(
                    class_=[
                        "infotemplatebox",
                        "infobox",
                        "infobox2",
                        "infoboxSpecial"]).find("tbody")
                self.picture = info.find("img")["src"]
            except BaseException:
                self.picture = None

            try:
                # 获取哔哩哔哩空间
                self.bilibili_link = group_response.find(
                    True, class_="mw-headline", string=re.compile(r"外部链接")).find_next(
                    True, href=re.compile(r"https://space\.bilibili\.com/"))["href"]
                self.uid = int(self.bilibili_link.split("/")[-1])

                try:
                    # 调用哔哩哔哩api
                    usr = user.User(self.uid)
                    get_official_video = asyncio.create_task(
                        usr.get_videos(pn=1, ps=1, order=user.VideoOrder.VIEW))
                    get_relative_video = asyncio.create_task(
                        search.search_by_type(
                            keyword=self.name+" 虚拟up主",
                            search_type=search.SearchObjectType.VIDEO,
                            order_type=search.OrderVideo.CLICK))

                    info = await asyncio.gather(get_official_video, get_relative_video)

                    # 获取官方发布播放量最高视频
                    bvid = info[0]["list"]["vlist"][0]["bvid"]
                    title = info[0]["list"]["vlist"][0]["title"]
                    views = info[0]["list"]["vlist"][0]["play"]
                    self.official_vid = BVideo(bvid, title, views)

                    # 获取全站播放量最高相关视频
                    bvid = info[1]["result"][0]["bvid"]
                    title = re.sub(r'<.*?>', "", info[1]["result"][0]["title"])
                    views = info[1]["result"][0]["play"]
                    self.relative_vid = BVideo(bvid, title, views)

                except BaseException:
                    self.official_vid = None
                    self.relative_vid = None

            except BaseException:
                self.bilibili_link = None
                self.official_vid = None
                self.relative_vid = None

        else:
            self.bio = None
            self.picture = None
            self.bilibili_link = None
            self.official_vid = None
            self.relative_vid = None

        print("Finished processing {}.".format(self.name))

    async def get_vups(self, template_link):
        """
        返回该企划的vup列表
        """
        print("Getting template data of {}...".format(self.name))
        get_template = asyncio.create_task(get_page(template_link))
        template_response = await get_template

        template_response = BeautifulSoup(template_response, "lxml")
        navbox = template_response.find(
            "table", class_="navbox").tbody.find("tbody")

        tasks = []
        names = []

        irrelevant_group_pattern = re.compile(r"关联|相关|其他|作品|游戏|赛事")
        unavailable_pattern = re.compile(r"（页面不存在）")

        for nav_group in navbox.find_all("td", class_=[
                                         "navbox-list navbox-even", "navbox-list navbox-odd", "navbox-abovebelow"]):

            # 跳过并非vup的条目（代表作品、相关企划等）
            nav_group_title = nav_group.find_previous_sibling("td")
            if nav_group_title is not None and nav_group_title["class"] == [
                    "navbox-group"]:
                if irrelevant_group_pattern.search(
                        str(nav_group_title.string)) is not None:
                    continue

            # 逐一获取各vup数据
            individuals = nav_group.find_all("a")
            for vup in individuals:

                # 不采用头图的链接以避免重复
                if vup.find("img") is not None:
                    continue

                # 跳过一些奇怪的条目（VirtualReal你害人不浅！）
                if vup.find_parent("td", class_="navbox-group") is not None:
                    continue

                if vup.find_parent("i") is not None or vup.find(
                        "i") is not None:
                    status = 0
                else:
                    status = 1

                try:
                    name = vup["title"]

                    if name in names:
                        continue  # 去重，否则可能有重复的结果
                    names.append(name)

                    if unavailable_pattern.search(name) is not None:
                        link = None
                    else:
                        link = "https://zh.moegirl.org.cn{}".format(
                            vup["href"])
                    name = re.sub(r"（.*?）|\(.*?\)", "", name)

                    new_vup = Vup(name, link, status, self)
                    self.vups.append(new_vup)
                    tasks.append(asyncio.create_task(new_vup.get_info()))
                    if link is not None:
                        await asyncio.sleep(3)

                except KeyError:
                    continue

        await asyncio.gather(*tasks)

    def get_json_dict(self):
        json_set = {}
        json_set["name"] = self.name
        json_set["moe_link"] = self.moe_link
        json_set["vups"] = [vup.name for vup in self.vups]
        json_set["bio"] = self.bio
        json_set["picture"] = self.picture
        json_set["bilibili_link"] = self.bilibili_link

        if self.official_vid is not None:
            json_set["official_vid"] = self.official_vid.get_json_dict()
        else:
            json_set["official_vid"] = None
        if self.relative_vid is not None:
            json_set["relative_vid"] = self.relative_vid.get_json_dict()
        else:
            json_set["relative_vid"] = None

        return json_set


class Vup:
    def __init__(self, name, link, status, group) -> None:
        self.name = name
        self.moe_link = link
        self.status = status
        self.group = group

    async def get_info(self):
        try:
            assert self.moe_link is not None

            print(
                "Getting data of {} in {}...".format(
                    self.name, self.group.name))
            get_individual = asyncio.create_task(get_page(self.moe_link))
            individual_response = await get_individual

            individual_response = BeautifulSoup(
                individual_response, "lxml")

            # 拉取信息栏
            info = individual_response.find(
                class_=[
                    "infotemplatebox",
                    "infobox",
                    "infobox2",
                    "infoboxSpecial"]).find("tbody")

            # 获取别名
            try:
                nicknames = info.find("span", itemprop="nickname")
                if nicknames is None:
                    nicknames = info.find(["th", "td"], string=re.compile(
                        r"别号|别名|昵称")).find_next_sibling(["th", "td"])
                if nicknames.find("style") != None:
                    nicknames.find("style").decompose()
                self.nickname = clean_data(nicknames, split=True)
            except AttributeError:
                self.nickname = []

            # 获取萌点
            try:
                moes = info.find(["th", "td"], string=re.compile(
                    "萌点")).find_next_sibling(["th", "td"])
                if moes.find("style") != None:
                    moes.find("style").decompose()
                self.moes = [re.sub(r'\(.*?\)| |（.*?）', "", moe)
                             for moe in clean_data(moes, split=True) if re.sub(r'\(.*?\)| |（.*?）', "", moe) != ""]  # 删除掉萌点中多余的括号与空格
            except AttributeError:
                self.moes = []

            # 获取发色、瞳色
            try:
                hair_color = info.find(
                    ["th", "td"], string=re.compile("发色")).find_next_sibling(["th", "td"])
                iris_color = info.find(
                    ["th", "td"], string=re.compile("瞳色")).find_next_sibling(["th", "td"])
                self.hair_color = clean_data(hair_color)
                self.iris_color = clean_data(iris_color)
            except AttributeError:
                self.hair_color = None
                self.iris_color = None

            # 获取萌娘百科头图链接
            try:
                self.picture = info.find("img")["src"]
            except BaseException:
                self.picture = None

            # 获取简介
            try:
                self.bio = ""
                for tag in individual_response.find(
                        "div", class_="mw-parser-output").find_all("h2", recursive=False)[0].next_siblings:
                    if tag.name == "h2" or tag.name == "h3":
                        break
                    if tag.name == "p" and tag.find(
                            "script") is None and tag.find(
                            "style") is None and tag.string != "\n": # TODO:这种诡异的写法很可能需要重写...
                        self.bio += clean_data(tag) + "\n"
                        continue

                    try:
                        ttag = tag.find("p")
                        if ttag is not None and ttag.find(
                                "script") is None and tag.find(
                                "style") is None and ttag.string != "\n": # TODO:同上
                            self.bio += clean_data(ttag) + "\n"
                    except BaseException:
                        continue

                self.bio = self.bio.rstrip()
            except BaseException:
                self.bio = None

            try:
                # 获取哔哩哔哩个人空间
                self.bilibili_link = individual_response.find(
                    True, class_="mw-headline", string=re.compile(r"外部链接")).find_next(
                    True, href=re.compile(r"https://space\.bilibili\.com/"))["href"]
                self.uid = int(
                    re.search(
                        r"[0-9]+",
                        self.bilibili_link).group())

                try:
                    # 调用哔哩哔哩api
                    usr = user.User(self.uid)
                    get_gender = asyncio.create_task(usr.get_user_info())
                    get_followers = asyncio.create_task(
                        usr.get_relation_info())
                    get_official_video = asyncio.create_task(
                        usr.get_videos(pn=1, ps=1, order=user.VideoOrder.VIEW))
                    get_relative_video = asyncio.create_task(
                        search.search_by_type(
                            keyword=self.name+" 虚拟up主",
                            search_type=search.SearchObjectType.VIDEO,
                            order_type=search.OrderVideo.CLICK))

                    info = await asyncio.gather(get_gender, get_followers, get_official_video, get_relative_video)

                    # 获取本人发布播放量最高视频
                    bvid = info[2]["list"]["vlist"][0]["bvid"]
                    title = info[2]["list"]["vlist"][0]["title"]
                    views = info[2]["list"]["vlist"][0]["play"]
                    self.official_vid = BVideo(bvid, title, views)

                    # 获取全站播放量最高相关视频
                    bvid = info[3]["result"][0]["bvid"]
                    title = re.sub(r'<.*?>', "", info[3]["result"][0]["title"])
                    views = info[3]["result"][0]["play"]
                    self.relative_vid = BVideo(bvid, title, views)

                    # 获取性别、粉丝数
                    self.gender, self.followers = info[0]["sex"], info[1]["follower"]

                except BaseException:
                    self.followers = None
                    self.gender = None
                    self.official_vid = None
                    self.relative_vid = None

            except BaseException:
                self.bilibili_link = None
                self.followers = None
                self.gender = None
                self.official_vid = None
                self.relative_vid = None

        except BaseException:
            self.bio = None
            self.picture = None
            self.nickname = []
            self.moes = []
            self.hair_color = None
            self.iris_color = None
            self.bilibili_link = None
            self.followers = None
            self.gender = None
            self.official_vid = None
            self.relative_vid = None

        print("Finished processing {}.".format(self.name))

    def get_json_dict(self):
        json_set = {}
        json_set["name"] = self.name
        json_set["group"] = self.group.name
        json_set["moe_link"] = self.moe_link
        json_set["bio"] = self.bio
        json_set["picture"] = self.picture
        json_set["nickname"] = self.nickname
        json_set["moes"] = self.moes
        json_set["hair_color"] = self.hair_color
        json_set["iris_color"] = self.iris_color
        json_set["followers"] = self.followers
        json_set["gender"] = self.gender
        json_set["bilibili_link"] = self.bilibili_link

        if self.official_vid is not None:
            json_set["official_vid"] = self.official_vid.get_json_dict()
        else:
            json_set["official_vid"] = None
        if self.relative_vid is not None:
            json_set["relative_vid"] = self.relative_vid.get_json_dict()
        else:
            json_set["relative_vid"] = None

        return json_set


async def get_page(url):
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                print("Getting page {} failed, code {}.".format(
                    url, resp.status))
                raise CancelledError
            return await resp.text()


def clean_data(string, split=False):
    """
    清理字符串中的html标签(并分割其内容)
    """
    string = re.sub(r'<br/>|<br>', "\n", str(string))
    string = re.sub(r'<.*?>|\[.*?\]|\n', "", string)
    if split == True:
        return re.split(r'\.|,| |，|、', string)
    else:
        return string

