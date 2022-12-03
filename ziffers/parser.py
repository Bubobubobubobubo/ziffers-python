from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from rich import print
from .ebnf import ebnf

__all__ = ('ZiffersVisitor', 'parse_expression',)

GRAMMAR = Grammar(ebnf)

class ZiffersVisitor(NodeVisitor):

    """
    Visitor for the Ziffers syntax.
    """

    def visit_ziffers(self, node, children):
        """
        Top-level visiter. Will traverse and build something out of a complete and valid
        Ziffers expression.
        """
        print(f"Node: {node}, Children: {children}")
        result = {'ziffers': []}

        for i in children:
            if i[0] in (None, [], {}) and isinstance(i[0], dict):
                continue
            try:
                result['ziffers'].append(i[0])
            except Exception as e:
                print(f"[red]Error in ziffers:[/red] {e}")
                pass
        return result

    def visit_pc(self, node, children):
        return {node.expr_name: node.text}

    def visit_escape(self, node, children):
        return {node.expr_name: node.text}

    # def visit_subdiv(self, node, visited_children):
    #     key, values = visited_children
    #     ret)rn {key, dict(values)}

    def generic_visit(self, node, children):
        """
        This method seem to be the generic method to include in any NodeVisitor.
        Probably better to keep it as is for the moment. This is appending a whole
        lot of garbage to the final expression because I don't really know how to
        write it properly...
        """
        return children or node

def parse_expression(expression: str) -> dict:
    tree = GRAMMAR.parse(expression)
    visitor = ZiffersVisitor()
    return visitor.visit(tree)

