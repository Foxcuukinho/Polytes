import random
from Utils.utils import DELTA_TIME, SCORE_MARGIN, STICKMAN_DEFAULT_DECIDE_COOLDOWN
from Utils.screen import get_screen_geometry

class StickmanBrain:

    def update(self, stickman):
        stickman.decide_cooldown -= DELTA_TIME

        if stickman.decide_cooldown <= 0:
            self.decide(stickman)
            stickman.decide_cooldown = STICKMAN_DEFAULT_DECIDE_COOLDOWN

        if stickman.state == 'WALK' and self.reached_target(stickman):
            stickman.target_x = self.choose_target_x(stickman)

    def decide(self, stickman):
        previous_state = stickman.state

        score_idle = self.score_idle(stickman)
        score_walk = self.score_walk(stickman)

        if score_walk > score_idle + SCORE_MARGIN and not stickman.dragging:
            stickman.state = 'WALK'
            stickman.target_x = self.choose_target_x(stickman)

        elif score_idle > score_walk:
            stickman.state = 'IDLE'
            stickman.target_x = None

        if stickman.state != previous_state:
            stickman.animation_frame_index = 0

    def score_idle(self, stickman): 
        return self._calculate_score(stickman, invert=True)

    def score_walk(self, stickman):
        return self._calculate_score(stickman, invert=False)

    def _calculate_score(self,stickman, invert):

        utility_factors = [stickman.energy, stickman.curiosity, stickman.stamina, stickman.boredom]

        utility = 0

        for factor in utility_factors:
            if invert:
                utility += 1 - (factor  / 100)
            else:
                utility += factor / 100

        return utility

    def choose_target_x(self, stickman):
        _, _, screen_width, _, = get_screen_geometry()
                
        min_x = stickman.width
        max_x = screen_width - stickman.width
        min_distance = 200

        while True:
            target = random.randint(min_x, max_x)
            if abs(stickman.x - target) >= min_distance:
                break

        
        return target

    def reached_target(self,stickman):
        if abs(stickman.x - stickman.target_x) < 10:
            return True
        else:
            return False