from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
from PySide6.QtWidgets import QVBoxLayout, QComboBox, QMessageBox, QHBoxLayout
from PySide6.QtWidgets import QDateTimeEdit, QPushButton, QColorDialog
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QColor
import xml.etree.ElementTree as ET
import os
import glob

from test_repeat import RepeatRulesDialog

class EventEditDialog(QDialog):

    def __init__(self, parent=None, event_name=None, event_time=None, setpoint_value=None, setpoint_type=None, repeat_rules=None, schedule_name=None, zone_id=None, event_outstation=None, event_colour=None, schedules_dir='Schedules', refresh_func=None):
        super().__init__(parent)
        self.setWindowTitle('Edit Event')
        self.schedules_dir = schedules_dir
        self.refresh_func = refresh_func
        self.remover = EventDeleter(schedules_dir)
        self.repeat_rules = repeat_rules if repeat_rules else []

        self.event_name_input = QLineEdit(event_name, self)
        self.original_name = event_name
        self.original_zone = zone_id
        self.original_schedule = schedule_name

        # 处理时间字符串
        if event_time:
            date_str = event_time.strftime("%Y-%m-%d %H:%M:%S")
            datetime_obj = QDateTime.fromString(date_str, Qt.ISODate)
        else:
            datetime_obj = QDateTime.currentDateTime()

        self.date_time_edit = QDateTimeEdit(datetime_obj, self)

        # 输入Setpoint Value并选择Setpoint Type
        self.setpoint_input = QLineEdit(setpoint_value, self) 
        self.setpoint_selector = QComboBox(self)

        self.schedule_selector = QComboBox(self) # 下拉列表选择日程
        self.zone_selector = QComboBox(self)  # 下拉列表选择区域
        self.outstation_identifier_input = QLineEdit(event_outstation, self) 

        # 创建Repeat行的按钮
        self.repeat_button = QPushButton("Repeat Rules", self)
        self.repeat_button.clicked.connect(self.open_repeat_rules_dialog)

        # 颜色按钮初始设置
        if event_colour:
            # 解析颜色字符串为元组
            color_tuple = self.parse_color_string(event_colour)
            # 使用解析后的元组初始化 QColor
            self.selected_color = QColor(color_tuple[0], color_tuple[1], color_tuple[2])
        else:
            self.selected_color = QColor('white')  # 默认颜色为白色
        self.selected_color_rgb = color_tuple if event_colour else (255, 255, 255)
        self.color_button = QPushButton('Colour Picker', self)
        self.color_button.setStyleSheet(f"background-color: {self.selected_color.name()}; color: black;")
        self.color_button.clicked.connect(self.chooseColor)

        self.setupUI()
        self.populate_setpoint_type_selector()
        self.populate_schedule_selector()  # 填充下拉列表

        # 设置日程选择器的当前选项
        index = self.schedule_selector.findText(schedule_name)
        if index != -1:
            self.schedule_selector.setCurrentIndex(index)
        else:
            self.schedule_selector.setCurrentIndex(0)

        # 连接日程选择器的信号以填充区域选择器
        self.schedule_selector.currentIndexChanged.connect(self.populate_zone_selector)

        # 确保区域选择器被正确填充
        self.populate_zone_selector()

        # 设置区域选择器的当前选项
        zone_index = self.zone_selector.findText(zone_id)
        if zone_index != -1:
            self.zone_selector.setCurrentIndex(zone_index)
        else:
            self.zone_selector.setCurrentIndex(0)

        self.setpoint_selector.setCurrentText(setpoint_type)

    def setupUI(self):
        layout = QVBoxLayout(self)

        # 创建表单布局以收集事件信息
        form_layout = QFormLayout()
        form_layout.addRow('Name:', self.event_name_input)

        self.date_time_edit.setCalendarPopup(True)
        form_layout.addRow('Date and Time:', self.date_time_edit)

        form_layout.addRow('Setpoint Value:', self.setpoint_input)
        form_layout.addRow('Setpoint Type:', self.setpoint_selector)

        # 布局Repeat选择按钮
        repeat_button_layout = QHBoxLayout()
        repeat_button_layout.addWidget(self.repeat_button)
        form_layout.addRow('Repeat:', repeat_button_layout)

        # 布局事件所属的日程和区域信息
        form_layout.addRow('Schedule:', self.schedule_selector)  # 添加下拉列表到表单
        form_layout.addRow('Zone:', self.zone_selector)
        form_layout.addRow('Outstation Identifier:', self.outstation_identifier_input)

        # 布局颜色选择按钮
        color_button_layout = QHBoxLayout()
        color_button_layout.addWidget(self.color_button)
        form_layout.addRow('Colour:', color_button_layout)

        layout.addLayout(form_layout)

        # 创建按钮组
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.saveEvent)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def open_repeat_rules_dialog(self):
        # 假设 self.repeat_rules 存储了之前设置的规则
        dialog = RepeatRulesDialog(self.repeat_rules, self)
        if dialog.exec_():
            self.repeat_rules = dialog.get_current_rules()  # 更新规则

    def populate_schedule_selector(self):
        self.schedule_selector.clear() 
        self.schedule_selector.addItem("Please select one of the following schedules", None) 

        schedules_dir = 'Schedules'
        schedule_files = glob.glob(os.path.join(schedules_dir, '*.xml'))
        for filepath in schedule_files:
            schedule_name = os.path.splitext(os.path.basename(filepath))[0]
            self.schedule_selector.addItem(schedule_name, filepath)  # 设置userData为文件路径 

    def populate_zone_selector(self):
        self.zone_selector.clear()  
        selected_schedule_path = self.schedule_selector.currentData()  # 获取选中的日程文件路径
        if selected_schedule_path:
            try:
                tree = ET.parse(selected_schedule_path)
                root = tree.getroot()
                building = root.find('.//building')
                if building:
                    for zone in building.findall('.//zone'):
                        zone_id = zone.get('ID')
                        self.zone_selector.addItem(zone_id)  # 添加区域ID到下拉列表
            except ET.ParseError as e:
                QMessageBox.critical(self, "Error", "Failed to parse the schedule file.")

    def populate_setpoint_type_selector(self):
        self.setpoint_selector.clear()
        self.setpoint_selector.addItem("Please select one of the following types", None)
        self.setpoint_selector.addItem("Less Than", "lt")
        self.setpoint_selector.addItem("Equal To", "eq")
        self.setpoint_selector.addItem("Greater Than", "gt")

    def parse_color_string(self, color_string):
        # 去除括号并分割字符串
        color_string = color_string.strip("()")
        # 分割后的字符串转换为整数列表
        color_tuple = tuple(int(num) for num in color_string.split(","))
        return color_tuple

    def chooseColor(self):
        color = QColorDialog.getColor(self.selected_color, self, "Select Color")
        if color.isValid():
            self.selected_color = color
            # 更新按钮的样式
            self.color_button.setStyleSheet(f"background-color: {color.name()}; color: black;")
            # 保存颜色的 RGB 值
            self.selected_color_rgb = (color.red(), color.green(), color.blue())

    def saveEvent(self):
        event_name = self.event_name_input.text().strip()

        # 获取事件时间
        date_str= self.date_time_edit.dateTime().toPython()
        date_time = date_str.strftime('%Y%m%d%H%M')

        # 获取Setpoint Value和Setpoint Type
        setpoint_value = self.setpoint_input.text().strip()
        setpoint_type = self.setpoint_selector.currentData()

        # 获取Repeat Rules列表
        repeat_rules = self.repeat_rules

        # 获取选定的日程和区域
        selected_schedule = self.schedule_selector.currentText()  
        zone_name = self.zone_selector.currentText()
        outstation_identifier = self.outstation_identifier_input.text().strip()

        colour = self.selected_color_rgb 

        if not event_name:  # 如果事件名称为空
            QMessageBox.critical(self, "Error", "Event name cannot be empty.")  # 显示错误消息
            return  # 退出方法，不继续执行后面的保存操作
        
        if not setpoint_value:
            QMessageBox.critical(self, "Error", "Setpoint Value cannot be empty.")
            return
        
        if not self.check_numeric(setpoint_value):
            QMessageBox.critical(self, "Error", "Setpoint Value must be a literal numeric value.")
            return
        
        if not setpoint_type:
            QMessageBox.critical(self, "Error", "Setpoint Type must be selected.")
            return
            
        if not zone_name:
            QMessageBox.critical(self, "Error", "Zone must be selected.")
            return
        
        if not outstation_identifier:
            QMessageBox.critical(self, "Error", "Outstation Identifier cannot be empty.")
            return
        
        if not self.remover.delete_event(self.original_schedule, self.original_zone, self.original_name):
            return
    
        if not self.updateEventXML(event_name, date_time, setpoint_value, setpoint_type, repeat_rules, selected_schedule, zone_name, outstation_identifier, colour):
            return  # 如果 createEventXML 返回 False，则不关闭对话框

        # 如果一切顺利，则可以接受对话框并关闭
        self.accept()
    
    def check_numeric(self, input_value):
        try:
            float(input_value)
            return True
        except ValueError:
            return False

    def updateEventXML(self, event_name, date_time, setpoint_value, setpoint_type, repeat_rules, schedule_name, zone_name, outstation_identifier, colour):
        filename = os.path.join(self.schedules_dir, f'{schedule_name}.xml')
    
        if os.path.exists(filename):
            tree = ET.parse(filename)
            root = tree.getroot()
            building = root.find('.//building')
            if building is not None:
                # 检查outstation-identifier是否在其他区域已被使用
                for zn in building.findall('.//zone'):
                    existing_outstation_event = zn.find(f".//event[@outstation='{outstation_identifier}']")
                    if existing_outstation_event is not None and existing_outstation_event.get('ID') != self.original_name and zn.get('ID') != zone_name:
                        found_zone_name = zn.get('ID')
                        QMessageBox.critical(None, "Error", f"Outstation Identifier '{outstation_identifier}' is already used in {found_zone_name}.")
                        return False

                # 添加新事件
                zone = building.find(f".//zone[@ID='{zone_name}']")
                event = ET.SubElement(zone, 'event', ID=event_name, outstation=outstation_identifier, colour=str(colour))
                ET.SubElement(event, 'eventTime').text = date_time
                ET.SubElement(event, 'setpoint', value=setpoint_value, type=setpoint_type)

                # 处理重复规则
                for rule in repeat_rules:
                    rrule = ET.SubElement(event, 'rrule')
                    ET.SubElement(rrule, 'repeat', specifier=rule[1], type=str(rule[0]))
                    for excluded_time in rule[2:]:
                        ET.SubElement(rrule, 'excDay').text = excluded_time

                tree.write(filename, encoding='utf-8', xml_declaration=True)
                if self.refresh_func:
                    self.refresh_func(date_time) 
                return True
            else:
                QMessageBox.critical(None, "Error", "No building element found in the schedule.")
                return False
        else:
            QMessageBox.critical(None, "Error", f"Schedule file '{schedule_name}.xml' does not exist.")
            return False

class EventDeleter:
    def __init__(self, schedules_dir='Schedules', refresh_func=None):
        self.schedules_dir = schedules_dir
        self.refresh_func = refresh_func

    def delete_event(self, schedule_name, zone_id, event_id):
        filename = os.path.join(self.schedules_dir, f'{schedule_name}.xml')
        if os.path.exists(filename):
            tree = ET.parse(filename)
            root = tree.getroot()
            building = root.find('.//building')
            if building is not None:
                zone = building.find(f".//zone[@ID='{zone_id}']")
                if zone is not None:
                    event = zone.find(f".//event[@ID='{event_id}']")
                    if event is not None:
                        zone.remove(event)
                        tree.write(filename, encoding='utf-8', xml_declaration=True)
                        if self.refresh_func:
                            self.refresh_func(None)  # 调用刷新函数
                        return True
                    else:
                        QMessageBox.critical(None, "Error", f"No event found with ID '{event_id}' in zone '{zone_id}'.")
                        return False
                else:
                    QMessageBox.critical(None, "Error", f"No zone found with ID '{zone_id}'.")
                    return False
            else:
                QMessageBox.critical(None, "Error", "No building element found in the schedule.")
                return False
        else:
            QMessageBox.critical(None, "Error", f"Schedule file '{schedule_name}.xml' does not exist.")
            return False
        