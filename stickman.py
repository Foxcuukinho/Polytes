from Utils.utils import STICKMAN_WIDTH, STICKMAN_HEIGHT, STICKMAN_DEFAULT_DECIDE_COOLDOWN, DEFAULT_ANIMATION_CYCLE_DURATION
from Brain.stickman_personality import generate_personality
from Animation.animations import ANIMATIONS

class Stickman:

    def __init__(self, name, color, hollow_head):

        # Configurações Principais
        self.name = name
        self.color = color
        self.hollow_head = hollow_head

        # Configurações de janela
        self.width = STICKMAN_WIDTH
        self.height = STICKMAN_HEIGHT

        # Física
        self.x = 0
        self.y = 0
        self.velocity_y = 0
        self.velocity_x = 0
        self.dragging = False
    
        # Cerébro
        self.state = 'IDLE'

        # TODO: Na V2, tirar esse inline
        self.energy, self.curiosity = generate_personality(name, hollow_head, color)

        # TODO: Pensei em colocar em utils.py tipo DEFAULT_NEEDS
        self.stamina = 100
        self.boredom = 45

        self.target_x = None
        self.direction = 1

        self.decide_cooldown = STICKMAN_DEFAULT_DECIDE_COOLDOWN

        # Animação
        self.animation_frame_index = 0
        self.animation_timer = 0
        self.current_frame = ANIMATIONS['IDLE']['frames'][0]
        self.base_frame = ANIMATIONS['IDLE']['frames'][0]
        self.animation_cycle_duration = DEFAULT_ANIMATION_CYCLE_DURATION

        print(f'Energy: {self.energy}')
        print(f'Curiosity: {self.curiosity}')