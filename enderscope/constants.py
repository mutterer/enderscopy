"""Shared G-code and stage-model constants."""

G_CODES = {
    'absolute': 'G90',
    'relative': 'G91',
    'homing': 'G28',
    'finish': 'M400',
    'set_speed_limit': 'M203',
    'current_position': 'M114'
}

DIRECTION_PREFIXES = {
    "north": "Y",
    "south": "Y-",
    "east": "X",
    "west": "X-",
    "up": "Z",
    "down": "Z-"
}

# declare different models here.
ENDER3V3SE = {
    "x_safe_offset": 85.0,
    "y_safe_offset": 100.0,
    "x_home_offset": -49.25,
    "y_home_offset": -25.0
}
