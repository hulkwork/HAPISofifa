from config.conf import base_sofifa_url
from datetime import datetime
from utils.meta import get_all_filter_date
import os


class VersionNotFound(Exception): pass


class DateNotFound(Exception): pass


FORMAT_DATE = '%d %b  %Y'


def reconstruct_url_player(player_uri, date=None):
    url = os.path.join(base_sofifa_url, player_uri)
    if date:
        filters = get_all_filter_date(older_version=True, write=True)
        assert type(date) == datetime
        date_str = date.strftime(FORMAT_DATE)
        year = str(date.year)
        year_plus_one = str(date.year + 1)
        tag = 'tag-fifa-%s' % year[2:]
        tag_plus_one = 'tag-fifa-%s' % year_plus_one[2:]
        counter_tag = 0
        tags = [tag, tag_plus_one]
        for t in tags:
            if t in filters:
                if date_str in filters[t]:
                    return os.path.join(url, "?%s" % filters[t][date_str]['uri'])

                else:
                    keys = list(filters[t].keys())
                    to_datetime = [datetime.strptime(d, FORMAT_DATE) for d in keys]
                    diff_time = [(date - d).days for d in to_datetime]
                    sort_diff = sorted(range(len(diff_time)), key=lambda k: diff_time[k])
                    for i in sort_diff:
                        if diff_time[i] > 0:
                            date_found = keys[i]
                            return os.path.join(url, "?%s" % filters[t][date_found]['uri'])


            else:
                counter_tag += 1
        if counter_tag == 2:
            raise VersionNotFound("FIFA %s version is not available" % year[2:])
        raise DateNotFound("%s not found into [%s]" % (date_str, ','.join(tags)))

    return url


def reconstruct_url_teams(teams, date=None):
    pass
