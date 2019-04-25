from config.conf import base_sofifa_url
from bs4 import BeautifulSoup
import os
import requests
import re


class Team(object):
    def __init__(self, team_uri, date=None):
        self.player_url = os.path.join(base_sofifa_url, team_uri)
        self.req = requests.get(self.player_url)
        assert self.req.status_code in [200], "[Html error] code %d" % self.req.status_code
        self.raw_data = self.req.text
        self.soup_data = BeautifulSoup(self.raw_data, features="html.parser")

    def get_article(self):
        """

        :return: all element of article
        """
        return self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 1}, {"html": 'article'}],
                                   html=self.raw_data)[0][0]

    def get_info(self):
        seen_key = 0
        info = self.go_deeper_html(lkey=[{"html": "body", "class": "is-preload"}
            , {"html": "div", "class": "center", "n_items": 1}, {"html": 'article'}, {"html": "div", "class": "info"}],
                                   html=self.raw_data)[0][0][0][0]

        # Get Name and id
        infos_name = self.go_deeper_html(lkey=[{'html': "h1"}],
                                         html=info)[0]
        name_id_pattern = r'(?P<name>[A-Za-z\s]+)\(ID:\s(?P<ID>[0-9]+)\)'
        str_name = BeautifulSoup(infos_name, features="html.parser").find('h1').text
        reg_match = re.match(name_id_pattern, str_name)
        res = reg_match.groupdict()
        # Get Name and id
        meta_info = self.go_deeper_html([{"html": "div", 'class': "meta"}], info)[0]
        meta_soup = BeautifulSoup(meta_info, features="html.parser")

        for a in meta_soup.find_all("a"):
            if "na" in a['href']:
                res['national_uri'] = a['href']
            if "lg" in a['href']:
                res['league_uri'] = a['href']
        res['league_name'] = meta_soup.text.strip()

        # get card stats
        g_card_stats = self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 1}, {"html": 'article'},
                                                 {"html": "div", "class": "card-body stats"}],
                                           html=self.raw_data)[0][0][0]
        g_card_stats_soup = BeautifulSoup(g_card_stats, features="html.parser")

        for k, spn in zip(["overall", "attack", "Midfield", "Defence"], g_card_stats_soup.find_all('span')):
            if k in res:
                k = "%s_%d" % (k, seen_key)
                seen_key += 1
            res[k] = spn.text

        teams = self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 1}, {"html": 'article'},
                                          {"html": "div", "class": "teams"}],
                                    html=self.raw_data)[0][0][0]
        teams_soup = BeautifulSoup(teams, features="html.parser")

        res['player_in_fields'] = []
        for player in teams_soup.find_all('div', {"class": "field-player"}):
            pl = player.find("a")
            player_img = player.find('span').find('img')['data-src']
            tmp_player = {"player_name": pl.text.strip(), "player_uri": pl['href'], 'position_infield': player['style'],
                          'player_img': player_img}
            res['player_in_fields'].append(tmp_player)

        teams_soup = BeautifulSoup(teams, features="html.parser")
        unk_count = 0
        for li in teams_soup.find_all('li'):
            label = li.find_all('label')

            if len(label) != 1:
                res['unknow_fields_team_%d' % unk_count] = li.text.strip()
                unk_count += 1
            else:

                label_soup = BeautifulSoup(str(label[0]), features="html.parser")
                key = label_soup.text
                if key in res:
                    key = "%s_%d" % (key, seen_key)
                    seen_key += 1
                res[key] = li.text.replace(label_soup.text, "").strip()
        header_squad = self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 1}, {"html": 'article'},
                                                 {"html": "thead"}], html=self.raw_data)[0][0][0]

        header_squad_soup = BeautifulSoup(header_squad, features="html.parser")
        header = [h.text.strip() for h in header_squad_soup.find("tr", {"class": "persist-header"}).find_all('th')]
        header[0] = "avatar"
        squad = self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 1}, {"html": 'article'},
                                          {"html": "tbody"}], html=self.raw_data)[0][0][0]
        tbody_soup = BeautifulSoup(squad, features="html.parser")

        def player_teams(player_status, ):
            starting_team = tbody_soup.find_all('tr', {"class": player_status})
            pl_status = []
            for st_pl in starting_team:
                fields = st_pl.find_all('td')
                tmp_fields = [f.text.strip() for f in fields]
                tmp_fields[0] = fields[0].find('img')['data-src']
                tmp_start = {}
                for k, field in zip(header, tmp_fields):
                    tmp_start[k] = field
                del tmp_start['']
                pl_status.append(tmp_start)
            return pl_status

        res["starting_player"] = player_teams("starting")
        res["sub_player"] = player_teams("sub")
        res["res_player"] = player_teams("res")

        # TODO : make <aside> available and verify if all keys are unique
        # TODO : clean field (put right type, parse date to datetime, int, put team link)
        # TODO :  Do same class with teams

        return {k.lower().replace(" ", "_"): res[k] for k in res}

    def get_aside(self):
        """

        :return: all element of aside
        """
        return self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 1}, {"html": 'aside'}],
                                   html=self.raw_data)[0][0]

    def go_deeper_html(self, lkey, html):
        """

        :param lkey:list of keys and attribute we need (Warning : an order of keys are important)
        lkey = [{"html" : "div", "class" : "center" , "n_items" : 1}]
        :param html: html content in string
        :return:
        """
        if len(lkey) == 1:
            k = lkey[0]

            n_items = k.get("n_items", 1)
            html_balise = k['html']
            html_class = k.get("class", {})
            return [str(s) for s in
                    BeautifulSoup(html, features="html.parser").find_all(name=html_balise, attrs=html_class)[:n_items]]
        return [self.go_deeper_html(lkey[1:], s) for s in self.go_deeper_html([lkey[0]], html)]
