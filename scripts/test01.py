from threading import Thread


def printer_thread():
    import time
    from ui.xnova.xn_data import XNPlanet
    from ui.xnova.xn_world import XNovaWorld_instance
    from ui.xnova import xn_logger

    logger = xn_logger.get('test01', debug=True)
    world = XNovaWorld_instance()
    planets = world.get_planets()

    world.script_test01_command = 'running'

    logger.info('Started.')

    # logger.info('Planets:')
    # for planet in planets:
    #    logger.info('{0}'.format(str(planet)))
    # logger.info('End planets.')

    while True:
        time.sleep(1)
        # print('   test01 running...')
        if world.script_test01_command == 'stop':
            break

        if world.script_test01_command == 'pn':
            planet_id = planets[0].planet_id
            post_url = '?set=overview&mode=renameplanet&pl={0}'.format(planet_id)
            post_data = dict()
            # post_data['action'] = 'Покинуть колонию'
            post_data['action'] = 'Сменить название'
            post_data['newname'] = 'XX9-WV'
            referer = 'http://uni4.xnova.su/?set=overview&mode=renameplanet'
            world._page_downloader.post(post_url, post_data=post_data, referer=referer)
            logger.debug('Rename planet complete to [{0}]'.format(post_data['newname']))
            # clear command
            world.script_test01_command = 'running'

    del world.script_test01_command

    logger.info('Stopped.')


# start script as a parallel thread
thr = Thread(target=printer_thread, name='Printer_thread')
thr.daemon = False
thr.start()
