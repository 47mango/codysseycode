import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QVBoxLayout
)
from PyQt5.QtCore import Qt


class Calculator:
    def __init__(self):
        self.reset()

    def reset(self):
        self.current = "0"
        self.operator = None
        self.operand = None
        self.result = None

    def input_digit(self, digit):
        if self.current == "0" and digit != ".":
            self.current = digit
        else:
            if digit == "." and "." in self.current:
                return  # 중복 소수점 방지
            self.current += digit

    def set_operator(self, op):
        if self.current:
            self.operand = float(self.current)
            self.operator = op
            self.current = ""

    def add(self):
        return self.operand + float(self.current)

    def subtract(self):
        return self.operand - float(self.current)

    def multiply(self):
        return self.operand * float(self.current)

    def divide(self):
        try:
            return self.operand / float(self.current)
        except ZeroDivisionError:
            return "Error"

    def percent(self):
        try:
            self.current = str(float(self.current) / 100)
        except Exception:
            self.current = "Error"

    def negative_positive(self):
        try:
            value = float(self.current)
            self.current = str(-value)
        except Exception:
            self.current = "Error"

    def equal(self):
        if not self.operator or not self.current:
            return self.current

        try:
            if self.operator == "+":
                self.result = self.add()
            elif self.operator == "-":
                self.result = self.subtract()
            elif self.operator == "*":
                self.result = self.multiply()
            elif self.operator == "/":
                self.result = self.divide()
            else:
                return "Error"

            # 소수점 6자리 이하 반올림 처리
            if isinstance(self.result, float):
                self.result = round(self.result, 6)

            self.current = str(self.result)
            self.operator = None
            self.operand = None
            return self.current
        except Exception:
            return "Error"


class CalculatorUI(QWidget):
    def __init__(self):
        super().__init__()
        self.calc = Calculator()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Calculator")
        self.setFixedSize(360, 480)
        self.setStyleSheet("background-color: #0a0a0a;")
        self.display = QLineEdit("0")
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setStyleSheet("background-color: black; color: white; font-size: 36px; padding: 10px; border: none;")
        layout = QVBoxLayout()
        layout.addWidget(self.display)

        grid = QGridLayout()
        buttons = [
            ("AC", self.clear), ("±", self.negate), ("%", self.percent), ("÷", lambda: self.operator("/")),
            ("7", lambda: self.digit("7")), ("8", lambda: self.digit("8")), ("9", lambda: self.digit("9")), ("×", lambda: self.operator("*")),
            ("4", lambda: self.digit("4")), ("5", lambda: self.digit("5")), ("6", lambda: self.digit("6")), ("−", lambda: self.operator("-")),
            ("1", lambda: self.digit("1")), ("2", lambda: self.digit("2")), ("3", lambda: self.digit("3")), ("+", lambda: self.operator("+")),
            ("0", lambda: self.digit("0")), (".", lambda: self.digit(".")), ("=", self.equal)
        ]

        row, col = 0, 0
        for text, handler in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(self.button_style(text))
            btn.clicked.connect(handler)
            if text == "0":
                grid.addWidget(btn, row, col, 1, 2)
                col += 1
            else:
                grid.addWidget(btn, row, col, 1, 1)
            col += 1
            if col > 3:
                col = 0
                row += 1

        layout.addLayout(grid)
        self.setLayout(layout)

    def button_style(self, text):
        if text in ["AC", "±", "%"]:
            color = "#a5a5a5; color: black;"
        elif text in ["÷", "×", "−", "+", "="]:
            color = "#ff9500; color: white;"
        else:
            color = "#333333; color: white;"
        return f"background-color: {color} font-size: 24px; border-radius: 40px; padding: 20px;"

    def update_display(self):
        self.display.setText(self.calc.current)

    def digit(self, d):
        self.calc.input_digit(d)
        self.update_display()

    def operator(self, op):
        self.calc.set_operator(op)
        self.update_display()

    def clear(self):
        self.calc.reset()
        self.update_display()

    def percent(self):
        self.calc.percent()
        self.update_display()

    def negate(self):
        self.calc.negative_positive()
        self.update_display()

    def equal(self):
        result = self.calc.equal()
        self.display.setText(result)

    def update_display(self):
        text = self.calc.current

        # 글자 수에 따라 폰트 크기 조절
        length = len(text)
        if length <= 8:
            font_size = 36
        elif length <= 12:
            font_size = 28
        else:
            font_size = 20

        self.display.setStyleSheet(
            f"background-color: black; color: white; font-size: {font_size}px; padding: 10px; border: none;"
        )
        self.display.setText(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalculatorUI()
    window.show()
    sys.exit(app.exec_())
