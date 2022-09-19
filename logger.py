class Logger:
    def __init__(self, silent):
        self.silent = silent

    @staticmethod
    def paint(color, text, bold=1):
        return f"\033[{0+bold};{color+30};40m\033[49m{text}\033[0m"

    def info(self, text, func=print, func_args={}):
        return func(f"[{self.paint(2, '*')}] {text}", **func_args)

    def warning(self, text, func=print, func_args={}):
        return func(f"[{self.paint(3, '!')}] {text}", **func_args)

    def error(self, text, func=print, func_args={}):
        return func(
            f"[{self.paint(1, 'x')}] {self.paint(1, 'error')}: {text}", **func_args
        )
