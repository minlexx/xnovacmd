import re


# this module will define/keep all static Xnova data models
# and basic classes


# XNova universe coordinates model
# [galaxy:solarsystem:planet]
class XNCoords:
    def __init__(self):
        self.galaxy = 0
        self.system = 0
        self.position = 0

    def __str__(self):
        return '[{0}:{1}:{2}]'.format(self.galaxy, self.system, self.position)

    def set_gsp(self, g: int, s: int, p: int):
        self.galaxy = g
        self.system = s
        self.position = p

    def parse_str(self, s: str):
        # '[1:23:456]'
        match = re.match('^\[(\d+):(\d+):(\d+)\]$', s)
        if match:
            self.galaxy = int(match.group(1))
            self.system = int(match.group(2))
            self.position = int(match.group(3))
        else:
            # '1:23:456'
            match = re.match('^(\d+):(\d+):(\d+)$', s)
            if match:
                self.galaxy = int(match.group(1))
                self.system = int(match.group(2))
                self.position = int(match.group(3))
            else:
                raise ValueError('XCoords parse error', s)


class XNovaAccountScores:
    def __init__(self):
        self.rank = 0
        self.rank_delta = 0
        self.buildings = 0
        self.fleet = 0
        self.defense = 0
        self.science = 0
        self.total = 0
        self.industry_level = 0
        self.industry_exp = (0, 0)
        self.military_level = 0
        self.military_exp = (0, 0)
        self.wins = 0
        self.losses = 0
        self.fraction = ''
        self.credits = 0

    def __str__(self):
        return '{0}({1}): {2}'.format(self.rank, str(self.rank_delta), self.total)


class XNovaAccountInfo:
    def __init__(self):
        self.id = 0
        self.login = ''
        self.email = ''
        self.main_planet_name = ''
        self.main_planet_coords = XNCoords()
        self.alliance_name = ''
        self.scrores = XNovaAccountScores()

    def __str__(self):
        return '{0} rank {1}'.format(self.login, self.scrores)
