from unittest import TestCase
from datetime import datetime
from utils import urls as module


class TestUrls(TestCase):
    def setUp(self):
        pass

    def test_url_player_no_date(self):
        actual = module.reconstruct_url_player("player/158023/lionel-messi/")
        expected = "https://sofifa.com/player/158023/lionel-messi/"
        self.assertEqual(actual, expected)

    def test_url_player(self):
        d = datetime(2019, 4, 18)
        actual = module.reconstruct_url_player("player/158023/lionel-messi/", d)
        expected = "https://sofifa.com/player/158023/lionel-messi/?v=19&e=159432&set=true"
        self.assertEqual(actual, expected)

    def test_url_nearest(self):
        d = datetime(2019, 4, 19)
        actual = module.reconstruct_url_player("player/158023/lionel-messi/", d)
        expected = "https://sofifa.com/player/158023/lionel-messi/?v=19&e=159432&set=true"
        self.assertEqual(actual, expected)

    def test_url_not_found(self):
        d = datetime(2006, 1, 1)
        with self.assertRaises(module.DateNotFound) as cm:
            module.reconstruct_url_player("player/158023/lionel-messi/", d)
