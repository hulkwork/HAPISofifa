from config.conf import base_sofifa_url
from bs4 import BeautifulSoup
import os
import requests
import re


class Player(object):
    def __init__(self, player_uri):
        self.player_url = os.path.join(base_sofifa_url, player_uri)
        self.req = requests.get(self.player_url)
        assert self.req.status_code in [200], "[Html error] code %d" % self.req.status_code
        self.raw_data = self.req.text
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
                res[label_soup.text] = li.text.replace(label_soup.text, "").strip()
        res['skills'] = [t.text for t in teams_soup.find_all('a', {"class":"label"})]
        mt_2mb_2 = self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 1}, {"html": 'article'},
                                          {"html": "div", "class": "mt-2 mb-2"}],
                                    html=self.raw_data)[0][0][0]

        mt_2mb_2_soup = BeautifulSoup(mt_2mb_2, features="html.parser")
        for li in mt_2mb_2_soup.find_all("li"):
            span = BeautifulSoup(str(li), features="html.parser").find_all("span")
            if len(span) ==2:
                res[span[1].text] = span[0].text

        mb_2 = self.go_deeper_html(lkey=[{"html": "div", "class": "center", "n_items": 2}, {"html": 'article'},
                                          {"html": "div", "class": "mb-2", "n_items" : 3}],
                                    html=self.raw_data)[0][0][2]

        # print(mb_2)
        mb_2_soup = BeautifulSoup(mb_2, features="html.parser")
        for li in mb_2_soup.find_all("li"):
            span = BeautifulSoup(str(li), features="html.parser").find_all("span")

            if len(span) == 2:
                res[span[1].text] = span[0].text
            else:

                if "traits" not in res:
                    res["traits"] = []
                if li.text == span[0].text:

                    res['traits'].append(span[0].text)
                else:
                    res[li.text.replace(span[0].text,"").strip()] = span[0].text

        print(res["traits"])


        return res

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
