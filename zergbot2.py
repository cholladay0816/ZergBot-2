import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2 import position
from sc2.constants import *
from sc2.position import Point2, Point3
from sc2.data import Status, Result
import numpy as np
import cv2
import random
from typing import List, Dict, Set, Tuple, Any, Optional, Union
# class Human(sc2.BotAI):
    # def __init__(self):
        # self.data=None
    # async def on_step(self,increment):
        # self.increment = 0
class ZergBot2(sc2.BotAI):
    def __init__(self):
        print("Bot started...")
        self.pending_orders=[]
        self.fighting_units = []
        self.enemy_unit_snapshot = []
        self.remembered_enemy_units = []
        self.remembered_enemy_units_by_tag = {}
        self.attack_wave = []
        self.to_be_removed = []
        self.main = None
        self.lurker_range_started=False
        self.mboost_started=False
        self.adrenalglands_started=False
        self.neural_parasite_started = False
        self.scouter=None
        
    def getTimeInSeconds(self):
        # Credit to Burny's CreepyBot for the time in seconds function
        return self.state.game_loop * 0.725 * (1/16)
    async def on_step(self,increment):
        self.larvae = self.units(LARVA).ready.noqueue
        self.can_spawn_larvae = (len(self.larvae) > 0)
        self.hatches = self.townhalls
        self.ready_hatches = self.townhalls.ready
        self.hatch_count=len(self.hatches)
        self.ideal_gas = int((len(self.units(DRONE)))/11)-1
        if(self.main == None):
            self.main = self.hatches[0]
        self.pending_orders=[]
        await self.micro()
        await self.defend()
        #await self.regroup()
        await self.distribute_workers()
        #await self.spawn_army()
        self.remember_enemy_units()
        await self.scout()
        await self.calculate_combat_value()
        await self.spawn_drones()
        await self.spawn_overlord_two()
        await self.upgrade()
        await self.expo()
        await self.build_gas_two()
        await self.do_actions(self.pending_orders)
        self.pending_orders=[]
    async def spawn_army(self):
        #20 zerglings
        #20 roaches
        #20 hydras
        for l in self.units(LARVA).ready:
            if len(self.units(ZERGLING)) <20:
                await self.spawn_from_larvae(ZERGLING)
            if len(self.units(BANELING)) <15:
                await self.spawn_from_larvae(BANELING)
            if len(self.units(ROACH)) <20:
                await self.spawn_from_larvae(ROACH)
            if len(self.units(HYDRALISK)) <20:
                await self.spawn_from_larvae(HYDRALISK)
            if len(self.units(MUTALISK)) <10:
                await self.spawn_from_larvae(MUTALISK)
            if len(self.units(RAVAGER)) <5:
                await self.spawn_from_larvae(RAVAGER)
            if len(self.units(INFESTOR)) <2:
                await self.spawn_from_larvae(INFESTOR)
            if len(self.units(LURKERMP)) <4:
                await self.spawn_from_larvae(LURKERMP)
            if len(self.units(ULTRALISK)) <3:
                await self.spawn_from_larvae(ULTRALISK)
    def remember_enemy_units(self):
        # Every 60 seconds, clear all remembered units (to clear out killed units)
        #if round(self.get_game_time() % 60) == 0:
        #    self.remembered_enemy_units_by_tag = {}

        # Look through all currently seen units and add them to list of remembered units (override existing)
        for unit in self.known_enemy_units:
            unit.is_known_this_step = True
            self.remembered_enemy_units_by_tag[unit.tag] = unit

        # Convert to an sc2 Units object and place it in self.remembered_enemy_units
        self.remembered_enemy_units = sc2.units.Units([], self._game_data)
        for tag, unit in list(self.remembered_enemy_units_by_tag.items()):
            # Make unit.is_seen = unit.is_visible 
            if unit.is_known_this_step:
                unit.is_seen = unit.is_visible # There are known structures that are not visible
                unit.is_known_this_step = False # Set to false for next step
            else:
                unit.is_seen = False

            # Units that are not visible while we have friendly units nearby likely don't exist anymore, so delete them
            if not unit.is_seen and self.units.closer_than(7, unit).exists:
                del self.remembered_enemy_units_by_tag[tag]
                continue

            self.remembered_enemy_units.append(unit)
    async def calculate_combat_value(self):
        value=0
        soft=0
        hard=0
        air=0
        ground=0
        friendly_value=0
        friendly_soft=0
        friendly_hard=0
        friendly_air=0
        friendly_ground=0
        # for u in self.known_enemy_units.filter(lambda x:x.tag not in self.enemy_unit_snapshot):
            # if u.tag in self.enemy_unit_snapshot:
                # continue
            # else:
                # self.enemy_unit_snapshot.append(u)
        # for u in self.enemy_unit_snapshot:
            # if u.health<=0:
                # self.enemy_unit_snapshot.remove(u)
            
        for unit in self.units.not_structure.exclude_type(DRONE).exclude_type(OVERLORD).exclude_type(QUEEN).exclude_type(EGG).exclude_type(LARVA):
            friendly_air+=unit.air_dps
            friendly_ground+=unit.ground_dps
            if not (unit.is_structure):
                if(unit.is_biological):
                    friendly_soft+=unit.health
                if(unit.is_armored or unit.is_mechanical or unit.is_robotic or unit.is_massive):
                    friendly_hard+=unit.health
            friendly_value += friendly_hard + friendly_soft + friendly_air + friendly_ground
        
        for unit in self.remembered_enemy_units.not_structure.exclude_type(SCV):
            air+=unit.air_dps
            ground+=unit.ground_dps
            if not (unit.is_structure):
                if(unit.is_biological):
                    soft+=unit.health
                if(unit.is_armored or unit.is_mechanical or unit.is_robotic or unit.is_massive):
                    hard+=unit.health
            value += hard + soft + air + ground
            
        totaldps=air+ground
        if totaldps!=0:
            airpercent = air / totaldps
        else:
            return
        hptotal = hard+soft
        if hptotal!=0:
            softpercent = soft / hptotal
        else:
            return
        if (friendly_value - value) < 1500 or self.getTimeInSeconds() > 360:
            if airpercent < 0.21:
                #make mutas
                await self.spawn_from_larvae(MUTALISK)
                await self.spawn_from_larvae(HYDRALISK)
                await self.spawn_from_larvae(LURKERMP)
                await self.spawn_from_larvae(ROACH)
                await self.spawn_from_larvae(ZERGLING)
            #if <40% air damage
                #if mostly soft, mutalisks
                #if mostly hard, make mutalisks
            if airpercent >= 0.21:
                if softpercent > 0.6:
                    await self.spawn_from_larvae(ROACH) #20%
                    await self.spawn_from_larvae(ZERGLING) #to make banes
                    await self.spawn_from_larvae(BANELING) #60%
                    await self.spawn_from_larvae(HYDRALISK) #20%
                if softpercent <= 0.6:
                    await self.spawn_from_larvae(HYDRALISK) #70%
                    await self.spawn_from_larvae(INFESTOR) #15%
                    await self.spawn_from_larvae(LURKERMP) #15%
                    await self.spawn_from_larvae(ZERGLING)
                    await self.spawn_from_larvae(MUTALISK)
        #if >60% air damage, do NOT make mutas or corruptors
            #if mostly soft, make roaches and banes
            #if mostly hard, make lurkers and hydras
            
            
            
        print("Perceived unit advantage: " + str(friendly_value - value))
        #print("Air DPS: "+str(friendly_air-air)+"\n"+"Ground DPS: "+str(friendly_ground-ground)+"\n"+"Armor HP: "+str(friendly_hard-hard)+"\n"+"Bio HP: "+str(friendly_soft-soft)+"\n")
        
        # if((friendly_value >= value or len(self.units(DRONE))<22) and len(self.units(DRONE)) < 50):
            # await self.build_worker_two()
        # elif(friendly_value < value):
            # await self.build_army()
        if((friendly_value - value) >= 20000 and friendly_air > 10 and friendly_ground > 10):
            await self.basic_attack()
    async def scout(self):
        if(self.scouter!=None):
            found=False
            for u in self.units(self.scout_type):
                if(u.tag == self.scouter.tag):
                    found=True
                    break
            if not found:
                self.scouter=None
        if(self.supply_used<20):
            return
        if self.scouter==None:
            if (self.units(CHANGELING)):
                self.scouter=self.units(CHANGELING)[0]
                self.scout_type = CHANGELING
            elif (self.units(ZERGLING)):
                self.scouter=self.units(ZERGLING)[0]
                self.scout_type = ZERGLING
            elif (self.units(DRONE)):
                if self.units(DRONE).idle:
                    self.scouter=self.units(DRONE).idle[0]
                else:
                    self.scouter=self.units(DRONE)[0]
                    self.scout_type = DRONE
            elif (self.units(OVERSEER)):
                self.scouter=self.units(OVERSEER)[0]
                self.scout_type = OVERSEER
            elif (self.units(OVERLORD)):
                self.scouter=self.units(OVERLORD)[0]
                self.scout_type = OVERLORD
            elif (self.units(QUEEN)):
                self.scouter=self.units(QUEEN)[0]
                self.scout_type = QUEEN
        if(self.scouter==None):
            return
        # if(self.scouter.is_idle):
        self.pending_orders.append(self.scouter.move(self.random_location_variance(self.enemy_start_locations[0],5)))
    async def basic_attack(self):#.filter(lambda unit: unit.is_idle)
        for u in self.units.ready.not_structure.exclude_type(DRONE).exclude_type(OVERLORD).exclude_type(QUEEN).exclude_type(EGG).exclude_type(LARVA):
            # if self.known_enemy_units:
                # self.pending_orders.append(u.attack(self.known_enemy_units.closest_to(u)))
                # continue
            # if self.known_enemy_structures:
                # self.pending_orders.append(u.attack(self.known_enemy_structures.closest_to(u)))
                # continue
            # if self.remembered_enemy_units:
                # self.pending_orders.append(u.attack(self.remembered_enemy_units.closest_to(u)))
                # continue
            # if self.remembered_enemy_structures:
                # self.pending_orders.append(u.attack(self.remembered_enemy_structures.closest_to(u)))
                # continue
            self.pending_orders.append(u.attack(self.enemy_start_locations[0]))
                
    async def micro(self):
        #UNIT MICRO
        for u in self.units():
            if(u.type_id==SIEGETANK):
                #INFESTED SIEGETANK, SIEGE NOW
                abilities = await self.get_available_abilities(self.units(SIEGETANK)[0])
                if AbilityId.SIEGEMODE_SIEGEMODE not in abilities or not self.can_afford(AbilityId.SIEGEMODE_SIEGEMODE):
                    continue
                self.pending_orders.append(u(SIEGEMODE_SIEGEMODE))
            #ZERGLING (EARLYGAME, <20 FRIENDLY ZERGLINGS, SIEGETANKS)
            #TARGET SIEGE TANKS, THEN NEAREST UNITS

            #BANELING (MORE SOFT GROUND DAMAGE)
            #TARGET CLOSEST UNITS, BUT SORTED BY SOFTNESS VS HARDNESS TO ATTACK MARINES INSTEAD OF CYCLONES
            if(u.type_id==ROACH):
                #UNIT TARGET MICRO GOES HERE
                
                #MAKE SURE BURROW EXISTS
                if self.units(DRONE):
                    droneAbilities = await self.get_available_abilities(self.units(DRONE)[0])
                    if AbilityId.BURROWDOWN_DRONE not in droneAbilities:
                        continue
                else:
                    continue
                abilities = await self.get_available_abilities(self.units(ROACH)[0])
                if AbilityId.BURROWDOWN_ROACH not in abilities or not self.can_afford(AbilityId.BURROWDOWN_ROACH):
                    continue
                if (u.health / u.health_max) <= 4/10:
                    self.pending_orders.append(u(BURROWDOWN_ROACH))
                #ROACH (MORE GROUND DAMAGE)
                #TARGET SOFT UNITS, BURROW WHEN LOW ON HEALTH, RE-EMERGE WHEN FULL
            if(u.type_id==ROACHBURROWED):
                #UNBURROW ROACH
                abilities = await self.get_available_abilities(self.units(ROACHBURROWED)[0])
                if AbilityId.BURROWUP_ROACH not in abilities or not self.can_afford(AbilityId.BURROWUP_ROACH):
                    continue
                if (u.health / u.health_max) >= 8/10 and u.is_burrowed:
                    self.pending_orders.append(u(BURROWUP_ROACH))
            if(u.type_id==LURKERMP):
                #UNIT TARGET MICRO GOES HERE
                
                #MAKE SURE BURROW EXISTS
                if self.units(DRONE):
                    droneAbilities = await self.get_available_abilities(self.units(DRONE)[0])
                    if AbilityId.BURROWDOWN_DRONE not in droneAbilities:
                        continue
                else:
                    continue
                abilities = await self.get_available_abilities(self.units(LURKERMP)[0])
                if AbilityId.BURROWDOWN_LURKER  not in abilities or not self.can_afford(AbilityId.BURROWDOWN_LURKER):
                    continue
                if (self.known_enemy_units.not_flying.not_structure.closer_than(10, u.position)):
                    self.pending_orders.append(u(BURROWDOWN_LURKER))
                #ROACH (MORE GROUND DAMAGE)
                #TARGET SOFT UNITS, BURROW WHEN LOW ON HEALTH, RE-EMERGE WHEN FULL
            if(u.type_id==LURKERMPBURROWED):
                #UNBURROW ROACH
                abilities = await self.get_available_abilities(self.units(LURKERMPBURROWED)[0])
                if AbilityId.BURROWUP_LURKER not in abilities or not self.can_afford(AbilityId.BURROWUP_LURKER):
                    continue
                if (not self.known_enemy_units.not_flying.not_structure.closer_than(10, u.position) and u.is_burrowed):
                    self.pending_orders.append(u(BURROWUP_LURKER))
            if(u.type_id==RAVAGER):
                #RAVAGER SHOT
                #GET ALL UNITS IN A 9 UNIT RADIUS
                #FIRE AT TARGETS BASED ON PRIORITY
                abilities = await self.get_available_abilities(self.units(RAVAGER)[0])
                if AbilityId.EFFECT_CORROSIVEBILE not in abilities or not self.can_afford(AbilityId.EFFECT_CORROSIVEBILE):
                    continue
                targets = [LIBERATOR, SIEGETANKSIEGED, THOR, LURKERMP, LURKERMPBURROWED]
                targets_alt = [MARAUDER, RAVAGER]
                shoot_targs = self.known_enemy_units.not_structure.filter(lambda x:x.type_id in targets).closer_than(10, u.position)
                if len(shoot_targs)<=0:
                    shoot_targs = self.known_enemy_units.not_structure.filter(lambda x:x.type_id in targets_alt).closer_than(10, u.position)
                if len(shoot_targs)>0:
                    for t in shoot_targs:
                        self.pending_orders.append(u(EFFECT_CORROSIVEBILE, t.position))
            #HYDRALISK (MORE GROUND AND AIR DAMAGE)
            #TARGET AIR UNITS, THEN GROUND UNITS.  RUN FROM SLOW MELEE UNITS LIKE BANELINGS.

            #MUTALISK (SLIGHT ANTI-AIR DAMAGE)
            #TARGET AIR-ATTACKING UNITS, THEN GROUND ONLY UNITS.

            #CORRUPTOR (MORE AIR DAMAGE)
            #TARGET AIR UNITS, AVOID GROUND UNITS.

            #INFESTOR (MORE THAN TWO MAJOR UNITS)
            if(u.type_id==INFESTOR):
                #RAVAGER SHOT
                #GET ALL UNITS IN A 9 UNIT RADIUS
                #FIRE AT TARGETS BASED ON PRIORITY
                abilities = await self.get_available_abilities(self.units(INFESTOR)[0])
                if AbilityId.NEURALPARASITE_NEURALPARASITE  not in abilities or not self.can_afford(AbilityId.NEURALPARASITE_NEURALPARASITE ):
                    continue
                targets = [LIBERATOR, SIEGETANKSIEGED, SIEGETANK, THOR, LURKERMP, LURKERMPBURROWED, ULTRALISK, GHOST]
                targets_alt = [BANSHEE, RAVAGER, GOLIATH, MEDIVAC]
                shoot_targs = self.known_enemy_units.not_structure.filter(lambda x:x.type_id in targets).closer_than(10, u.position)
                if len(shoot_targs)<=0:
                    shoot_targs = self.known_enemy_units.not_structure.filter(lambda x:x.type_id in targets_alt).closer_than(10, u.position)
                if len(shoot_targs)>0:
                    for t in shoot_targs:
                        self.pending_orders.append(u(NEURALPARASITE_NEURALPARASITE, t))
            #IF NOT ACTIVELY SNATCHING A SIEGE TANK, THOR, ULTRALISK, RAVAGER, COLLOSSUS, OR MOTHERSHIP, STAY NEAR COMBAT ZONE BUT SAFELY OUT OF RANGE

            #ULTRALISK (MANY MARINES OR ZEALOTS)
            #ATTACK LARGE CLUMPS OF UNITS, (WITH BACKUP RANGE UNITS IDEALLY)
    def get_unit_center(self):
        self.fighting_units = self.units.not_structure.exclude_type(DRONE).exclude_type(OVERLORD).exclude_type(QUEEN).exclude_type(EGG).exclude_type(LARVA)
        self.attack_wave = (self.fighting_units)
        res = Point2((0, 0))
        if len(self.fighting_units) > 0:
            sum_x = 0
            sum_y = 0
            for i in self.fighting_units:
                sum_x += i.position.x
                sum_y += i.position.y
            target_pos_x = sum_x / len(self.fighting_units)
            
            target_pos_y = sum_y / len(self.fighting_units)
            print(str(target_pos_x)+','+str(target_pos_y))
            res = Point2((target_pos_x, target_pos_y))
        return res
    async def regroup(self):
        units = self.units.not_structure.exclude_type(DRONE).exclude_type(OVERLORD).exclude_type(QUEEN).exclude_type(EGG).exclude_type(LARVA)
        out_of_position=0
        for unit in units:
            # if len(unit.orders) == 1 and unit.orders[0].ability.id in [AbilityId.ATTACK]:
                # continue
            
            if unit.distance_to(self.get_unit_center()) > 10 and unit.type_id != ZERGLING:
                out_of_position+=1
            if out_of_position/len(units) >= 0.5:
                for u in units:
                    if u.is_idle:
                        continue
                    if u.distance_to(self.enemy_start_locations[0]) > 40:
                        self.pending_orders.append(u.move(self.get_unit_center()))
    async def defend(self):
        self.fighting_units = self.units.not_structure.exclude_type(DRONE).exclude_type(OVERLORD).exclude_type(QUEEN).exclude_type(EGG).exclude_type(LARVA)
        for u in self.fighting_units:
            if u in self.attack_wave:
                self.fighting_units.remove(u)
        enemies = self.known_enemy_units.closer_than(60, self.start_location)
        
        if not enemies or not self.fighting_units:
            return
        for u in self.fighting_units.idle:
            self.pending_orders.append(u.attack(random.choice(enemies)))
    async def spawn_drones(self):
        if(len(self.units(DRONE))>=80):
            return
        for l in self.units(LARVA).ready:
            if(self.supply_left <= 2*self.hatch_count and not self.already_pending(OVERLORD)):
                return
            if(self.minerals < 50):
                return
            if(self.hatch_count * 19 < len(self.units(DRONE))):
                return
            if not self.can_afford(DRONE):
                return
            
            if(len(self.units(DRONE))>=18 and self.minerals < 150):
                return
            await self.spawn_from_larvae(DRONE)
    async def expo(self):
        #22 to 1
        if(self.hatch_count>=5):
            return
        if(self.hatch_count*22<len(self.units(DRONE))):
            return
        if(self.already_pending(HATCHERY)):
            return
        await self.expand_now_fixed()
    async def build_gas_two(self):
        if self.already_pending(EXTRACTOR):
            return
        if len(self.units(DRONE))-3 < (11*(len(self.units(EXTRACTOR))+1)):
            return
        for hatch in self.ready_hatches:
            vespenes = self.state.vespene_geyser.closer_than(15.0, hatch)
            for vespene in vespenes:
                if not self.can_afford(EXTRACTOR):
                    break
                worker = self.select_build_worker(vespene.position)
                if worker is None:
                    break
                if not self.units(EXTRACTOR).closer_than(1.0, vespene).exists:
                    self.pending_orders.append(worker.build(EXTRACTOR, vespene))
                    return
    async def expand_now_fixed(self, building: UnitTypeId=None, max_distance: Union[int, float]=10, location: Optional[Point2]=None):
        """Takes new expansion."""

        if not building:
            # self.race is never Race.Random
            building = HATCHERY

        assert isinstance(building, UnitTypeId)

        if not location:
            location = await self.get_next_expansion()
        if(self.can_afford(HATCHERY)):
            await self.build(building, near=location, max_distance=max_distance, random_alternative=False, placement_step=1)
    async def spawn_from_larvae(self, type):
        if not self.can_spawn_larvae:
            return
        zerglings = self.units(ZERGLING).idle
        hydras = self.units(HYDRALISK).idle
        roaches = self.units(ROACH).idle
        if type == BANELING and zerglings:
            r=zerglings.idle.random
        elif type == LURKERMP and hydras:
            r=hydras.idle.random
        elif type == RAVAGER and roaches:
            r=roaches.idle.random
        else:
            r = self.larvae.random
        if not r:
            return
        if self.can_afford(type):
            self.pending_orders.append(r.train(type))
            print("Hatching "+str(type))
            return
    async def spawn_overlord_two(self):
        #print(self.hatch_count)
        if self.supply_left - (self.hatch_count*3) <= 0 and not self.already_pending(OVERLORD):
            if self.can_afford(OVERLORD):
                await self.spawn_from_larvae(OVERLORD)
    async def upgrade(self):
        if(len(self.units(DRONE))<14):
            return
        #NEURAL PARASITE
        if self.vespene >= 150:
            ip = self.units(INFESTATIONPIT).ready
            if ip.exists and self.minerals >= 150:# and not self.neural_parasite_started:
                self.pending_orders.append(ip.first(AbilityId.RESEARCH_NEURALPARASITE))
                self.neural_parasite_started = True
        #BUILD POOL
        if not self.units(SPAWNINGPOOL) and self.can_afford(SPAWNINGPOOL) and not self.already_pending(SPAWNINGPOOL) and ((len(self.units(DRONE)) >= 17)):
            await self.build(SPAWNINGPOOL, near=self.hatches[0].position.towards(self.enemy_start_locations[0], 4))
        #SPEEDLINGS
        if self.vespene >= 100:
            sp = self.units(SPAWNINGPOOL).ready
            if sp.exists and self.minerals >= 100 and not self.mboost_started:
                self.pending_orders.append(sp.first(RESEARCH_ZERGLINGMETABOLICBOOST))
                self.mboost_started = True
        #LURKER RANGE
        if self.vespene >= 150:
            sp = self.units(LURKERDENMP).ready
            if sp.exists and self.minerals >= 150 and not self.lurker_range_started:
                self.pending_orders.append(sp.first(RESEARCH_ADAPTIVETALONS))
                self.lurker_range_started = True
        
        #ZERG_DMG
        if self.vespene >= 200 and self.units(HIVE).ready:
            sp = self.units(SPAWNINGPOOL).ready
            if sp.exists and self.minerals >= 200 and not self.adrenalglands_started:
                self.pending_orders.append(sp.first(RESEARCH_ZERGLINGADRENALGLANDS))
                self.adrenalglands_started = True
        #BUILD LAIR
        if self.hatch_count > 0 and not self.units(LAIR)and not self.units(HIVE) and (len(self.units(DRONE)) > 16):
            if(self.main.noqueue and self.can_afford(LAIR) and not self.already_pending(LAIR) and len(self.units(SPAWNINGPOOL))>0):
                self.pending_orders.append(self.main.build(LAIR))
        #BUILD EVO
        if not self.units(EVOLUTIONCHAMBER) and self.can_afford(EVOLUTIONCHAMBER) and not self.already_pending(EVOLUTIONCHAMBER) and (len(self.units(DRONE)) > 17):
            await self.build(EVOLUTIONCHAMBER, near=self.hatches[0].position.towards(self.enemy_start_locations[0], 3))
        #BUILD ROACHES
        if not self.units(ROACHWARREN) and self.can_afford(ROACHWARREN) and not self.already_pending(ROACHWARREN) and ((len(self.units(DRONE)) > 18)):
            await self.build(ROACHWARREN, near=self.main.position.towards(self.enemy_start_locations[0], 4))
        #BUILD LURKERS
        if not (self.units(LURKERDEN)|self.units(LURKERDENMP)) and (self.units(LAIR)|self.units(HIVE)) and self.units(HYDRALISKDEN) and self.can_afford(LURKERDENMP) and not self.already_pending(LURKERDENMP) and ((len(self.units(DRONE)) > 19)):
            await self.build(LURKERDENMP, near=self.main.position.towards(self.enemy_start_locations[0], 4))
        #BURROW
        if self.units(DRONE):
            droneAbilities = await self.get_available_abilities(self.units(DRONE)[0])
            if AbilityId.BURROWDOWN_DRONE not in droneAbilities:
                if ((self.units(LAIR) | self.units(HIVE)) and self.units(HATCHERY) and self.can_afford(AbilityId.RESEARCH_BURROW)):
                    targets = self.units(HATCHERY).ready.idle+self.units(LAIR).ready.idle+self.units(HIVE).ready.idle
                    if targets:
                        target=random.choice(targets)
                        self.pending_orders.append(self.main(AbilityId.RESEARCH_BURROW))
        #ROACH BURROW
        if self.units(ROACHWARREN):
            warren = self.units(ROACHWARREN).random
            abilities = await self.get_available_abilities(warren)
            if(AbilityId.RESEARCH_TUNNELINGCLAWS in abilities and self.can_afford(AbilityId.RESEARCH_TUNNELINGCLAWS)):
                self.pending_orders.append(warren(AbilityId.RESEARCH_TUNNELINGCLAWS))
        #BUILD HYDRAS
        if not self.units(HYDRALISKDEN) and self.can_afford(HYDRALISKDEN) and not self.already_pending(HYDRALISKDEN) and ((len(self.units(DRONE)) > 20)):
            await self.build(HYDRALISKDEN, near=self.hatches[0].position.towards(self.enemy_start_locations[0], 5))
        #UPGRADE GROUND UNITS
        if self.units(EVOLUTIONCHAMBER) and self.minerals > 200 and self.vespene > 150:
            evo = random.choice(self.units(EVOLUTIONCHAMBER))
            upgrades = [AbilityId.RESEARCH_ZERGMISSILEWEAPONSLEVEL1, AbilityId.RESEARCH_ZERGMISSILEWEAPONSLEVEL2, AbilityId.RESEARCH_ZERGMISSILEWEAPONSLEVEL3, AbilityId.RESEARCH_ZERGGROUNDARMORLEVEL1, AbilityId.RESEARCH_ZERGGROUNDARMORLEVEL2, AbilityId.RESEARCH_ZERGGROUNDARMORLEVEL3]
            upgrades.extend([AbilityId.RESEARCH_ZERGMELEEWEAPONSLEVEL1,
            AbilityId.RESEARCH_ZERGMELEEWEAPONSLEVEL2,
            AbilityId.RESEARCH_ZERGMELEEWEAPONSLEVEL3])
            abilities = await self.get_available_abilities(evo)
            for upgrade in upgrades:
                if upgrade in abilities and self.can_afford(upgrade):
                    error = self.pending_orders.append(evo(upgrade))
        #BUILD SPIRE
        if not self.units(SPIRE) and self.can_afford(SPIRE) and not self.already_pending(SPIRE) and not self.units(GREATERSPIRE) and ((len(self.units(DRONE)) > 22)):
            await self.build(SPIRE, near=self.hatches[0].position.towards(self.enemy_start_locations[0], 6))
        #BUILD BANELING
        if not self.units(BANELINGNEST) and self.can_afford(BANELINGNEST) and not self.already_pending(BANELINGNEST) and ((len(self.units(DRONE)) > 20)):
            await self.build(BANELINGNEST, near=self.hatches[0].position.towards(self.enemy_start_locations[0], 4))
        #BUILD INFESTATIONPIT
        if not self.units(INFESTATIONPIT) and self.can_afford(INFESTATIONPIT) and not self.already_pending(INFESTATIONPIT) and (len(self.units(DRONE)) > 23):
            await self.build(INFESTATIONPIT, near=self.hatches[0].position.towards(self.enemy_start_locations[0], 4))
        #BUILD HIVE
        if self.hatch_count > 0 and not self.units(HIVE) and (len(self.units(DRONE)) > 32):
            if(self.main.noqueue and self.can_afford(HIVE) and not self.already_pending(HIVE) and len(self.units(INFESTATIONPIT))>0):
                self.pending_orders.append(self.main.build(HIVE))
        #BUILD GREATERSPIRE
        if not self.units(GREATERSPIRE) and self.units(HIVE) and self.units(SPIRE) and (len(self.units(DRONE)) > 26):
            if(self.main.noqueue and self.can_afford(GREATERSPIRE) and not self.already_pending(GREATERSPIRE)):
                self.pending_orders.append(self.units(SPIRE)[0].build(GREATERSPIRE))
        #BUILD ULTRALISKCAVERN
        if not self.units(ULTRALISKCAVERN) and self.can_afford(ULTRALISKCAVERN) and not self.already_pending(ULTRALISKCAVERN) and ((len(self.units(DRONE)) > 28)):
            await self.build(ULTRALISKCAVERN, near=self.hatches[0].position.towards(self.enemy_start_locations[0], 5))
            
            # ZERGMELEEWEAPONSLEVEL1 = 53
            # ZERGMELEEWEAPONSLEVEL2 = 54
            # ZERGMELEEWEAPONSLEVEL3 = 55
            # ZERGGROUNDARMORSLEVEL1 = 56
            # ZERGGROUNDARMORSLEVEL2 = 57
            # ZERGGROUNDARMORSLEVEL3 = 58
            # ZERGMISSILEWEAPONSLEVEL1 = 59
            # ZERGMISSILEWEAPONSLEVEL2 = 60
            # ZERGMISSILEWEAPONSLEVEL3 = 61
            # OVERLORDSPEED = 62
            # OVERLORDTRANSPORT = 63
            # BURROW = 64
            # ZERGLINGATTACKSPEED = 65
            # ZERGLINGMOVEMENTSPEED = 66
            # HYDRALISKSPEED = 67
            # ZERGFLYERWEAPONSLEVEL1 = 68
            # ZERGFLYERWEAPONSLEVEL2 = 69
            # ZERGFLYERWEAPONSLEVEL3 = 70
            # ZERGFLYERARMORSLEVEL1 = 71
            # ZERGFLYERARMORSLEVEL2 = 72
            # ZERGFLYERARMORSLEVEL3 = 73
            # INFESTORENERGYUPGRADE = 74

    def random_location_variance(self, location, amount):
        x = location[0]
        y = location[1]

        #  FIXED THIS
        x += random.randrange(-amount,amount)
        y += random.randrange(-amount,amount)

        if x < 0:
            print("x below")
            x = 0
        if y < 0:
            print("y below")
            y = 0
        if x > self.game_info.map_size[0]:
            print("x above")
            x = self.game_info.map_size[0]
        if y > self.game_info.map_size[1]:
            print("y above")
            y = self.game_info.map_size[1]

        go_to = position.Point2(position.Pointlike((x,y)))

        return go_to
        
run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Zerg, ZergBot2()),
    Computer(Race.Terran, Difficulty.Hard)
    ], realtime=False)

