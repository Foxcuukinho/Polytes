def check_rect_overlap(
    first_x, first_y, first_width, first_height,
    second_x, second_y, second_width, second_height
):
    return not (
        first_x + first_width  <= second_x or
        second_x + second_width <= first_x or
        first_y + first_height <= second_y or
        second_y + second_height <= first_y
    )    