
ebnf = r"""
    expr = (bar / octup / octdown / escape / rhythm / float / chord / pc / ws?)+

    escape = (lt (chord / pc) gt)

    chord     = pc{2,}
    pc        = (neg_pc / pc_basic)
    neg_pc    = (~r"-" pc)
    pc_basic  = ~r"[0-9TE]"

    rhythm    = ~r"[mklpdcwyhnqaefsxtgujoz]"

    float     = ~r"\d+\.\d+"

    lpar      = "("
    rpar      = ")"
    lbra      = "["
    rbra      = "]"
    lcbra     = "{"
    rcbra     = "}"
    lt        = "<"
    gt        = ">"


    octup     = "^"
    octdown   = "_"

    bar       = "|"

    plus = "+"
    minus = "-"
    times = "*"
    div   = "/"

    emptyline = ws+
    comma     = ","
    ws        = ~"\s*"
    """
