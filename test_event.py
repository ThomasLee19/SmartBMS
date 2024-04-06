from PySide6.QtWidgets import QApplication, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QVBoxLayout, QComboBox, QMessageBox
import xml.etree.ElementTree as ET
import os
import glob

class EventDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Create New Event')
        self.event_name_input = QLineEdit(self)
        self.schedule_selector = QComboBox(self) # 下拉列表选择日程
        self.zone_name_input = QLineEdit(self)
        self.zone_description_input = QLineEdit(self)  
        self.setupUI()
        self.populate_schedule_selector()  # 填充下拉列表

    def setupUI(self):
        layout = QVBoxLayout(self)

        # 创建表单布局以收集事件信息
        form_layout = QFormLayout()
        form_layout.addRow('Event Name:', self.event_name_input)
        form_layout.addRow('Schedule:', self.schedule_selector)  # 添加下拉列表到表单
        form_layout.addRow('Zone Name:', self.zone_name_input)
        form_layout.addRow('Zone Description:', self.zone_description_input)
        layout.addLayout(form_layout)

        # 创建按钮组
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.saveEvent)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def populate_schedule_selector(self):
        schedules_dir = 'Schedules'
        schedule_files = glob.glob(os.path.join(schedules_dir, '*.xml'))
        for filepath in schedule_files:
            schedule_name = os.path.splitext(os.path.basename(filepath))[0]
            self.schedule_selector.addItem(schedule_name)

    def saveEvent(self):
        event_name = self.event_name_input.text().strip()  # 使用 strip() 移除可能的空白字符
        zone_name = self.zone_name_input.text().strip()

        if not event_name:  # 如果事件名称为空
            QMessageBox.critical(self, "Error", "Event name cannot be empty.")  # 显示错误消息
            return  # 退出方法，不继续执行后面的保存操作
    
        if not zone_name:
            QMessageBox.critical(self, "Error", "Zone name cannot be empty.")  # 显示错误消息
            return  # 退出方法，不继续执行后面的保存操作
    
        zone_description = self.zone_description_input.text().strip()
        selected_schedule = self.schedule_selector.currentText()  # 获取选定的日程
    
        if not self.createEventXML(event_name, selected_schedule, zone_name, zone_description):
            return  # 如果 createEventXML 返回 False，则不关闭对话框

        # 如果一切顺利，则可以接受对话框并关闭
        self.accept()

    def createEventXML(self, event_name, schedule_name, zone_name, zone_description):
        schedules_dir = 'Schedules'
        filename = os.path.join(schedules_dir, f'{schedule_name}.xml')
    
        if os.path.exists(filename):
            tree = ET.parse(filename)
            root = tree.getroot()
            building = root.find('.//building')
            if building is not None:
            # 在building元素中寻找与提供的zone_name匹配的zone元素
                zone = None
                for zn in building.findall('.//zone'):
                    if zn.get('ID') == zone_name:
                        zone = zn
                        break

                if zone is None:
                    zone = ET.SubElement(building, 'zone', ID=zone_name, description=zone_description)

                # 检查当前区域内是否已有相同名称的event
                existing_event = zone.find(f".//event[@ID='{event_name}']")
                if existing_event is not None:
                    QMessageBox.critical(self, "Error", f"{event_name} already exists in {zone_name}.")
                    return False

                event = ET.SubElement(zone, 'event', ID=event_name)
                ET.SubElement(event, 'eventTime')
                setpoint = ET.SubElement(event, 'setpoint', value="", type="")
                rrule = ET.SubElement(event, 'rrule')
                ET.SubElement(rrule, 'repeat')
                ET.SubElement(rrule, 'excDay')

                tree = ET.ElementTree(root)
                tree.write(filename, encoding='utf-8', xml_declaration=True)
                return True  # 创建成功
            else:
                QMessageBox.critical(self, "Error", "No building element found in the schedule.")
                return False # 创建失败
        else:
            QMessageBox.critical(self, "Error", "Schedule file does not exist.")
            return False


