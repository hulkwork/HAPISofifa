from unittest import TestCase

from src import teams as module


# TODO : Put more tests

class Testplayers(TestCase):
    def setUp(self):
        self.team = module.Team(team_uri='team/245/ajax/')

    def test_instance_team(self):
        print(self.team.get_info())