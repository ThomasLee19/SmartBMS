from PySide6.QtWidgets import QPushButton, QVBoxLayout, QLabel, QLineEdit, QMessageBox, QScrollArea
from PySide6.QtWidgets import QHBoxLayout, QDialog, QCheckBox, QDateTimeEdit, QFormLayout, QWidget
from PySide6.QtCore import QDateTime, QSize, Qt, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from functools import partial

class RepeatRulesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Repeat Rules")
        self.resize(400, 300)
        self.specifiers = []  # 存储所有的Day Specifiers

        # 创建提示标签
        self.prompt_label = QLabel("Please select the type of the new repeat specifier:", self)

        # 创建按钮
        self.day_button = QPushButton("Day Specifier", self)
        self.time_button = QPushButton("Time Specifier", self)

        # 创建滚动区域和其内容容器
        self.scroll_area = QScrollArea(self)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)

        # 水平布局放置按钮
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.day_button)
        button_layout.addWidget(self.time_button)

        # 垂直布局放置所有控件
        layout = QVBoxLayout()
        layout.addWidget(self.prompt_label)
        layout.addLayout(button_layout)
        layout.addWidget(self.scroll_area)

        # 添加保存和取消按钮
        self.save_button = QPushButton("Save", self)
        self.cancel_button = QPushButton("Cancel", self)
        self.save_button.clicked.connect(self.attempt_save)
        self.cancel_button.clicked.connect(self.reject)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 连接按钮的点击事件
        self.day_button.clicked.connect(self.open_day_specifier_dialog)
        self.time_button.clicked.connect(self.open_time_specifier_dialog)

        self.update_rules()

    def update_rules(self):
        # 清除旧的规则显示
        self.clear_layout(self.scroll_layout)

        # 添加一个标签来显示 "Current Repeat Rules"
        if self.specifiers:
            header_label = QLabel("Current Repeat Rules:")
            self.scroll_layout.addWidget(header_label)

            # 首先对specifiers进行排序，0在前，1在后
            self.specifiers.sort(key=lambda x: x[0])

            for index, specifier in enumerate(self.specifiers, 1):
                specifier_type = specifier[0]
                days = specifier[1]
                excluded_times = specifier[2:]

                # 创建规则描述和删除按钮
                rule_layout = QHBoxLayout()
                rule_label_text = f"{index}. "
                rule_label_text += "Day Repeat Specifier: " if specifier_type == 0 else "Time Repeat Specifier: "
                rule_label_text += f"{days}"
                rule_label = QLabel(rule_label_text)
                delete_button = QPushButton("-")
                delete_button.setFixedSize(QSize(20, 20))
                delete_button.clicked.connect(partial(self.remove_specifier, index-1))
                rule_layout.addWidget(rule_label)
                rule_layout.addWidget(delete_button)

                # 创建一个临时QWidget来包装布局
                rule_widget = QWidget()
                rule_widget.setLayout(rule_layout)
                self.scroll_layout.addWidget(rule_widget)

                # 如果有排除时间，将其显示在新的一行
                if excluded_times:
                    excluded_time_layout = QHBoxLayout()
                    excluded_time_label = QLabel(f"    Excluded Time: {', '.join(excluded_times)}")
                    excluded_time_layout.addWidget(excluded_time_label)
                    excluded_time_widget = QWidget()
                    excluded_time_widget.setLayout(excluded_time_layout)
                    self.scroll_layout.addWidget(excluded_time_widget)
        else:
            # 如果没有规则，显示None
            no_rules_label = QLabel("Current Repeat Rules: None")
            self.scroll_layout.addWidget(no_rules_label)

    def remove_specifier(self, index):
        del self.specifiers[index]
        self.update_rules()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                self.clear_layout(item.layout())

    def open_day_specifier_dialog(self):
        dialog = DaySpecifierDialog(self)
        if dialog.exec_():
            day_specifier = dialog.get_selected_days()
            self.specifiers.append(day_specifier)  # 保存新的规则
            self.update_rules()  # 更新显示的规则

    def open_time_specifier_dialog(self):
        dialog = TimeSpecifierDialog(self)
        if dialog.exec_():
            time_specifier = dialog.get_selected_time()
            self.specifiers.append(time_specifier)
            self.update_rules()

    def attempt_save(self):
        if not self.specifiers:
            QMessageBox.critical(self, "Error", "No repeat rules have been set. Save failed.")
            return
        self.accept()

    def get_current_rules(self):
        if not self.specifiers:
            return None
        return self.specifiers

class DaySpecifierDialog(QDialog):
    def __init__(self, parent=None):
        super(DaySpecifierDialog, self).__init__(parent)
        self.setWindowTitle("Set Day Repeat")
        self.layout = QVBoxLayout(self)

        # 添加提示信息
        self.info_label = QLabel("Please select the days on which the event repeats")
        self.layout.addWidget(self.info_label)

        # 复选框初始化
        self.checkboxes = {
            "Mo": QCheckBox("Monday"),
            "Tu": QCheckBox("Tuesday"),
            "We": QCheckBox("Wednesday"),
            "Th": QCheckBox("Thursday"),
            "Fr": QCheckBox("Friday"),
            "Sa": QCheckBox("Saturday"),
            "Su": QCheckBox("Sunday")
        }
        for checkbox in self.checkboxes.values():
            self.layout.addWidget(checkbox)
            checkbox.stateChanged.connect(self.update_selected_days)

        # 选择的天显示标签
        self.selected_days_label = QLabel("Selected Days: None")
        self.layout.addWidget(self.selected_days_label)

        # Excluded Time 输入部分
        self.excluded_time_layout = QHBoxLayout()
        self.excluded_time_label = QLabel("Excluded Time:")
        self.excluded_time_layout.addWidget(self.excluded_time_label)

        self.excluded_times = []
        self.add_excluded_time_button = QPushButton("+")
        self.add_excluded_time_button.clicked.connect(self.add_excluded_time_input)
        self.add_excluded_time_button.setFixedSize(QSize(20, 20))

        self.remove_excluded_time_button = QPushButton("-")
        self.remove_excluded_time_button.clicked.connect(self.remove_excluded_time_input)
        self.remove_excluded_time_button.setFixedSize(QSize(20, 20))

        self.excluded_time_layout.addWidget(self.add_excluded_time_button)
        self.excluded_time_layout.addWidget(self.remove_excluded_time_button)
        self.layout.addLayout(self.excluded_time_layout)

        # 时间输入行的容器
        self.time_inputs_layout = QVBoxLayout()
        self.layout.addLayout(self.time_inputs_layout)

        # 确定和取消按钮
        self.buttons_layout = QHBoxLayout()
        self.ok_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.buttons_layout.addWidget(self.ok_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.buttons_layout)

        self.ok_button.clicked.connect(self.attempt_accept)
        self.cancel_button.clicked.connect(self.reject)

    def add_excluded_time_input(self):
        datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        datetime_edit.setCalendarPopup(True)
        datetime_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.time_inputs_layout.addWidget(datetime_edit)
        self.excluded_times.append(datetime_edit)

    def remove_excluded_time_input(self):
        if self.excluded_times:
            datetime_edit = self.excluded_times.pop()
            datetime_edit.deleteLater()

    def update_selected_days(self):
        selected_days = [day for day, checkbox in self.checkboxes.items() if checkbox.isChecked()]
        day_names = [checkbox.text() for day, checkbox in self.checkboxes.items() if checkbox.isChecked()]
        self.selected_days_label.setText(f"Selected Days: {', '.join(day_names)}")

    def get_selected_days(self):
        selected_days = ', '.join([day for day, checkbox in self.checkboxes.items() if checkbox.isChecked()])
        # 将每个排除时间作为单独的元素存储
        excluded_times = [datetime_edit.dateTime().toString("yyyyMMddHHmm") for datetime_edit in self.excluded_times]
        return (0, selected_days, *excluded_times)

    def attempt_accept(self):
        # 检查是否有天被选中
        if not any(checkbox.isChecked() for checkbox in self.checkboxes.values()):
            QMessageBox.critical(self, "Error", "You have not set the Day Specifier, save failed.")
            return
        
        # 检查排除时间是否有重复
        times = [datetime_edit.dateTime().toString("yyyyMMddHHmm") for datetime_edit in self.excluded_times]
        if len(times) != len(set(times)):
            QMessageBox.critical(self, "Error", "There is a duplicate Excluded Time, save failed.")
            return
        self.accept()

class TimeSpecifierDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Time Repeat")
        self.init_ui()

    def init_ui(self):
        # 创建提示标签和表单布局
        prompt_label = QLabel("Please enter each part of the time format, use '*' for wildcards:", self)
        form_layout = QFormLayout()

        # 初始化输入框和设置验证器
        self.initialize_input_fields()

        # 添加输入框到表单
        self.add_input_fields_to_form(form_layout)

        # 初始化 Excluded Time 部分
        self.initialize_excluded_time_section()

        # 创建保存和取消按钮，并设置布局
        self.setup_buttons()

        # 主布局
        layout = QVBoxLayout()
        layout.addWidget(prompt_label)
        layout.addLayout(form_layout)
        layout.addLayout(self.excluded_time_layout)
        layout.addLayout(self.time_inputs_layout)
        layout.addLayout(self.buttons_layout)
        self.setLayout(layout)

    def initialize_input_fields(self):
        self.year_edit = QLineEdit(self)
        self.month_edit = QLineEdit(self)
        self.day_edit = QLineEdit(self)
        self.hour_edit = QLineEdit(self)
        self.minute_edit = QLineEdit(self)

        # 设置正则表达式验证器
        year_regex = QRegularExpression("([0-9*]{4})")
        month_day_hour_minute_regex = QRegularExpression("([0-9*]{2})")
        
        self.year_edit.setValidator(QRegularExpressionValidator(year_regex, self))
        self.month_edit.setValidator(QRegularExpressionValidator(month_day_hour_minute_regex, self))
        self.day_edit.setValidator(QRegularExpressionValidator(month_day_hour_minute_regex, self))
        self.hour_edit.setValidator(QRegularExpressionValidator(month_day_hour_minute_regex, self))
        self.minute_edit.setValidator(QRegularExpressionValidator(month_day_hour_minute_regex, self))

    def add_input_fields_to_form(self, form_layout):
        form_layout.addRow("Year (YYYY):", self.year_edit)
        form_layout.addRow("Month (MM):", self.month_edit)
        form_layout.addRow("Day (DD):", self.day_edit)
        form_layout.addRow("Hour (HH):", self.hour_edit)
        form_layout.addRow("Minute (mm):", self.minute_edit)

    def initialize_excluded_time_section(self):
        self.excluded_time_layout = QHBoxLayout()
        self.excluded_time_label = QLabel("Excluded Time:")
        self.excluded_time_layout.addWidget(self.excluded_time_label)
        self.excluded_times = []

        self.add_excluded_time_button = QPushButton("+")
        self.add_excluded_time_button.clicked.connect(self.add_excluded_time_input)
        self.add_excluded_time_button.setFixedSize(QSize(20, 20))

        self.remove_excluded_time_button = QPushButton("-")
        self.remove_excluded_time_button.clicked.connect(self.remove_excluded_time_input)
        self.remove_excluded_time_button.setFixedSize(QSize(20, 20))

        self.excluded_time_layout.addWidget(self.add_excluded_time_button)
        self.excluded_time_layout.addWidget(self.remove_excluded_time_button)
        self.time_inputs_layout = QVBoxLayout()

    def setup_buttons(self):
        self.save_button = QPushButton("Save", self)
        self.cancel_button = QPushButton("Cancel", self)
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.save_button.clicked.connect(self.save_time_format)
        self.cancel_button.clicked.connect(self.reject)

    def add_excluded_time_input(self):
        datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        datetime_edit.setCalendarPopup(True)
        datetime_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.time_inputs_layout.addWidget(datetime_edit)
        self.excluded_times.append(datetime_edit)

    def remove_excluded_time_input(self):
        if self.excluded_times:
            datetime_edit = self.excluded_times.pop()
            datetime_edit.deleteLater()

    def get_selected_time(self):
        # 获取各部分的输入
        year = self.year_edit.text()
        month = self.month_edit.text()
        day = self.day_edit.text()
        hour = self.hour_edit.text()
        minute = self.minute_edit.text()

        # 组合输入数据
        time_format = f"{year}{month}{day}{hour}{minute}"
        # 将每个排除时间作为单独的元素存储
        excluded_times = [datetime_edit.dateTime().toString("yyyyMMddHHmm") for datetime_edit in self.excluded_times]
        return (1, time_format, *excluded_times)

    def save_time_format(self):
        # 获取各部分的输入
        year = self.year_edit.text()
        month = self.month_edit.text()
        day = self.day_edit.text()
        hour = self.hour_edit.text()
        minute = self.minute_edit.text()

        # 组合输入数据
        time_format = f"{year}{month}{day}{hour}{minute}"

        # 检查是否没有设置Time format
        if not any([year, month, day, hour, minute]):
            QMessageBox.critical(self, "Error", "You have not set the Time Specifier, save failed.")
            return

        # 检查是否全部为通配符
        if time_format.count('*') == 12:
            QMessageBox.critical(self, "Error", "The time format cannot be all '*'. Please specify at least one part.")
            return

        # 检查每个部分是否完全填满
        if not all([len(year) == 4, len(month) == 2, len(day) == 2, len(hour) == 2, len(minute) == 2]):
            QMessageBox.critical(self, "Error", "Each part of the time format must be fully filled. Please correct your entries.")
            return
        
        if not self.validate_time_format(year, month, day, hour, minute):
            QMessageBox.critical(self, "Error", "Invalid date or time format.")
            return

        # 检查排除时间是否有重复
        times = [datetime_edit.dateTime().toString("yyyyMMddHHmm") for datetime_edit in self.excluded_times]
        if len(times) != len(set(times)):
            QMessageBox.critical(self, "Error", "There is a duplicate Excluded Time, save failed.")
            return

        # 检查Time format是否全为数字，如果是，则不允许设置Excluded Time
        if time_format.isdigit() and self.excluded_times:
            QMessageBox.critical(self, "Error", "Exclusion time cannot be set for specific time repetitions.")
            return

        self.accept()
    
    def validate_time_part(self, part, first_digit_options, second_digit_map):
        if len(part) != 2:
            return False
        first_digit, second_digit = part[0], part[1]
        valid_second_digits = second_digit_map.get(first_digit, '*')  # 默认允许任何值，如果第一位是星号
        if (first_digit not in first_digit_options + '*') or (second_digit not in valid_second_digits + '*'):
            return False
        return True

    def validate_year(self, year):
        return len(year) == 4 and all(c.isdigit() or c == '*' for c in year)

    def validate_time_format(self, year, month, day, hour, minute):
        if not self.validate_year(year):
            return False
        if not all([len(month) == 2, len(day) == 2, len(hour) == 2, len(minute) == 2]):
            return False
        if not self.validate_time_part(month, '01', {'0': '123456789', '1': '012'}):
            return False
        if not self.validate_time_part(day, '0123', {'0': '123456789', '1': '0123456789', '2': '0123456789', '3': '01'}):
            return False
        if not self.validate_time_part(hour, '012', {'0': '0123456789', '1': '0123456789', '2': '0123'}):
            return False
        if not self.validate_time_part(minute, '012345', {'0': '0123456789', '1': '0123456789', '2': '0123456789', '3': '0123456789', '4': '0123456789', '5': '0123456789'}):
            return False
        return True