from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtWidgets import QWidget, QSizePolicy, QSpacerItem, QMessageBox
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt, QDate
from datetime import datetime

from test_event_editing import EventEditDialog, EventDeleter

class EventInfor():

    def __init__(self, parent=None):
        self.parent = parent
        # 传递刷新函数
        self.event_deleter = EventDeleter(refresh_func=self.refresh_events_from_parent)

    def view_event(self, event_name, event_time, setpoint_value, setpoint_type, repeat_rules, schedule_name, zone_id, event_outstation, event_colour):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Event Information")
        dialog.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        dialog.adjustSize()

        # Create a widget to hold the buttons with a fixed width
        button_container = QWidget()
        button_container.setFixedHeight(40)  # Set the fixed width of the container

        # Create horizontal layout for buttons within the container
        button_layout = QHBoxLayout(button_container)

        # Color display
        rgb_tuple = eval(event_colour)
        rgb_css = f"rgb({rgb_tuple[0]}, {rgb_tuple[1]}, {rgb_tuple[2]})"
        color_label = QLabel()
        color_label.setFixedSize(40, 30)  # Set the size of the color display area
        color_label.setStyleSheet(f"background-color: {rgb_css};")
        button_layout.addWidget(color_label)

        button_layout.addStretch(1)

        # 添加一个水平空间
        spacer = QSpacerItem(240, 30)
        button_layout.addItem(spacer)

        # Edit button with icon and fixed size
        edit_button = QPushButton()
        edit_button.setIcon(QIcon('Images/edit_event.jpg'))
        edit_button.setFixedSize(30, 30)
        edit_button.clicked.connect(lambda: self.edit_event(event_name, event_time, setpoint_value, setpoint_type, repeat_rules, schedule_name, zone_id, event_outstation, event_colour, dialog))
        
        # Delete button with icon and fixed size
        delete_button = QPushButton()
        delete_button.setIcon(QIcon('Images/delete_event.jpg'))
        delete_button.setFixedSize(30, 30)
        delete_button.clicked.connect(lambda: self.delete_event(event_name, schedule_name, zone_id, dialog))
        
        # Add buttons to the horizontal layout
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        
        # Main layout
        layout = QVBoxLayout(dialog)
        
        # Add button container to the main layout
        layout.addWidget(button_container)

        # Set Font
        font = QFont()
        font.setPointSize(14)

        # Event information labels
        event_name_label = QLabel(f"Name: {event_name}")
        event_name_label.setFont(font)
        layout.addWidget(event_name_label)

        layout.addWidget(QLabel(f"Time: {event_time.strftime('%Y-%m-%d %H:%M')}"))
        layout.addWidget(QLabel(f"Setpoint Value: {setpoint_value}"))
        layout.addWidget(QLabel(f"Setpoint Type: {setpoint_type}"))

        # Display Repeat Rules
        if repeat_rules:
            repeat_rules_label = QLabel("Repeat Rules:")
            layout.addWidget(repeat_rules_label)
            for index, rule in enumerate(repeat_rules, start=1):
                specifier_type = "Day Specifier" if rule[0] == "day" else "Time Specifier"
                # Convert day abbreviations to full names or format as datetime
                if rule[0] == "day":
                    days = self.convert_days(rule[1])
                else:
                    days = self.format_time(rule[1]) if rule[1].isdigit() else rule[1]

                specifier_text = f"{index}. {specifier_type}: {days}"
                layout.addWidget(QLabel(specifier_text))
                for excluded_time in rule[2:]:
                    formatted_time = self.format_time(excluded_time)
                    excluded_time_text = f"    Excluded Time: {formatted_time}"
                    layout.addWidget(QLabel(excluded_time_text))
        else:
            layout.addWidget(QLabel("Repeat Rules: None"))
        
        layout.addWidget(QLabel(f"Schedule: {schedule_name}"))
        layout.addWidget(QLabel(f"Zone: {zone_id}"))
        layout.addWidget(QLabel(f"Outstation Identifier: {event_outstation}"))

        # 用于更新Timeline
        self.event_name = event_name
        self.schedule_name = schedule_name
        self.event_time = event_time
        
        # Set the dialog layout
        dialog.setLayout(layout)
        dialog.exec_()

    def convert_days(self, days_str):
        day_mapping = {
            "Mo": "Monday", "Tu": "Tuesday", "We": "Wednesday",
            "Th": "Thursday", "Fr": "Friday", "Sa": "Saturday", "Su": "Sunday"
        }
        return ', '.join(day_mapping.get(day.strip(), day.strip()) for day in days_str.split(','))

    def format_time(self, time_str):
        # 解析原始时间格式
        dt = datetime.strptime(time_str, '%Y%m%d%H%M')
        # 转换为新的时间格式
        return dt.strftime('%Y-%m-%d %H:%M')
    
    def edit_event(self, event_name, event_time, setpoint_value, setpoint_type, repeat_rules, schedule_name, zone_id, event_outstation, event_colour, dialog):
        # 关闭当前的信息对话框
        dialog.close()
        # 打开编辑事件的对话框
        edit_dialog = EventEditDialog(self.parent, event_name, event_time, setpoint_value, setpoint_type, repeat_rules, schedule_name, zone_id, event_outstation, event_colour, refresh_func=self.refresh_events_from_parent)
        if edit_dialog.exec_():
            dialog.accept()  # 关闭对话框

    def delete_event(self, event_name, schedule_name, zone_id, dialog):
        # 弹出确认删除的对话框
        response = QMessageBox.question(self.parent, 'Confirm Deletion', f'Are you sure you want to delete the event "{event_name}"?', QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            # 用户确认删除
            if self.event_deleter.delete_event(schedule_name, zone_id, event_name):
                dialog.accept()  # 关闭对话框
            else:
                QMessageBox.critical(self.parent, 'Deletion Failed', f'Failed to delete the event "{event_name}".')

    def refresh_events_from_parent(self, date_in):
        if self.parent:
            schedule_path = f"Schedules\\{self.schedule_name}.xml"

            if date_in is None:
                date = self.event_time
                # 从 datetime 对象中提取年、月、日
                year = date.year
                month = date.month
                day = date.day

            else:
                year = int(date_in[0:4])
                month = int(date_in[4:6])
                day = int(date_in[6:8])

            # 使用提取的年、月、日创建一个 QDate 对象
            qdate_object = QDate(year, month, day)

            self.parent.updateEventsTimeline(schedule_path, qdate_object)  # 调用主界面的刷新方法