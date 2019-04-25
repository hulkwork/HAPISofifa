from unittest import TestCase
from utils.meta import get_all_filter_date


class TestMeta(TestCase):
    def setUp(self):
        pass

    def test_get_meta(self):
        filters = get_all_filter_date()

        self.assertIn('tag-fifa-19', filters)
