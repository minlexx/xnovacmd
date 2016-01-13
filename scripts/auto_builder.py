from threading import Thread


def auto_builder_thread():
    import time
    from enum import Enum
    from ui.xnova.xn_data import XNPlanet, XNPlanetBuildingItem
    from ui.xnova.xn_world import XNovaWorld_instance, XNovaWorld
    from ui.xnova import xn_logger

    class BGid(Enum):
        METAL_FACTORY = 1
        CRYSTAL_FACTORY = 2
        DEIT_FACTORY = 3
        SOLAR_STATION = 4
        FACTORY = 14
        SHIPYARD = 21
        METAL_SILO = 22
        CRYSTAL_SILO = 23
        DEIT_SILO = 24
        LAB = 31

    def check_bonus(world: XNovaWorld):
        bonus_url = world.get_bonus_url()
        if bonus_url is not None:
            logger.info('Detected that bonus is available, get it!')
            world.signal(world.SIGNAL_GET_URL, url=bonus_url, referer='?set=overview')
            time.sleep(10)
            world.clear_bonus_url()
            time.sleep(2)

    def energy_need_for_gid(gid: int, level: int) -> int:
        if (gid == 1) or (gid == 2) or (gid == 12):
            e = (10 * level) * (1.1 ** level)
            return round(e)
        if gid == 3:
            e = (30 * level) * (1.1 ** level)
            return round(e)
        return -1

    def check_planet_buildings(world: XNovaWorld, planet: XNPlanet)
        # is there any building in progress on planet now?
        build_in_progress = False
        bitem = XNPlanetBuildingItem()
        for bitem_ in planet.buildings_items:
            if bitem_.is_in_progress():
                build_in_progress = True
                bitem = bitem_
                break
        if build_in_progress:
            logger.info('{0} has still build in progress {1} lv {2}'.format(
                    planet.name, bitem.name, bitem.level+1))
            return
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
            gid = 0
            level = 0
            bitem = XNPlanetBuildingItem()

        # maybe we are at the end of queue?
        if (gid == 0) or (level == 0) or (bitem.build_link is None):
            logger.info('Seems we have built all the queue!')
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

    logger = xn_logger.get('auto_builder', debug=True)

    world = XNovaWorld_instance()
    world.script_command = 'running'

    WORK_INTERVAL = 60  # seconds
    last_work_time = time.time() - WORK_INTERVAL

    logger.info('Started.')

    while True:
        time.sleep(1)
        if world.script_command == 'stop':
            break

        cur_time = time.time()
        if cur_time - last_work_time >= WORK_INTERVAL:
            last_work_time = cur_time
            # logger.debug('{0} seconds have passed, working...'.format(WORK_INTERVAL))
            check_bonus(world)
            planets = world.get_planets()
            if len(planets) < 1:
                continue
            for planet in planets:
                check_planet_buildings(world, planet)
        # if we didn't sleep long enough for a work_interval
    # while True

    del world.script_command

    logger.info('Stopped.')


# start script as a parallel thread
thr = Thread(target=auto_builder_thread, name='auto_builder_thread')
thr.daemon = False
thr.start()
