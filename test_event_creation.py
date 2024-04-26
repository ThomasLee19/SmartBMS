from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
from PySide6.QtWidgets import QVBoxLayout, QComboBox, QMessageBox, QHBoxLayout
from PySide6.QtWidgets import QDateTimeEdit, QPushButton, QColorDialog
from PySide6.QtCore import QDate, QDateTime, Signal
from PySide6.QtGui import QColor
import xml.etree.ElementTree as ET
import os
import glob

from test_repeat import RepeatRulesDialog

class EventDialog(QDialog):

    event_created = Signal(QDate) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Create New Event')
        self.repeat_rules = []

        self.event_name_input = QLineEdit(self)

        # 创建日期和时间选择器
        self.date_time_edit = QDateTimeEdit(QDateTime.currentDateTime(), self)

        # 输入Setpoint Value并选择Setpoint Type
        self.setpoint_input = QLineEdit(self)  
        self.setpoint_selector = QComboBox(self)

        self.schedule_selector = QComboBox(self) # 下拉列表选择日程
        self.zone_selector = QComboBox(self)  # 下拉列表选择区域
        self.outstation_identifier_input = QLineEdit(self) 

        # 创建Repeat行的按钮
        self.repeat_button = QPushButton("Repeat Rules", self)
        self.repeat_button.clicked.connect(self.open_repeat_rules_dialog)

        # 颜色按钮初始设置
        self.selected_color = QColor('white')  # 默认颜色为白色
        self.selected_color_rgb = (255, 255, 255)
        self.color_button = QPushButton('Colour Picker', self)
        self.color_button.clicked.connect(self.chooseColor)

        self.setupUI()
        self.populate_setpoint_type_selector()
        self.populate_schedule_selector()  # 填充下拉列表
        # 连接日程选择器的信号以填充区域选择器
        self.schedule_selector.currentIndexChanged.connect(self.populate_zone_selector)

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
        
        self.schedule_selector.setCurrentIndex(0)

    def populate_zone_selector(self):
        self.zone_selector.clear()  # 清除之前的选项
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
    
        if not self.createEventXML(event_name, date_time, setpoint_value, setpoint_type, repeat_rules, selected_schedule, zone_name, outstation_identifier, colour):
            return  # 如果 createEventXML 返回 False，则不关闭对话框

        # 如果一切顺利，则可以接受对话框并关闭
        new_event_date = self.get_new_event_date()
        self.event_created.emit(new_event_date)
        self.accept()

    def get_new_event_date(self):
        # 返回用户在日期时间选择器中选择的事件开始日期
        return self.date_time_edit.date()
    
    def check_numeric(self, input_value):
        try:
            float(input_value)
            return True
        except ValueError:
            return False

    def createEventXML(self, event_name, date_time, setpoint_value, setpoint_type, repeat_rules, schedule_name, zone_name, outstation_identifier, colour):
        schedules_dir = 'Schedules'
        filename = os.path.join(schedules_dir, f'{schedule_name}.xml')
    
        if os.path.exists(filename):
            tree = ET.parse(filename)
            root = tree.getroot()
            building = root.find('.//building')
            if building is not None:
                # 检查outstation-identifier是否在其他区域已被使用
                for zn in building.findall('.//zone'):
                    existing_outstation_event = zn.find(f".//event[@outstation='{outstation_identifier}']")
                    if existing_outstation_event is not None and zn.get('ID') != zone_name:
                        found_zone_name = zn.get('ID')
                        QMessageBox.critical(self, "Error", f"Outstation Identifier '{outstation_identifier}' is already used in {found_zone_name}.")
                        return False
            
                # 直接获取选择的zone元素，不需要检查是否存在，因为用户是从已有区域中选择的
                zone = building.find(f".//zone[@ID='{zone_name}']")
            
                # 检查当前区域内是否已有相同名称的event
                existing_event = zone.find(f".//event[@ID='{event_name}']")
                if existing_event is not None:
                    QMessageBox.critical(self, "Error", f"{event_name} already exists in {zone_name}.")
                    return False

                # 创建新的event元素
                event = ET.SubElement(zone, 'event', ID=event_name, outstation=outstation_identifier, colour=colour)
                event_time = ET.SubElement(event, 'eventTime')
                event_time.text = f' "{date_time}" '
                setpoint = ET.SubElement(event, 'setpoint', value=setpoint_value, type=setpoint_type)

                # 处理重复规则
                for rule in self.repeat_rules:
                    rrule = ET.SubElement(event, 'rrule')
                    # 添加repeat元素，包含specifier和type属性
                    repeat_element = ET.SubElement(rrule, 'repeat', specifier=rule[1], type=str(rule[0]))
                    for excluded_time in rule[2:]:  # 第三位及以后是 excludedTime
                        # 添加excludedTime，文本两边添加一个空格
                        ET.SubElement(rrule, 'excDay').text = f' "{excluded_time}" '

                tree.write(filename, encoding='utf-8', xml_declaration=True)
                return True  # 创建成功
            else:
                QMessageBox.critical(self, "Error", "No building element found in the schedule.")
                return False
        else:
            QMessageBox.critical(self, "Error", "Schedule file does not exist.")
            return False
