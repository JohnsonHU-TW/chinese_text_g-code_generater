import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt
from UI.ui import Ui_MainWindow
from PyQt6 import QtWidgets, QtGui
import os
import shutil
from generate_gcode import gen_main

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.bt_gen.clicked.connect(self.on_bt_gen_click)
        self.grview = self.ui.preview_window
        self.ui.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ui.bt_pre_page.clicked.connect(
            self.on_bt_pre_page_click)
        self.ui.bt_next_page.clicked.connect(self.on_bt_next_page_click)
        self.ui.input_area.textChanged.connect(self.enforce_line_limit)
        self.ui.sl_text_size.valueChanged.connect(self.enforce_line_limit)
        self.ui.sl_xspace.valueChanged.connect(self.enforce_line_limit)
        self.ui.sl_yspace.valueChanged.connect(self.enforce_line_limit)
        self.ui.sl_padding.valueChanged.connect(self.enforce_line_limit)


    def enforce_line_limit(self):
        padding = self.ui.sl_padding.value()
        font_size = self.ui.sl_text_size.value()
        x_spacing = self.ui.sl_xspace.value()

        max_chars_per_line = (2100 - 2*padding) // (font_size + x_spacing) # 同gen... .py

        text = self.ui.input_area.toPlainText()
        cursor = self.ui.input_area.textCursor()
        cursor_position = cursor.position()

        lines = text.split('\n')
        new_lines = []

        for line in lines:
            while len(line) > max_chars_per_line:
                new_lines.append(line[:max_chars_per_line])  # 分割超過字數的部分
                line = line[max_chars_per_line:]
            new_lines.append(line)

        new_text = '\n'.join(new_lines)
        if new_text != text:
            self.ui.input_area.blockSignals(True)  # 避免卡死
            self.ui.input_area.setPlainText(new_text)
            self.ui.input_area.blockSignals(False)

            cursor.setPosition(min(cursor_position, len(new_text)))
            self.ui.input_area.setTextCursor(cursor)

    def on_bt_next_page_click(self):
        num_pages = [os.path.splitext(file)[0] for file in os.listdir("outputs") if file.endswith(".png")]

        current_page = self.ui.label_7.text()[self.ui.label_7.text().index("共") + 1:self.ui.label_7.text().index("/")]
        print(current_page, len(num_pages))
        if int(current_page) == 0:
            scene = QtWidgets.QGraphicsScene()
            scene.setSceneRect(0, 0, 2100, 2970)
            img = QtGui.QPixmap('outputs/1output.png')
            img = img.scaled(2100, 2970)
            scene.addPixmap(img)
            self.grview.setScene(scene)
            self.grview.resetTransform()
            self.grview.scale(0.2, 0.2)

            self.ui.label_7.setText(f'共 1/{len(num_pages)} 頁')
            self.ui.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)

            with open('outputs/1output.gcode', "r", encoding="utf-8") as file:
                content = file.read()
                self.ui.gcode_window.setText(content)
                num_lines = len(content.splitlines())
                self.ui.num_lens_gcode.setText(f'行數：{num_lines}')


        elif int(current_page) < len(num_pages):
            print('y')

            scene = QtWidgets.QGraphicsScene()
            scene.setSceneRect(0, 0, 2100, 2970)
            img = QtGui.QPixmap(f'outputs/{int(current_page)+1}output.png')
            img = img.scaled(2100, 2970)
            scene.addPixmap(img)
            self.grview.setScene(scene)
            self.grview.resetTransform()
            self.grview.scale(0.2, 0.2)

            self.ui.label_7.setText(f'共 {int(current_page)+1}/{len(num_pages)} 頁')
            self.ui.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)

            with open(f'outputs/{int(current_page)+1}output.gcode', "r", encoding="utf-8") as file:
                content = file.read()
                self.ui.gcode_window.setText(content)
                num_lines = len(content.splitlines())
                self.ui.num_lens_gcode.setText(f'行數：{num_lines}')

    def on_bt_pre_page_click(self):
        num_pages = [os.path.splitext(file)[0] for file in os.listdir("outputs") if file.endswith(".png")]

        current_page = self.ui.label_7.text()[self.ui.label_7.text().index("共") + 1:self.ui.label_7.text().index("/")]
        print(current_page, len(num_pages))
        if int(current_page) == 0:
            scene = QtWidgets.QGraphicsScene()
            scene.setSceneRect(0, 0, 2100, 2970)
            img = QtGui.QPixmap('outputs/1output.png')
            img = img.scaled(2100, 2970)
            scene.addPixmap(img)
            self.grview.setScene(scene)
            self.grview.resetTransform()
            self.grview.scale(0.2, 0.2)

            self.ui.label_7.setText(f'共 1/{len(num_pages)} 頁')
            self.ui.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)

            with open('outputs/1output.gcode', "r", encoding="utf-8") as file:
                content = file.read()
                self.ui.gcode_window.setText(content)
                num_lines = len(content.splitlines())
                self.ui.num_lens_gcode.setText(f'行數：{num_lines}')
        elif int(current_page) > 1:
            print('y')

            scene = QtWidgets.QGraphicsScene()
            scene.setSceneRect(0, 0, 2100, 2970)
            img = QtGui.QPixmap(f'outputs/{int(current_page)-1}output.png')
            img = img.scaled(2100, 2970)
            scene.addPixmap(img)
            self.grview.setScene(scene)
            self.grview.resetTransform()
            self.grview.scale(0.2, 0.2)

            self.ui.label_7.setText(f'共 {int(current_page)-1}/{len(num_pages)} 頁')
            self.ui.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)

            with open(f'outputs/{int(current_page)-1}output.gcode', "r", encoding="utf-8") as file:
                content = file.read()
                self.ui.gcode_window.setText(content)
                num_lines = len(content.splitlines())
                self.ui.num_lens_gcode.setText(f'行數：{num_lines}')

    def on_bt_gen_click(self):
        text = self.ui.input_area.toPlainText()
        text = text.replace('\n', '')
        draw_speed = self.ui.le_drawspeed.text()
        travel_speed = self.ui.le_travelspeed.text()

        font_size = self.ui.sl_text_size.value()
        padding = self.ui.sl_padding.value()
        x_spacing = self.ui.sl_xspace.value()
        y_spacing = self.ui.sl_yspace.value()
        print(text)
        if len(text) != 0:

            with open('strings.txt', "w", encoding="utf-8") as f:
                f.write(text)

            # 先刪除輸出資料夾中所有東東
            directory = "outputs/"
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

            gen_main(font_type="fonts/msjhl.ttc", x_space=x_spacing, y_space=y_spacing, padding=padding, font_size=font_size, feed_rate=draw_speed,
                     traval_speed=travel_speed)

            scene = QtWidgets.QGraphicsScene()
            scene.setSceneRect(0, 0, 2100, 2970)
            img = QtGui.QPixmap('outputs/1output.png')
            img = img.scaled(2100, 2970)
            scene.addPixmap(img)
            self.grview.setScene(scene)
            self.grview.resetTransform()
            self.grview.scale(0.2, 0.2)

            with open('outputs/1output.gcode', "r", encoding="utf-8") as file:
                content = file.read()
                self.ui.gcode_window.setText(content)
                num_lines = len(content.splitlines())
                self.ui.num_lens_gcode.setText(f'行數：{num_lines}')

            num_pages = len([os.path.splitext(file)[0] for file in os.listdir("outputs") if file.endswith(".svg")])
            self.ui.label_7.setText(f'共 1/{num_pages} 頁')
            self.ui.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)

if __name__ == "__main__":
    if not os.path.exists('outputs'):
        os.makedirs('outputs')

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

    # pyuic6 -o UI/ui.py UI/main.ui
    # pyinstaller main.py --noconsole --workpath pack/  --distpath pack/dict
