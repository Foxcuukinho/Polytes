import random
from Utils.helpers import seed_from_name, clamp

def generate_base_traits(seed):
    rng = random.Random(seed)
    energy = rng.randint(0, 100)
    curiosity = rng.randint(0, 100)
    return energy, curiosity

# TODO: Na V2, tranformars os valores de buff em constantes
def apply_hollow_head_buff(energy, hollow_head):
    if hollow_head:
        return energy * 1.2
    else:
        return energy

def apply_color_buff(energy, curiosity, color):
    hue, _, _, _ = color.getHsv()

    if hue >= 120 and hue <= 240:
        curiosity = curiosity * 1.2

    else:
        energy = energy * 1.2

    return energy, curiosity

def generate_personality(name, hollow_head, color):
    seed = seed_from_name(name)

    energy, curiosity = generate_base_traits(seed)
    energy = apply_hollow_head_buff(energy, hollow_head)
    energy, curiosity = apply_color_buff(energy, curiosity, color)
    energy =  clamp(energy, 1, 100)
    curiosity = clamp(curiosity, 1, 100)

    return round(energy), round(curiosity)