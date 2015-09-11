# -*- coding: utf-8 -*-
import execjs

from .xn_data import XNCoords
from .xn_parser import XNParserBase, safe_int, get_attribute
from . import xn_logger

logger = xn_logger.get(__name__, debug=False)


class GalaxyParser(XNParserBase):
    def __init__(self):
        super(GalaxyParser, self).__init__()
        self._in_galaxy = False
        self.script_body = ''
        self.galaxy_rows = []

    def clear(self):
        self.script_body = ''
        self.galaxy_rows = []

    def handle_starttag(self, tag: str, attrs: list):
        super(GalaxyParser, self).handle_starttag(tag, attrs)
        if tag == 'div':
            # find [<div id='galaxy'>]
            div_id = get_attribute(attrs, 'id')
            if div_id is not None:
                if div_id == 'galaxy':
                    self._in_galaxy = True

    def handle_endtag(self, tag: str):
        super(GalaxyParser, self).handle_endtag(tag)
        if self._in_galaxy and tag == 'script':
            self._in_galaxy = False

    def handle_data2(self, data: str, tag: str, attrs: list):
        if self._in_galaxy and (tag == 'script'):
            self.script_body = data
            # logger.debug('Got galaxy script: [{0}]'.format(self.script_body))
        return  # def handle_data()

    def unscramble_galaxy_script(self):
        if not self.script_body.startswith('var Deuterium = '):
            logger.error('Invalid format of script body: cannot parse it!')
            return None
        eval_start = self.script_body.find('eval(function(p,a,c,k,e,d)')
        if eval_start == -1:
            logger.error('parse error (1)')
            return None
        eval_end = self.script_body.find("$('#galaxy').append(PrintRow());")
        if eval_end == -1:
            logger.error('parse error (2)')
            return None
        eval_text = self.script_body[eval_start:eval_end]
        eval_text = eval_text.strip()
        logger.debug('eval [{0}]'.format(eval_text))
        # ^^ [eval(function(p,a,c,k,e,d){e=function(c){r... ...141|7866|u0426'.split('|')))]
        inner_eval = eval_text[5:-1]
        logger.debug('inner eval [{0}]'.format(inner_eval))
        # ^^ [function(p,a,c,k,e,d){e=functi... ...0426'.split('|'))]
        #
        # create JS interptreter and eval that
        js_runtimes = execjs.available_runtimes()
        if 'Node' in js_runtimes:
            js = execjs.get('Node')
        else:
            js = execjs.get()  # default
        logger.debug('Using [{0}] as JS runtime.'.format(js.name))
        eval_res = js.eval(inner_eval)
        # Now, eval_res is a string:
        # row[12]={"planet":12,"id_planet":54448,"ally_planet":0,"metal":0,"crystal":0,
        # "name":"\u0413\u043b\u0430\u0432\u043d\u0430\u044f \u043f\u043b\u0430\u043d\u0435\u0442\u0430",
        # "planet_type":1,"destruyed":0,"image":"normaltempplanet02","last_active":60,"parent_planet":0,
        # "luna_id":null,"luna_name":null,"luna_destruyed":null,"luna_diameter":null,"luna_temp":null,
        # "user_id":71992,"username":"\u041e\u041b\u0415\u0413 \u041a\u0410\u0420\u041f\u0415\u041d\u041a\u041e",
        # "race":4,"ally_id":0,"authlevel":0,"onlinetime":1,"urlaubs_modus_time":0,"banaday":0,"sex":1,
        # "avatar":7,"user_image":"","ally_name":null,"ally_members":null,"ally_web":null,"ally_tag":null,
        # "type":null,"total_rank":7865,"total_points":0};row[9]={"planet":9,"id_planet":54450,"ally_planet":0,
        # "metal":0,"crystal":0,"name":"Arnon","planet_type":1,"destruyed":0,"image":"normaltempplanet08",
        # "last_active":0,"parent_planet":0,"luna_id":null,"luna_name":null,"luna_destruyed":null,
        # "luna_diameter":null,"luna_temp":null,"user_id":71995,"username":"minlexx","race":4,"ally_id":389,
        # "authlevel":0,"onlinetime":0,"urlaubs_modus_time":0,"banaday":0,"sex":1,"avatar":5,
        # "user_image":"71995_1440872455.jpg","ally_name":"Fury","ally_members":8,"ally_web":"",
        # "ally_tag":"Fury","type":null,"total_rank":141,"total_points":115582};
        # ...
        # we ned to eval() this string again, slightly modified, to get resulting row:
        eval_res = 'var row = []; ' + eval_res + "\nreturn row;"
        ctx = js.compile(eval_res)
        self.galaxy_rows = ctx.exec_(eval_res)
        # print(type(self.galaxy_rows))
        # print(self.galaxy_rows)
        # <class 'list'>
        # [None, None, None, None, None, None, None,
        # {
        #   'type': None,
        #   'planet_type': 1,
        #   'total_points': 0,
        #   'ally_planet': 0,
        #   'ally_web': None,
        #   'urlaubs_modus_time': 0,
        #   'crystal': 0,
        #   'user_id': 71993,
        #   'name': 'Главная планета',
        #   'ally_tag': None,
        #   'last_active': 60,
        #   'luna_name': None,
        #   'planet': 7,
        #   'luna_diameter': None,
        #   'ally_id': 0,
        #   'onlinetime': 1,
        #   'luna_id': None,
        #   'parent_planet': 0,
        #   'sex': 1,
        #   'ally_name': None,
        #   'avatar': 8,
        #   'user_image': '',
        #   'destruyed': 0,
        #   'banaday': 0,
        #   'luna_temp': None,
        #   'race': 4,
        #   'image': 'normaltempplanet09',
        #   'username': 'Дмитрий и Марина Цыкуновы',
        #   'luna_destruyed': None,
        #   'metal': 0,
        #   'id_planet': 54449,
        #   'authlevel': 0,
        #   'ally_members': None,
        #   'total_rank': 7866
        # },
        # None, ... ]
