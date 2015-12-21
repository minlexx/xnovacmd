from threading import Thread


def printer_thread():
    import time
    from ui.xnova.xn_data import XNPlanet
    from ui.xnova.xn_world import XNovaWorld_instance
    from ui.xnova import xn_logger

    logger = xn_logger.get('test01', debug=True)
    world = XNovaWorld_instance()
    planets = world.get_planets()

    logger.info('Planets:')
    for planet in planets:
        logger.info('{0}'.format(str(planet)))
    logger.info('End planets.')

    for i in range(5):
        time.sleep(1)
        print('   printer: {0}'.format(i))
    print('End printer')


# start script as a parallel thread
thr = Thread(target=printer_thread, name='Printer_thread')
thr.daemon = False
thr.start()
