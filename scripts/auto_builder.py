from threading import Thread


def printer_thread():
    import time

    from ui.xnova.xn_data import XNPlanet, XNPlanetBuildingItem
    from ui.xnova.xn_world import XNovaWorld_instance
    from ui.xnova import xn_logger

    logger = xn_logger.get('auto_builder', debug=True)
    world = XNovaWorld_instance()

    world.script_command = 'running'

    logger.info('Started.')

    my_planet_id = 82160
    WORK_INTERVAL = 20  # seconds
    last_work_time = time.time() - WORK_INTERVAL

    METAL_FACTORY = 1
    CRYSTAL_FACTORY = 2
    DEIT_FACTORY = 3
    SOLAR_STATION = 4

    buildings_queue = list()  # gid, level
    buildings_queue.append([SOLAR_STATION, 1])
    buildings_queue.append([METAL_FACTORY, 1])
    buildings_queue.append([CRYSTAL_FACTORY, 1])
    #
    buildings_queue.append([SOLAR_STATION, 2])
    buildings_queue.append([METAL_FACTORY, 2])
    buildings_queue.append([CRYSTAL_FACTORY, 2])
    #
    buildings_queue.append([SOLAR_STATION, 3])
    buildings_queue.append([METAL_FACTORY, 3])
    buildings_queue.append([CRYSTAL_FACTORY, 3])
    #
    buildings_queue.append([SOLAR_STATION, 4])
    buildings_queue.append([METAL_FACTORY, 4])
    buildings_queue.append([CRYSTAL_FACTORY, 4])
    #
    buildings_queue.append([SOLAR_STATION, 5])
    buildings_queue.append([METAL_FACTORY, 5])
    buildings_queue.append([CRYSTAL_FACTORY, 5])

    while True:
        time.sleep(1)
        if world.script_command == 'stop':
            break

        cur_time = time.time()
        if cur_time - last_work_time >= WORK_INTERVAL:
            last_work_time = cur_time
            # do work
            logger.debug('{0} seconds have passed, working...'.format(WORK_INTERVAL))
            planet = world.get_planet(my_planet_id)
            if planet is None:
                continue

            logger.debug('got my planet: {0}'.format(planet))

            # is there any building in progress on planet now?
            build_in_progress = False
            bitem_in_progress = XNPlanetBuildingItem()
            for bitem in planet.buildings_items:
                if bitem.is_in_progress():
                    build_in_progress = True
                    bitem_in_progress = bitem
                    break
            if build_in_progress:
                logger.info('{0} has still build in progress {1}'.format(planet.name, bitem_in_progress.name))
                continue

            # no builds in progress, we can continue
            # find the first building in a queue that is not present on the planet
            gid = 0
            level = 0
            for queue_item in buildings_queue:
                gid = queue_item[0]
                level = queue_item[1]
                is_present = True
                for bitem in planet.buildings_items:
                    if bitem.gid == gid:  # the same building type, check level
                        if bitem.level < level:  # AHA! level too low?
                            is_present = False
                            break
                if not is_present:
                    break

            logger.info('Next building in a queue: {0} lv {1}'.format(gid, level))

    del world.script_command

    logger.info('Stopped.')


# start script as a parallel thread
thr = Thread(target=printer_thread, name='Printer_thread')
thr.daemon = False
thr.start()
