import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QVBoxLayout
)
from PyQt5.QtCore import Qt


class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Calculator")
        self.setStyleSheet("background-color: #0a0a0a;")
        self.setFixedSize(360, 480)
        self.create_ui()

    def create_ui(self):
        # 전체 레이아웃
        vbox = QVBoxLayout()
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setStyleSheet(
            "background-color: black; color: white; font-size: 36px; padding: 10px; border: none;"
        )
        self.display.setText("0")
        vbox.addWidget(self.display)

        # 버튼 그리드 레이아웃
        grid = QGridLayout()
        buttons = [
            ('AC', 'gray'), ('±', 'gray'), ('%', 'gray'), ('÷', 'orange'),
            ('7', 'dark'), ('8', 'dark'), ('9', 'dark'), ('×', 'orange'),
            ('4', 'dark'), ('5', 'dark'), ('6', 'dark'), ('−', 'orange'),
            ('1', 'dark'), ('2', 'dark'), ('3', 'dark'), ('+', 'orange'),
            ('0', 'dark', 2), ('.', 'dark'), ('=', 'orange')
        ]

        # 버튼 배치
        row, col = 0, 0
        for btn in buttons:
            text = btn[0]
            color = btn[1]
            span = btn[2] if len(btn) == 3 else 1
            button = QPushButton(text)
            button.setStyleSheet(self.get_button_style(color))
            button.clicked.connect(self.on_button_click)
            if span == 2:
                grid.addWidget(button, row, col, 1, 2)
                col += 1  # 추가 span 고려
            else:
                grid.addWidget(button, row, col, 1, 1)
            col += 1
            if col > 3:
                col = 0
                row += 1

        vbox.addLayout(grid)
        self.setLayout(vbox)

    def get_button_style(self, color):
        colors = {
            'gray': 'background-color: #a5a5a5; color: black;',
            'dark': 'background-color: #333333; color: white;',
            'orange': 'background-color: #ff9500; color: white;'
        }
        return f"{colors[color]} font-size: 24px; border-radius: 40px; padding: 20px;"

    def on_button_click(self):
        btn_text = self.sender().text()
        current_text = self.display.text()

        if btn_text == "AC":
            self.display.setText("0")
        elif btn_text == "=":
            try:
                expression = current_text.replace("×", "*").replace("÷", "/").replace("−", "-")
                result = str(eval(expression))
                self.display.setText(result)
            except Exception:
                self.display.setText("Error")
        elif btn_text == "±":
            if current_text.startswith("-"):
                self.display.setText(current_text[1:])
            else:
                self.display.setText("-" + current_text)
        elif btn_text == "%":
            try:
                result = str(float(current_text) / 100)
                self.display.setText(result)
            except Exception:
                self.display.setText("Error")
        else:
            if current_text == "0" and btn_text not in (".", "÷", "×", "−", "+"):
                self.display.setText(btn_text)
            else:
                self.display.setText(current_text + btn_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    calc = Calculator()
    calc.show()
    sys.exit(app.exec_())
