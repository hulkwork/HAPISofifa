from unittest import TestCase
from src import players as module
from datetime import datetime


# TODO : Put more tests

class Testplayers(TestCase):
    def setUp(self):
        self.uri = "player/236632/david-neres-campos/"

        self.pl = module.Player(self.uri)

    def test_instance_player(self):
        expected = "https://sofifa.com/player/236632/david-neres-campos/"
        actual = self.pl.player_url
        self.assertEqual(expected, actual)

    def test_go_deeper(self):
        lkey = [{"html": "div", "class": "center", "n_items": 1}, {"html": 'article'}]
        self.assertEqual(len(self.pl.go_deeper_html(lkey, self.pl.raw_data)), 1)

    def test_get_info(self):
        print(self.pl.get_info())

    def test_players(self):
        pls = module.Player(self.uri, date=datetime(2019, 4, 23))
        actual = pls.player_url
        expected = "https://sofifa.com/player/236632/david-neres-campos/?v=19&e=159437&set=true"
        self.assertEqual(actual, expected)
