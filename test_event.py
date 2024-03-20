from PyQt5.QtWidgets import QApplication, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QVBoxLayout, QComboBox, QMessageBox
import xml.etree.ElementTree as ET
import os
import glob

class EventDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Event')
        self.event_name_input = QLineEdit(self)
        self.schedule_selector = QComboBox(self)  # 下拉列表选择日程
        self.setupUI()
        self.populate_schedule_selector()  # 填充下拉列表

    def setupUI(self):
        layout = QVBoxLayout(self)

        # 创建表单布局以收集事件信息
        form_layout = QFormLayout()
        form_layout.addRow('Event Name:', self.event_name_input)
        form_layout.addRow('Schedule:', self.schedule_selector)  # 添加下拉列表到表单
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
        if not event_name:  # 如果事件名称为空
            QMessageBox.critical(self, "Error", "Event name cannot be empty.")  # 显示错误消息
            return  # 退出方法，不继续执行后面的保存操作

        selected_schedule = self.schedule_selector.currentText()  # 获取选定的日程
        self.createEventXML(event_name, selected_schedule)
        self.accept()

    def createEventXML(self, event_name, schedule_name):
        schedules_dir = 'Schedules'
        filename = os.path.join(schedules_dir, f'{schedule_name}.xml')
        
        if os.path.exists(filename):
            tree = ET.parse(filename)
            root = tree.getroot()
        else:
            # 如果文件不存在（理论上不应该发生），创建新的根元素
            root = ET.Element('schedule', name=schedule_name)

        # 创建并添加事件元素
        event = ET.Element('event', ID=event_name)
        ET.SubElement(event, 'eventTime')
        setpoint = ET.SubElement(event, 'setpoint', value="", type="")
        rrule = ET.SubElement(event, 'rrule')
        ET.SubElement(rrule, 'repeat')
        ET.SubElement(rrule, 'excDay')
        
        root.append(event)
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)


