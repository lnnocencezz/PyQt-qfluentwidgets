# -*- coding: utf-8 -*-
# Author    ： ly
# Datetime  ： 2023/11/6 16:10
# coding='utf-8'
from lxml import etree

import requests


class GameData:
    def __init__(self, url):
        self.url = url
        self.links = self.get_links()

    def get_links(self):
        response = requests.get(url=self.url)

        html_data = response.text
        res = etree.HTML(html_data)

        links = res.xpath("//a[@class='d']/@href")
        return links

    @staticmethod
    def get_team_names(teams):
        home_team = away_team = None
        for team in teams:
            if '主队' in team:
                home_team = team.split('（')[0]
            elif '客队' in team:
                away_team = team.split('（')[0]
        return home_team, away_team

    def parse_links(self):
        players = []
        scores = []
        for link in self.links:
            score_data = {}
            resp = requests.get(link)
            html = etree.HTML(resp.text)
            # 客队
            teams = html.xpath('//div[contains(@class, "clearfix")]/h2/text()')
            home_team, away_team = self.get_team_names(teams)
            away_score = html.xpath(
                '//div[contains(@class, "team_vs_box")]//div[contains(@class, "team_a")]//div[contains(@class, "message")]/h2/text()')
            home_score = html.xpath(
                '//div[contains(@class, "team_vs_box")]//div[contains(@class, "team_b")]//div[contains(@class, "message")]/h2/text()')
            away_rows = html.xpath('//table[@id="J_away_content"]/tbody/tr[position()>1]')
            # 主队
            home_rows = html.xpath('//table[@id="J_home_content"]/tbody/tr[position()>1]')
            away_data = self.filter_data(away_rows, away_team)
            home_data = self.filter_data(home_rows, home_team)

            players.extend(away_data)
            players.extend(home_data)
            # 对players整体排序
            players.sort(key=lambda x: float(x[-1]), reverse=True)
            if home_team and away_team:
                score_data = {'home_team': home_team, 'home_score': home_score[0], 'away_team': away_team,
                              'away_score': away_score[0]}
                scores.append(score_data)
        game_data = {"players": players, "scores": scores}
        return game_data

    @staticmethod
    def filter_data(rows, team_name):
        base_data = []
        filter_data = []
        for row in rows:
            # 统计所有td
            name_list = row.xpath('./td[@class="tdw-1 left"]/a/text()')
            if name_list:
                name = name_list[0]
            else:
                name = ""
            # 得分
            pts_td = row.xpath('./td[15]')[0]
            pts = pts_td.xpath('./span[@class="high"]/text()')
            if pts:
                pts = pts[0]
            else:
                pts = pts_td.text.strip()
            # 效率值
            ef_td = row.xpath('./td[16]')[0]
            ef = ef_td.xpath('./span[@class="high"]/text()')
            if ef:
                ef = ef[0]
            else:
                ef = ef_td.text.strip()
            # 篮板
            reb_td = row.xpath('./td[9]')[0]
            reb = reb_td.xpath('./span[@class="high"]/text()')
            if reb:
                reb = reb[0]
            else:
                reb = reb_td.text.strip()
            # 助攻
            ast_td = row.xpath('./td[10]')[0]
            ast = ast_td.xpath('./span[@class="high"]/text()')
            if ast:
                ast = ast[0]
            else:
                ast = ast_td.text.strip()
            # 抢断
            stl_td = row.xpath('./td[12]')[0]
            stl = stl_td.xpath('./span[@class="high"]/text()')
            if stl:
                stl = stl[0]
            else:
                stl = stl_td.text.strip()
            # 盖帽
            blk_td = row.xpath('./td[14]')[0]
            blk = blk_td.xpath('./span[@class="high"]/text()')
            if blk:
                blk = blk[0]
            else:
                blk = blk_td.text.strip()
            # 失误
            to_td = row.xpath('./td[13]')[0]
            to = to_td.xpath('./span[@class="high"]/text()')
            if to:
                to = to[0]
            else:
                to = to_td.text.strip()
            # 犯规
            fault_td = row.xpath('./td[11]')[0]
            fa = fault_td.xpath('./span[@class="high"]/text()')
            if fa:
                fa = fa[0]
            else:
                fa = fault_td.text.strip()

            # 23 , 1,  6, 0, 1 , 2
            if name == '' or pts == '0':
                continue
            cp = int(pts) + int(reb) * 1.2 + int(ast) * 1.5 + int(stl) * 3 + int(blk) * 3 - int(to)
            cp = str(round(cp, 2))
            base_data.append([name, team_name, pts, reb, ast, stl, blk, to, fa, ef, cp])
            # 去掉得分低于5分的
            filter_data = [player for player in base_data if int(player[2]) >= 1]
        return filter_data


if __name__ == '__main__':
    from datetime import datetime

    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    url = f'https://nba.hupu.com/games/{today_str}'
    data = GameData(url).parse_links()
    # print(data['scores'])
