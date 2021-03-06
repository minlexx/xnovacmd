from threading import Thread


def auto_builder_thread():
    import time
    from enum import IntEnum
    from ui.xnova.xn_data import XNPlanet, XNPlanetBuildingItem
    from ui.xnova.xn_world import XNovaWorld_instance, XNovaWorld
    from ui.xnova.xn_techtree import XNTechTree_instance
    from ui.xnova import xn_logger

    class BGid(IntEnum):
        METAL_FACTORY = 1
        CRYSTAL_FACTORY = 2
        DEIT_FACTORY = 3
        SOLAR_STATION = 4
        FACTORY = 14
        NANITES = 15
        SHIPYARD = 21
        METAL_SILO = 22
        CRYSTAL_SILO = 23
        DEIT_SILO = 24
        LAB = 31
        ROCKET_SILO = 44

    logger = xn_logger.get('auto_builder', debug=True)

    world = XNovaWorld_instance()
    world.script_command = 'running'

    WORK_INTERVAL = 145  # seconds
    IMPERIUM_REFRESH_INTERVAL = 300  # seconds

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
        # error! incorrect gid supplied?
        tt = XNTechTree_instance()
        item = tt.find_item_by_gid(gid)
        s = 'Don\'t know how to calculate energy need for gid={0} "{1}" ({2})'.format(
            gid, item.name, item.category)
        logger.error(s)
        raise RuntimeError(s)

    def calc_planet_next_building(planet: XNPlanet) -> XNPlanetBuildingItem:
        if planet.is_moon or planet.is_base:
            return None
        met_level = 0
        cry_level = 0
        deit_level = 0
        ss_level = 0
        #
        met_bitem = planet.find_bitem_by_gid(int(BGid.METAL_FACTORY))
        if met_bitem is not None:
            met_level = met_bitem.level
        cry_bitem = planet.find_bitem_by_gid(int(BGid.CRYSTAL_FACTORY))
        if cry_bitem is not None:
            cry_level = cry_bitem.level
        deit_bitem = planet.find_bitem_by_gid(int(BGid.DEIT_FACTORY))
        if deit_bitem is not None:
            deit_level = deit_bitem.level
        ss_bitem = planet.find_bitem_by_gid(int(BGid.SOLAR_STATION))
        if ss_bitem is not None:
            ss_level = ss_bitem.level
        free_energy = planet.energy.energy_left
        #
        # first, check energy
        if free_energy <= 1:
            logger.info('Planet [{0}] has too low energy ({1}), must '
                        'build solar station!'.format(planet.name, free_energy))
            return ss_bitem
        # second, check robotics factory, if it is below level 10
        factory_level = 0
        factory_bitem = planet.find_bitem_by_gid(int(BGid.FACTORY))
        if factory_bitem is not None:
            factory_level = factory_bitem.level
            if factory_bitem.level < 10:
                # check resources, this will build factory before any
                # any other building only if enough resources NOW, do not wait
                if (planet.res_current.met >= factory_bitem.cost_met) and \
                        (planet.res_current.cry >= factory_bitem.cost_cry) and \
                        (planet.res_current.deit >= factory_bitem.cost_deit):
                    logger.info('Planet [{0}] Factory level < 10 and have res for it,'
                                ' build Factory!'.format(planet.name))
                    return factory_bitem
        # maybe build shipyard? :)
        shipyard_bitem = planet.find_bitem_by_gid(int(BGid.SHIPYARD))
        if shipyard_bitem is not None:
            if shipyard_bitem.level < factory_level:
                if (planet.res_current.met >= shipyard_bitem.cost_met) and \
                        (planet.res_current.cry >= shipyard_bitem.cost_cry) and \
                        (planet.res_current.deit >= shipyard_bitem.cost_deit):
                    logger.info('Planet [{0}] Shipyard level < {1} and have res for it,'
                                ' build Factory!'.format(planet.name, factory_level))
                    return shipyard_bitem
        # maybe build nanites factory? :)
        if factory_level >= 10:
            nanites_bitem = planet.find_bitem_by_gid(int(BGid.NANITES))
            if nanites_bitem is not None:
                if (planet.res_current.met >= nanites_bitem.cost_met) and \
                        (planet.res_current.cry >= nanites_bitem.cost_cry) and \
                        (planet.res_current.deit >= nanites_bitem.cost_deit):
                    logger.info('Planet [{0}] can build NANITES!'.format(planet.name))
                    return nanites_bitem
        # maybe build rocket silo?
        rs_bitem = planet.find_bitem_by_gid(int(BGid.ROCKET_SILO))
        if rs_bitem is not None:
            if rs_bitem.level < 2:
                if (planet.res_current.met >= rs_bitem.cost_met) and \
                        (planet.res_current.cry >= rs_bitem.cost_cry) and \
                        (planet.res_current.deit >= rs_bitem.cost_deit):
                    logger.info('Planet [{0}] can build rocket silo lv {1}'.format(
                        planet.name, rs_bitem.level+1))
                    return rs_bitem
        #
        # other resources buildings
        logger.info('Planet [{0}] m/c/d/e levels: {1}/{2}/{3}/{4} free_en: {5}'.format(
            planet.name, met_level, cry_level, deit_level, ss_level, free_energy))
        if ss_level < met_level:
            return ss_bitem
        #
        # calc energy needs
        met_eneed = energy_need_for_gid(int(BGid.METAL_FACTORY), met_level+1) \
            - energy_need_for_gid(int(BGid.METAL_FACTORY), met_level)
        cry_eneed = energy_need_for_gid(int(BGid.CRYSTAL_FACTORY), cry_level+1) \
            - energy_need_for_gid(int(BGid.CRYSTAL_FACTORY), cry_level)
        deit_eneed = energy_need_for_gid(int(BGid.DEIT_FACTORY), deit_level+1) \
            - energy_need_for_gid(int(BGid.DEIT_FACTORY), deit_level)
        logger.info('Planet [{0}] needed en: {1}/{2}/{3}'.format(
                planet.name, met_eneed, cry_eneed, deit_eneed))
        # try to fit in energy some buildings
        if (met_level < ss_level) and (met_eneed <= free_energy):
            return met_bitem
        if (cry_level < (ss_level-2)) and (cry_eneed <= free_energy):
            return cry_bitem
        if (deit_level < (ss_level-4)) and (deit_eneed <= free_energy):
            return deit_bitem
        #
        # check resources storage capacity
        if planet.res_max_silos.met > 0:
            if planet.res_current.met / planet.res_max_silos.met >= 0.7:
                silo_bitem = planet.find_bitem_by_gid(int(BGid.METAL_SILO))
                logger.info('Planet [{0}] needs metal silo!'.format(planet.name))
                return silo_bitem
        if planet.res_max_silos.cry > 0:
            if planet.res_current.cry / planet.res_max_silos.cry >= 0.7:
                silo_bitem = planet.find_bitem_by_gid(int(BGid.CRYSTAL_SILO))
                logger.info('Planet [{0}] needs crystal silo!'.format(planet.name))
                return silo_bitem
        if planet.res_max_silos.deit > 0:
            if planet.res_current.deit / planet.res_max_silos.deit >= 0.7:
                silo_bitem = planet.find_bitem_by_gid(int(BGid.DEIT_SILO))
                logger.info('Planet [{0}] needs deit silo!'.format(planet.name))
                return silo_bitem
        #
        # default - build solar station
        logger.warn('Planet [{0}] for some reason cannot decide what to build, '
                    'will build solar station by default'.format(planet.name))
        return ss_bitem

    def check_planet_buildings(world: XNovaWorld, planet: XNPlanet):
        # is there any building in progress on planet now?
        build_in_progress = False
        bitem = XNPlanetBuildingItem()
        for bitem_ in planet.buildings_items:
            if bitem_.is_in_progress():
                build_in_progress = True
                bitem = bitem_
                break
        if build_in_progress:
            logger.info('Planet [{0}] has still build in progress {1} lv {2}'.format(
                    planet.name, bitem.name, bitem.level+1))
            return
        # no builds in progress, we can continue

        bitem = calc_planet_next_building(planet)
        if bitem is None:
            logger.error('Planet [{0}]: for some reason could not calculate '
                         'next building, some internal error? Try to relogin and '
                         'refresh all world.'.format(planet.name))
            return

        logger.info('Planet [{0}] Next building will be: {1} lv {2}'.format(
                planet.name, bitem.name, bitem.level+1))
        logger.info('Planet [{0}] Its price: {1}m {2}c {3}d'.format(
                planet.name, bitem.cost_met, bitem.cost_cry, bitem.cost_deit))
        logger.info('Planet [{0}] We have: {1}m {2}c {3}d'.format(
                planet.name, int(planet.res_current.met), int(planet.res_current.cry),
                int(planet.res_current.deit)))
        # do we have enough resources to build it?
        if (planet.res_current.met >= bitem.cost_met) and \
                (planet.res_current.cry >= bitem.cost_cry) and \
                (planet.res_current.deit >= bitem.cost_deit):
            logger.info('Planet [{0}] We have enough resources to build it, trigger!'.format(
                    planet.name))
            world.signal(world.SIGNAL_BUILD_ITEM,
                         planet_id=planet.planet_id,
                         bitem=bitem,
                         quantity=0)
            logger.info('Planet [{0}] Signal to build this item has been sent to world thread, wait 10s...'.format(
                planet.name))
            time.sleep(10)  # actually wait
        else:
            logger.warn('Planet [{0}] We DO NOT have enough resources to build [{1} lv {2}]...'.format(
                    planet.name, bitem.name, bitem.level+1))

    last_work_time = time.time() - WORK_INTERVAL
    last_imperium_refresh_time = time.time()

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
                time.sleep(1)
                if world.script_command == 'stop':
                    break
        # if we didn't sleep long enough for a work_interval

        # refresh imperium from time to time
        if cur_time - last_imperium_refresh_time >= IMPERIUM_REFRESH_INTERVAL:
            logger.info('Time to refresh imperium...')
            last_imperium_refresh_time = cur_time
            world.signal(world.SIGNAL_RELOAD_PAGE, page_name='imperium')
    # while True

    del world.script_command

    logger.info('Stopped.')


# start script as a parallel thread
thr = Thread(target=auto_builder_thread, name='auto_builder_thread')
thr.daemon = False
thr.start()
