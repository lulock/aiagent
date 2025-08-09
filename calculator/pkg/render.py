# render.py

def render(expression, result):
    if isinstance(result, float) and result.is_integer():
        result_str = str(int(result))
    else:
        result_str = str(result)

    box_width = int(max(len(expression), len(result_str)) + 4)

    top_border = "┌" + "" .join(["─" for _ in range(box_width)]) + "┐"
    expression_line = "│  " + expression + "" .join([" " for _ in range(box_width - len(expression) - 2)]) + "│"
    empty_line = "│" + "" .join([" " for _ in range(box_width)]) + "│"
    equals_line = "│  =" + "" .join([" " for _ in range(box_width - 3)]) + "│"
    result_line = "│  " + result_str + "" .join([" " for _ in range(box_width - len(result_str) - 2)]) + "│"
    bottom_border = "└" + "" .join(["─" for _ in range(box_width)]) + "┘"

    box = [top_border, expression_line, empty_line, equals_line, empty_line, result_line, bottom_border]
    return "\n".join(box)
