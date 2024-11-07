import inspect

HEADER = '\033[95m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
END = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'


def color_print(text: str, color: str):
    print("[" + inspect.stack()[2].function.lower() + "]: " + color + text + END)

def print_info(text):
    color_print(text, CYAN)

def print_ok(text):
    color_print(text, GREEN)

def print_error(text):
    color_print(text, RED)

def print_warning(text):
    color_print(text, YELLOW)

def print_important(text):
    color_print(text, BLUE)