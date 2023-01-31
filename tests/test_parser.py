from ziffers import *

def test_can_parse():
    expressions = [
            "[1 [2 3]]",
            "(1 (1,3) 1..3)",
            "_^ q _qe^3 qww_4 _123 <1 2>",
            "q _2 _ 3 ^ 343",
            "2 qe2 e4",
            "q 2 <3 343>",
            "q (2 <3 343 (3 4)>)",
    ]
    results = []
    for expression in expressions:
        try:
            print(f"Parsing expression: {expression}")
            result = parse_expression(expression)
            results.append(True)
        except Exception as e:
            print(e)
            results.append(False)

    # Return true if all the results are true (succesfully parsed)
    print(results)
    assert all(results)

#print(ziffers_parser.parse("[1 [2 3]]"))
#print(ziffers_parser.parse("(1 (1,3) 1..3)"))
#print(ziffers_parser.parse("_^ q _qe^3 qww_4 _123 <1 2>"))
#print(ziffers_parser.parse("q _2 _ 3 ^ 343"))
#print(ziffers_parser.parse("2 qe2 e4").values)
#print(ziffers_parser.parse("q 2 <3 343>"))
#print(ziffers_parser.parse("q (2 <3 343 (3 4)>)"))
