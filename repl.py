""" Simple REPL for testing Ziffers notation """
# pylint: disable=locally-disabled, redefined-builtin, broad-except

from rich import print
from ziffers import parse_expression
import readline

EXIT_CONDITION = ("exit", "quit", "")

if __name__ == "__main__":
    print("[purple]== ZIFFERS REPL ==[/purple]")
    while True:
        expr = input("> ")
        if expr not in EXIT_CONDITION:
            try:
                print(parse_expression(expr))
            except Exception as e:
                print(f"[red]Failed:[/red] {e}")
        else:
            exit()
