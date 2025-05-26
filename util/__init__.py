FONT_PATH_SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

def grow_rect(rect: tuple[float, float, float, float], grow: float) -> tuple[float, float, float, float]:
    """
    Grow a rectangle by a given amount.
    :param rect: The rectangle to grow.
    :param grow: The amount to grow the rectangle.
    :return: The grown rectangle.
    """
    return (rect[0] - grow, rect[1] - grow, rect[2] + grow, rect[3] + grow)