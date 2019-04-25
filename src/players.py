from config.conf import base_sofifa_url, max_player_2019
from bs4 import BeautifulSoup
import os
import requests
import re
from utils.urls import reconstruct_url_player


class Player(object):
    def __init__(self, player_uri, date=None):
        self.player_url = reconstruct_url_player(player_uri=player_uri, date=date)
        self.req = requests.get(self.player_url)
        assert self.req.status_code in [200], "[Html error] code %d" % self.req.status_code
        self.raw_data = self.req.text
        assert self.req.url == self.player_url, "[html ERROR] Your player not Found : url %s" % self.player_url
        self.soup_data = BeautifulSoup(self.raw_data, features="html.parser")

    def get_center_class(self):
        center = self.soup_data.findAll("div", {"class": "center"})
        assert len(center) == 1, "[Multiple Centers] %d" % len(center)
        return center[0]

    def get_article(self):
        """

        :return: all element of article
        """
        return self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 1}, {"html": 'article'}],
                                   html=self.raw_data)[0][0]

    def get_info(self):
        seen_key = 0
        info = self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 1}, {"html": 'article'},
                                         {"html": "div", "class": "info"}],
                                   html=self.raw_data)[0][0][0]
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
        res['flag_url'] = meta_soup.find('img')['data-src']
        res['position'] = [spn.text for spn in meta_soup.find_all('span')]
        res['other_info'] = meta_soup.text

        # get card stats
        g_card_stats = self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 1}, {"html": 'article'},
                                                 {"html": "div", "class": "card-body stats"}],
                                           html=self.raw_data)[0][0][0]
        g_card_stats_soup = BeautifulSoup(g_card_stats, features="html.parser")
        for k, spn in zip(["overall_rating", "potential", "value", "wage"], g_card_stats_soup.find_all('span')):
            if k in res:
                k = "%s_%d" % (k, seen_key)
                seen_key += 1
            res[k] = spn.text

        teams = self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 1}, {"html": 'article'},
                                          {"html": "div", "class": "teams"}],
                                    html=self.raw_data)[0][0][0]
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
        res['skills'] = [t.text for t in teams_soup.find_all('a', {"class": "label"})]
        mt_2mb_2 = self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 1}, {"html": 'article'},
                                             {"html": "div", "class": "mt-2 mb-2"}],
                                       html=self.raw_data)[0][0][0]

        mt_2mb_2_soup = BeautifulSoup(mt_2mb_2, features="html.parser")
        for li in mt_2mb_2_soup.find_all("li"):
            span = BeautifulSoup(str(li), features="html.parser").find_all("span")
            if len(span) == 2:
                key = span[1].text
                if key in res:
                    key = "%s_%d" % (key, seen_key)
                    seen_key += 1
                res[key] = span[0].text

        mb_2 = self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 2}, {"html": 'article'},
                                         {"html": "div", "class": "mb-2", "n_items": 3}],
                                   html=self.raw_data)[0][0][2]

        # print(mb_2)
        mb_2_soup = BeautifulSoup(mb_2, features="html.parser")
        for li in mb_2_soup.find_all("li"):
            span = BeautifulSoup(str(li), features="html.parser").find_all("span")

            if len(span) == 2:
                key = span[1].text
                if key in res:
                    key = "%s_%d" % (key, seen_key)
                    seen_key += 1
                res[key] = span[0].text
            else:

                if "traits" not in res:
                    res["traits"] = []
                if li.text == span[0].text:

                    res['traits'].append(span[0].text)
                else:
                    key = li.text.replace(span[0].text, "").strip()
                    if key in res:
                        key = "%s_%d" % (key, seen_key)
                        seen_key += 1
                    res[key] = span[0].text

        # unknow field filled
        res["play_team"] = res["unknow_fields_team_0"]
        del res['unknow_fields_team_0']

        # TODO : make <aside> available and verify if all keys are unique
        # TODO : clean field (put right type, parse date to datetime, int, put team link)

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


class Players(object):
    """

    """

    def __init__(self, date=None):
        if date:
            self.players_url = reconstruct_url_player("players/", date=date) + "&offset=%d"
        else:
            self.players_url = base_sofifa_url + "players?offset=%d"
        self.req = requests.get(self.players_url % 0)
        assert self.req.status_code in [200], "[Html error] code %d" % self.req.status_code
        assert self.req.url == self.players_url % 0, "[html ERROR] Your player not Found : url %s" % (
                self.players_url % 0)
        self.raw_data = self.req.text
        self.soup_data = BeautifulSoup(self.raw_data, features="html.parser")
        self.header = self.get_header()

    def get_header(self):
        """

        :return:
        """
        header = self.soup_data.find('article').find('thead').find("tr", {"class": 'persist-header'}).find_all('th')
        header = [h.text.strip() for h in header]
        header[0] = "avatar"
        return header

    def get_players(self, offset):
        """

        :param offset: into 2019 the max offset are 18077
        :return: players
        """
        req = requests.get(self.players_url % offset)
        assert req.status_code in [200], "[Html error] code %d" % req.status_code
        assert self.req.url == self.players_url % offset, "[html ERROR] Your player not Found : url %s" % (
                self.players_url % offset)
        raw_data = req.text
        soup_data = BeautifulSoup(raw_data, features="html.parser")
        players_offset = soup_data.find('article').find('tbody').find_all("tr")

        def player_feat(play):
            res = []
            player_face = play[0].find('img').get('data-src')
            res.append(player_face)

            player_name_field = play[1].find_all('a')

            tmp = {'title_nat': player_name_field[0].get('title'),
                   "href": player_name_field[0].get('href'),
                   "flag": player_name_field[0].find('img').get('data-src'),
                   'player_href': player_name_field[1].get('href'),
                   "player_name": player_name_field[1].get('title')}

            player_name_position = [(a.get('href'), a.text.strip()) for a in
                                    play[1].find('div', {'class': "text-ellipsis rtl"}).find_all('a')]
            tmp["position"] = player_name_position
            res.append(tmp)

            age = play[2].text.strip()
            res.append(age)

            ova = play[3].text.strip()
            res.append(ova)

            pot = play[4].text.strip()
            res.append(pot)

            player_team = play[5]
            tmp = {"team_flag": player_team.find('img').get('data-src'),
                   "team_href": player_team.find('a').get("href"),
                   "team_name": player_team.find('a').text.strip(),
                   'contract': player_team.find('div', {"class": "subtitle text-ellipsis rtl"}).text.strip()}

            res.append(tmp)
            res.append('UNKN')

            value = play[6].text.strip()
            res.append(value)
            wage = play[7].text.strip()
            res.append(wage)
            res.append('UNKN')
            total_stats = play[8].text.strip()
            res.append(total_stats)
            res.append('UNKN')
            hit_comments = play[9].text.strip()
            res.append(hit_comments)

            return res

        results = {}
        for pl in players_offset:
            pl = player_feat(pl.find_all('td'))
            tmp = {k: v for k, v in zip(self.header, pl)}
            results[tmp['Name'].get('player_name')] = tmp

        return results

    def get_all_players(self, verbose=0):
        result_all = {}
        number_offset = max_player_2019 // 60
        for off in range(number_offset):
            offset = 60 * off
            res = self.get_players(offset)
            for k in res:
                tmp_k = k
                count = 0
                while k in result_all:
                    k = k + " %d" % count
                result_all[k] = res[tmp_k]
            if verbose:
                print("Number of players %d" % len(result_all))
                print('Offset number %d/%d' % (off, number_offset))
        return result_all
