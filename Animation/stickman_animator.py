from Utils.constants import DELTA_TIME, DISTANCE_PER_WALK_CYCLE
from Animation.animations import ANIMATIONS

class StickmanAnimator:
    def update(self, stickman):

        current_animation = ANIMATIONS[stickman.state]
        current_frames = current_animation['frames']

        self.calculate_cycle_duration(stickman, current_animation)

        seconds_per_frame = stickman.animation_cycle_duration / len(current_frames)
        
        stickman.current_frame = self.interpolate_frame(stickman, current_frames, seconds_per_frame)

        stickman.animation_timer += DELTA_TIME

        if stickman.animation_timer >= seconds_per_frame:
            stickman.animation_timer = 0
            stickman.animation_frame_index = (stickman.animation_frame_index + 1) % len(current_frames)
            stickman.base_frame = current_frames[stickman.animation_frame_index]

    def calculate_cycle_duration(self, stickman, current_animation):
        if stickman.state == 'WALK' and not (stickman.holding or stickman.flying):
            stickman.animation_cycle_duration =  DISTANCE_PER_WALK_CYCLE / stickman.velocity_x
        else:
            stickman.animation_cycle_duration = current_animation["default_seconds_per_cycle"]

    def interpolate_frame(self, stickman, current_frames, seconds_per_frame):

        progress = stickman.animation_timer / seconds_per_frame

        next_frame = current_frames[(stickman.animation_frame_index + 1) % len(current_frames)]

        interpolated_frame = {}

        for angle in stickman.base_frame:
            interpolated_angle = stickman.base_frame[angle] + (next_frame[angle] - stickman.base_frame[angle]) * progress
            interpolated_frame[angle] = interpolated_angle

        return interpolated_frame