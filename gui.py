import sys

import PyQt5.QtCore
import pyautogui
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QThread
from PyQt5.QtGui import QKeyEvent, QCursor, QTextCursor, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit,QFrame,
    QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout, QLayout
)
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
import re
import main
#____Thread_Worker____
class SeleniumWorker(QThread):
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        try:
            result = self.func(*self.args)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
#____Image_To_Label____
class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 100)
        self.setMaximumSize(1000, 1000)
        self.x_for_scale = 500
        self.y_for_scale = 500
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("⏳ Ожидание изображения...")
        self.setScaledContents(True)  # Автоматическое масштабирование
        self.nam = QNetworkAccessManager()

    def load_image_from_url(self, url: str):
        """Асинхронная загрузка изображения."""
        request = QNetworkRequest(QUrl(url))
        reply = self.nam.get(request)
        reply.finished.connect(lambda: self._on_image_loaded(reply))

    def _on_image_loaded(self, reply):
        """Обработка загруженного изображения."""
        if reply.error() == 0:  # Успешная загрузка
            pixmap = QPixmap()
            if pixmap.loadFromData(reply.readAll()):
                self._display_pixmap(pixmap)
            else:
                self.setText("❌ Ошибка: не удалось декодировать изображение")
        else:
            self.setText(f"❌ Ошибка сети: {reply.errorString()}")
        reply.deleteLater()

    def _display_pixmap(self, pixmap: QPixmap):
        """Масштабирует изображение, чтобы оно вписалось в бокс, сохраняя пропорции."""
        wight_new = pixmap.width()
        height_new = pixmap.height()
        k = wight_new / height_new
        if pixmap.width()>pixmap.height():
            if pixmap.width() > self.x_for_scale or pixmap.width() < self.y_for_scale:
                wight_new = self.width()
                height_new = int(1/k*wight_new)
        if pixmap.width() <= pixmap.height():
            if pixmap.height() > self.x_for_scale or pixmap.height() < self.y_for_scale:
                height_new = self.height()
                wight_new = int(k*height_new)
        scaled_pixmap = pixmap.scaled(
            wight_new, height_new,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation  # Сглаживание для качества
        )
        self.setFixedSize(wight_new,height_new)
        self.setPixmap(scaled_pixmap)
#____Test_Tag_Frame____
class TagWidget(QFrame):
    """Один тег: текст + кнопка удаления."""
    removed = pyqtSignal()  # сигнал, что тег хотят удалить

    def __init__(self, text: str, type=None, parent=None):
        super().__init__(parent)
        self.text = text
        self.type = type

        # Layout внутри тега
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 2, 2)
        layout.setSpacing(4)

        # Текст
        self.label = QLabel(text)
        layout.addWidget(self.label)

        # Кнопка "×"
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.clicked.connect(self.removed.emit)
        layout.addWidget(self.close_btn)
        # Стилизация
        self.setStyleSheet("""
            TagWidget {
                background-color: #e3f2fd;
                border: 2px solid #90caf9;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
                color: #1565c0;
                font-size: 12px;
            }
            QPushButton {
                background: transparent;
                border: none;
                color: #1565c0;
                font-weight: bold;
                font-size: 14px;
                padding: 0;
            }
            QPushButton:hover { color: #d32f2f; }
        """)


class FlowLayout(QLayout):
    """Layout, который переносит виджеты на новую строку, если не хватает места."""
    def __init__(self, parent=None, margin=4, spacing=4):
        super().__init__(parent)
        self._items = []
        self._margin = margin
        self._spacing = spacing

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(PyQt5.QtCore.QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = PyQt5.QtCore.QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self._margin * 2
        size += PyQt5.QtCore.QSize(m, m)
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x() + self._margin
        y = rect.y() + self._margin
        line_height = 0

        for item in self._items:
            wid = item.widget()
            space = self._spacing
            item_size = item.sizeHint()
            next_x = x + item_size.width() + space
            if next_x - space > rect.right() and line_height > 0:
                x = rect.x() + self._margin
                y = y + line_height + space
                next_x = x + item_size.width() + space
                line_height = 0
            if not test_only:
                item.setGeometry(PyQt5.QtCore.QRect(PyQt5.QtCore.QPoint(x, y), item_size))
            x = next_x
            line_height = max(line_height, item_size.height())

        return y + line_height - rect.y() + self._margin

class TagInputWidget(QWidget):
    submitted = pyqtSignal()
    def __init__(self, textbox:CommandEdit()=None, parent=None):
        super().__init__(parent)
        self.promt_text=textbox

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(4, 4, 4, 4)

        # Контейнер для тегов с FlowLayout
        self.tags_container = QWidget()
        self.tags_layout = FlowLayout(self.tags_container, margin=2, spacing=4)
        self.main_layout.addWidget(self.tags_container)

        # Поле ввода
        self.input = QLineEdit()
        self.input.setPlaceholderText("Введите слово и нажмите Enter...")
        self.input.returnPressed.connect(self._add_tag_from_input)
        self.main_layout.addWidget(self.input)

        # Общий стиль «поля» — как будто это один виджет
        self.setStyleSheet("""
            TagInputWidget {
                background-color: white;
                border: 1px solid #bdbdbd;
                border-radius: 6px;
            }
            QLineEdit {
                border: none;
                background: transparent;
                padding: 4px;
            }
        """)

    def add_tag(self, text: str):
        text = text.strip()
        if not text:
            return
        tag = TagWidget(text)
        tag.removed.connect(lambda: self._remove_tag(tag))
        self.tags_layout.addWidget(tag)

    def replace_tags(self, tags: list[str]):
        print("hello")
        self._remove_all_tags_no_refresh()
        [self.add_tag(tag)
        for tag in tags]

    def refresh_text(self):
        tags = self.get_tags()
        if len(tags) == 0:
            self.promt_text.setText("")
            return
        self.promt_text.setText("")
        app_string = ""
        for tag in tags:
            if (tag == tags[0]):
                app_string+=f"{tag}"
            else:
                app_string+=f", {tag}"
        self.promt_text.setText(app_string)

    def _remove_tag(self, tag: TagWidget):
        print(self.get_tags()[0])
        self.tags_layout.removeWidget(tag)
        tag.setParent(None)
        tag.deleteLater()
        self.refresh_text()

    def _add_tag_from_input(self):
        text = self.input.text()
        if text == "":
            self.submitted.emit()
        self.tag = TagWidget(text)
        self.add_tag(text)
        self.input.clear()
        self.refresh_text()

    def _remove_all_tags(self):
        while self.tags_layout.count()>0:
            widget = self.tags_layout.itemAt(0).widget()
            widget.setParent(None)
            widget.deleteLater()
        self.promt_text.setText("")

    def _remove_all_tags_no_refresh(self):
        while self.tags_layout.count()>0:
            widget = self.tags_layout.itemAt(0).widget()
            widget.setParent(None)
            widget.deleteLater()

    def get_tags(self) -> list[str]:
        return [
            self.tags_layout.itemAt(i).widget().text
            for i in range(self.tags_layout.count())
        ]
#____Placers_Classes____
class CommandEdit(QTextEdit):
    submitted = pyqtSignal()
    updated = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Enter — выполнить, Shift+Enter — перенос")
        self.setMinimumHeight(70)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                # Shift+Enter → обычный перенос строки
                super().keyPressEvent(event)
            else:
                # Enter → Вызов сигнала вывода
                self.submitted.emit()
        else:
            super().keyPressEvent(event)
            cursor_pos = self.textCursor().position()
            list = self.parse_text(self.toPlainText())
            self.updated.emit(list)
            cursor = self.textCursor()
            cursor.setPosition(cursor_pos)
            self.setTextCursor(cursor)

    def parse_text(self,text: str) -> list[str]:
        normalized = text.replace("\n", " ")
        parts = normalized.split(",")
        return [p.strip() for p in parts if p.strip()]

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ВК - КОНТОРА ПИДАРАСОВ")
        self.resize(500, 600)

        # Виджеты
        self.label1 = QLabel("Интерактивный промт:")
        self.label2 = QLabel("Текстовый промт:")
        self.input_promt = CommandEdit()
        self.button_clear_tags = QPushButton("Очистить")
        self.button = QPushButton("Отправить")
        self.button_repeat = QPushButton("Повторить")
        self.button_upgrade = QPushButton("Улучшить")
        self.tag_input = TagInputWidget(self.input_promt)
        self.result_pic = ImageLabel()

        # Компоновка
        layout = QVBoxLayout()
        main_layout = QHBoxLayout()
        result_layout = QVBoxLayout()
        result_layout.addWidget(self.result_pic)
        main_layout.addLayout(layout)
        main_layout.addLayout(result_layout)
        layout.addWidget(self.label1, 1, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.tag_input)
        layout.addWidget(self.button_clear_tags, 1, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.label2,1,Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.input_promt,10,Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.button,1,Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.button_repeat, 1, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.button_upgrade, 1, Qt.AlignmentFlag.AlignTop)
        self.setLayout(main_layout)

        # Сигнально-слотовая связь
        self.button.clicked.connect(self.click_generation)
        self.input_promt.submitted.connect(self.click_generation)
        self.button_repeat.clicked.connect(self.click_repeat)
        self.button_upgrade.clicked.connect(self.click_upgrade)
        self.button_clear_tags.clicked.connect(self.tag_input._remove_all_tags)
        self.tag_input.submitted.connect(self.click_generation)
        self.input_promt.updated.connect(self.tag_input.replace_tags)
    #____Нажатия____
    def disable_buttons(self):
        self.button.setEnabled(False)
        self.button_repeat.setEnabled(False)
        self.button_upgrade.setEnabled(False)
    def enable_buttons(self):
        self.button.setEnabled(True)
        self.button_repeat.setEnabled(True)
        self.button_upgrade.setEnabled(True)

    def click_generation(self):
        self.disable_buttons()
        main.CHECK(driver)

        name = self.input_promt.toPlainText().replace("\n", " ") or "rat-girl, crying, @kanekoshake, space purple hair, black eyes, bikini, safe, space background, galaxies"
        last_message = int(main.GET_LAST_MESSAGE(driver))
        print("check")

        # Вся последовательность в одном worker'е
        self.worker = SeleniumWorker(
            main.GENERATE_AND_WAIT,
            driver,
            lambda d: main.PRINT_MESSAGE(d, f"gen {name}"),
            last_message+1
        )
        print("check2")
        self.worker.result_ready.connect(self._on_generation_done)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def click_repeat(self):
        self.disable_buttons()
        main.CHECK(driver)

        last_message = int(main.GET_LAST_MESSAGE(driver))

        self.worker = SeleniumWorker(
            main.GENERATE_AND_WAIT,
            driver,
            main.REPEAT_GENERATION,
            last_message
        )
        self.worker.result_ready.connect(self._on_generation_done)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def click_upgrade(self):
        self.disable_buttons()
        main.CHECK(driver)

        last_message = int(main.GET_LAST_MESSAGE(driver))

        self.worker = SeleniumWorker(
            main.GENERATE_AND_WAIT,
            driver,
            main.UPGRADE_GENERATION,
            last_message
        )
        self.worker.result_ready.connect(self._on_generation_done)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def _on_generation_done(self, url):
        """Обработчик результата генерации."""
        if url:
            self.result_pic.load_image_from_url(url)
        else:
            print("Генерация не удалась")
        self.enable_buttons()

    def _on_error(self, err):
        print(f"Ошибка: {err}")
        self.enable_buttons()
    #____Изменение_размеров/положения_окна____
    def show_half_screen(window, side="left"):
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()
        width = geo.width() // 2
        height = geo.height()
        if side == "left":
            x = geo.x()
        elif side == "right":
            x = geo.x() + geo.width() - width
        else:
            raise ValueError("side должен быть 'left' или 'right'")
        y = geo.y()
        window.setGeometry(x, y, width, height)

    def snap_window(window,side="left"):
        pyautogui.hotkey('win', side)


if __name__ == "__main__":
    driver = main.OPEN(9222)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    #window.snap_window("right")
    sys.exit(app.exec_())
    main.CLOSE(driver)