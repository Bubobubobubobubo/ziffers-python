from ziffers import *
from rich import print

EXIT_CONDITION = ('exit', 'quit', '')

if __name__ == "__main__":
    print(f"[purple]== ZIFFERS REPL ==[/purple]")
    while True:
        expr = input('> ')
        if expr not in EXIT_CONDITION:
            try:
                result = parse_expression(expr)
                print(result)
            except Exception as e:
                print(f"[red]Failed:[/red] {e}")
        else:
            exit()
