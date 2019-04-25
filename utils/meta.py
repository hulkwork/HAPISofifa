from bs4 import BeautifulSoup
import requests
import re
import os
from datetime import datetime
import json

base_file = os.path.dirname(os.path.abspath(__file__))

base_filter_data_file = os.path.join(base_file, "../config/filters.json")


def get_all_filter_date(older_version=False, write=True):
    """

    :param older_version:
    :return:
    """
    assert type(older_version) == bool

    filter = "filter-body columns"
    player_url = "https://sofifa.com/players"
    res = {}
    if os.path.exists(base_filter_data_file):
        with open(base_filter_data_file) as f:
            res = json.load(f)
        if older_version:
            return res

    req = requests.get(player_url)
    assert req.status_code in [200], "[Html error] code %d" % req.status_code
    raw_data = req.text
    soup_data = BeautifulSoup(raw_data, features="html.parser")
    filters = soup_data.find('div', {"class": filter}).find_all("div", {"class": "column col-4"})

    for fil in filters:
        version = fil.get('data-tag')
        if version not in res:
            res[version] = {}
        month_year = fil.find('div', {"class": "card-header"}).text.strip()
        dates = fil.find('div', {"class": "card-body"}).find_all('a')
        reg = r"/players\?v=(?P<v>[0-9]+)\&e=(?P<e>[0-9]+)&set=(?P<set>[a-z]+)"
        for d in dates:
            reg_match = re.match(reg, d.get('href'))
            reg_res = reg_match.groupdict()
            reg_res['uri'] = "&".join(["%s=%s" % (k, reg_res[k]) for k in reg_res])
            dt = "%s %s" % (d.text.strip(), month_year)
            dt_ = datetime.strptime(dt, "%d %b  %Y")
            res[version][dt] = reg_res

    res['_version'] = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    if write:
        with open(base_filter_data_file, 'w') as f:
            json.dump(res, f, indent=4)
    return res
