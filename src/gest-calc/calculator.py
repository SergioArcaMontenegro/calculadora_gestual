class CalculatorLogic:
    def __init__(self):
        self.expression = ""
        self.last_result = ""
        self.max_length = 16

    def input(self, value: str) -> None:
        if value == "C":
            self.clear()
        elif value == "<":
            self.backspace()
        elif value == "=":
            self.evaluate()
        else:
            self.append_char(value)

    def append_char(self, char: str) -> None:
        if len(self.expression) >= self.max_length:
            return

        operators = {"+", "-", "*", "/"}
        
        if self.expression == "Error":
            self.expression = ""

        if not self.expression:
            if char in {"+", "*", "/"}:
                return
            if char == ".":
                self.expression = "0."
                return
            self.expression += char
            return

        last_char = self.expression[-1]

        if char in operators:
            if last_char in operators:
                self.expression = self.expression[:-1] + char
            else:
                self.expression += char
            return

        if char == ".":
            tokens = []
            current = ""
            for c in self.expression:
                if c in operators:
                    tokens.append(current)
                    current = ""
                else:
                    current += c
            tokens.append(current)
            if "." in tokens[-1]:
                return
            if last_char in operators:
                self.expression += "0."
                return

        self.expression += char

    def backspace(self) -> None:
        if self.expression == "Error":
            self.expression = ""
        else:
            self.expression = self.expression[:-1]

    def clear(self) -> None:
        self.expression = ""

    def evaluate(self) -> None:
        if not self.expression or self.expression == "Error":
            return

        operators = {"+", "-", "*", "/"}
        clean_expr = self.expression
        while clean_expr and clean_expr[-1] in operators:
            clean_expr = clean_expr[:-1]

        if not clean_expr:
            return

        try:
            allowed_chars = set("0123456789+-*/. ")
            if not all(c in allowed_chars for c in clean_expr):
                raise ValueError("Caracteres no permitidos")

            result = eval(clean_expr, {"__builtins__": None}, {})
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 6)

            self.last_result = f"{clean_expr} = {result}"
            self.expression = str(result)
        except ZeroDivisionError:
            self.last_result = self.expression
            self.expression = "Error: Div/0"
        except Exception:
            self.expression = "Error"
