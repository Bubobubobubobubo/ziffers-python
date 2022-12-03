from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from .ebnf import ebnf

__all__ = ('ZiffersVisitor', 'parse_expression',)

GRAMMAR = Grammar(ebnf)

class ZiffersVisitor(NodeVisitor):
    def visit_expr(self, node, visited_children):
        """ Returns the overall output. """
        output = {}
        for child in visited_children:
            output.update(child[0])
        return output

    def visit_entry(self, node, visited_children):
        """ Makes a dict of the section (as key) and the key/value pairs. """
        key, values = visited_children
        return {key: dict(values)}

    def visit_section(self, node, visited_children):
        """ Gets the section name. """
        _, section, *_ = visited_children
        return section.text

    def visit_pair(self, node, visited_children):
        """ Gets each key/value pair, returns a tuple. """
        key, _, value, *_ = node.children
        return key.text, value.text

    def generic_visit(self, node, visited_children):
        """ The generic visit method. """
        return visited_children or node

def parse_expression(expression: str) -> dict:
    tree = GRAMMAR.parse(expression)
    visitor = ZiffersVisitor()
    return visitor.visit(tree)

