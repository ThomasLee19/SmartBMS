from PySide6.QtWidgets import QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QDialog, QCheckBox, QDateTimeEdit, QMessageBox
from PySide6.QtCore import QDateTime, QSize

class RepeatRulesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Repeat Rules")
        self.day_specifiers = []  # 存储所有的Day Specifiers

        # 创建提示标签
        self.prompt_label = QLabel("Please select the type of the new repeat specifier:", self)

        # 创建按钮
        self.day_button = QPushButton("Day Specifier", self)
        self.time_button = QPushButton("Time Specifier", self)

        # 创建当前规则显示标签
        self.current_rules_label = QLabel("Current Repeat Rules: None", self)

        # 水平布局放置按钮
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.day_button)
        button_layout.addWidget(self.time_button)

        # 垂直布局放置所有控件
        layout = QVBoxLayout()
        layout.addWidget(self.prompt_label)
        layout.addLayout(button_layout)
        layout.addWidget(self.current_rules_label)

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

    def open_day_specifier_dialog(self):
        dialog = DaySpecifierDialog(self)
        if dialog.exec_():
            specifier = dialog.get_selected_days()
            self.day_specifiers.append(specifier)  # 保存新的规则
            self.update_rules()  # 更新显示的规则

    def update_rules(self):
        if self.day_specifiers:
            rules_text = "Current Repeat Rules:\n"
            for index, specifier in enumerate(self.day_specifiers, 1):
                days = specifier[0]
                excluded_times = specifier[1:]
                rules_text += f"{index}. Day Repeat Specifier: {days}\n"
                if excluded_times:
                    rules_text += f"    Excluded Time: {', '.join(excluded_times)}\n"
        else:
            rules_text = "Current Repeat Rules: None"
        self.current_rules_label.setText(rules_text)

    def attempt_save(self):
        if not self.day_specifiers:
            QMessageBox.critical(self, "Error", "No repeat rules have been set. Save failed.")
            return
        self.accept()

    def get_current_rules(self):
        if not self.day_specifiers:
            return None
        return self.day_specifiers

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
        return (selected_days, *excluded_times)

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