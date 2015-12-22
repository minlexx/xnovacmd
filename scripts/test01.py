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

    # logger.info('Planets:')
    # for planet in planets:
    #    logger.info('{0}'.format(str(planet)))
    # logger.info('End planets.')

    while True:
        time.sleep(1)
        print('   test01 running...')
        if world.script_test01_command == 'stop':
            break

    del world.script_test01_command

    print('Ended test01')


# start script as a parallel thread
thr = Thread(target=printer_thread, name='Printer_thread')
thr.daemon = False
thr.start()
