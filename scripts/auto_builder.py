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
    FACTORY = 14
    SHIPYARD = 21
    METAL_SILO = 22
    CRYSTAL_SILO = 23
    DEIT_SILO = 24

    buildings_queue = list()  # gid, level
    #
    buildings_queue.append([FACTORY, 1])
    buildings_queue.append([FACTORY, 2])
    #
    for i in range(5):  # base mining plants to level 5
        buildings_queue.append([SOLAR_STATION, i+1])
        buildings_queue.append([METAL_FACTORY, i+1])
        buildings_queue.append([CRYSTAL_FACTORY, i+1])
    #
    buildings_queue.append([SHIPYARD, 1])
    buildings_queue.append([SHIPYARD, 2])
    #
    for i in range(5): # base mining plants to level 10
        buildings_queue.append([SOLAR_STATION, i+6])
        buildings_queue.append([METAL_FACTORY, i+6])
        buildings_queue.append([CRYSTAL_FACTORY, i+6])
    # silos
    buildings_queue.append([METAL_SILO, 1])
    buildings_queue.append([CRYSTAL_SILO, 1])
    buildings_queue.append([DEIT_SILO, 1])

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
            bitem = XNPlanetBuildingItem()
            for bitem_ in planet.buildings_items:
                if bitem_.is_in_progress():
                    build_in_progress = True
                    bitem = bitem_
                    break
            if build_in_progress:
                logger.info('{0} has still build in progress {1}'.format(planet.name, bitem.name))
                continue

            # no builds in progress, we can continue
            # find the first building in a queue that is not present on the planet
            gid = 0
            level = 0
            bitem = XNPlanetBuildingItem()
            for queue_item in buildings_queue:
                gid = queue_item[0]
                level = queue_item[1]
                is_present = True
                for bitem_ in planet.buildings_items:
                    if bitem_.gid == gid:  # the same building type, check level
                        if bitem_.level < level:  # AHA! level too low?
                            is_present = False
                            bitem = bitem_
                            break
                if not is_present:
                    break

            # maybe we are at the end of queue?
            if (gid == 0) and (level == 0):
                logger.info('Seemd we have build all!')
                break

            logger.info('Next building in a queue: {0} lv {1}'.format(bitem.name, level))
            logger.info('Its build_Link is: [{0}]'.format(bitem.build_link))
            logger.info('Its price: {0}m {1}c {2}d'.format(bitem.cost_met, bitem.cost_cry, bitem.cost_deit))
            logger.info('We have: {0}m {1}c {2}d'.format(int(planet.res_current.met),
                                                         int(planet.res_current.cry),
                                                         int(planet.res_current.deit)))
            # do we have enough resources to build it?
            if (planet.res_current.met >= bitem.cost_met) and \
                    (planet.res_current.cry >= bitem.cost_cry) and \
                    (planet.res_current.deit >= bitem.cost_deit):
                logger.info('We have enough resources to build it, trigger!')
                world.signal(world.SIGNAL_BUILD_ITEM,
                             planet_id=planet.planet_id,
                             bitem=bitem,
                             quantity=0)
                logger.info('Signal to build this item has been sent to world thread, wait...')
            else:
                logger.warn('We DO NOT have enough resources to build it =( Wait...')
        # if we didn't sleep long enough for a work_interval
    # while True

    del world.script_command

    logger.info('Stopped.')


# start script as a parallel thread
thr = Thread(target=printer_thread, name='Printer_thread')
thr.daemon = False
thr.start()
