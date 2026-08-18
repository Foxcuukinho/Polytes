from Utils.constants import DELTA_TIME
from Utils.helpers import clamp

class StickmanNeeds:
    def update(self, stickman):

        stamina_drain_per_frame = (65 / stickman.energy) * DELTA_TIME
        stamina_gain_per_frame = (stickman.energy / 50) * DELTA_TIME

        
        boredom_drain_per_frame = (stickman.curiosity / 50) * DELTA_TIME
        boredom_gain_per_frame = (stickman.curiosity / 30) * DELTA_TIME


        if stickman.state == 'IDLE':
            stickman.stamina += stamina_gain_per_frame
            stickman.boredom += boredom_gain_per_frame
        else:
            stickman.stamina -= stamina_drain_per_frame
            stickman.boredom -= boredom_drain_per_frame

        stickman.stamina = clamp(stickman.stamina, 0, 100)
        stickman.boredom = clamp(stickman.boredom, 0, 100)