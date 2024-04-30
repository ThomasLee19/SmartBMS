from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
from PySide6.QtWidgets import QMessageBox, QHBoxLayout, QPushButton, QWidget
from PySide6.QtCore import Signal, Qt
import xml.etree.ElementTree as ET
import os

class ListItemWidget(QWidget):
    removed = Signal(str)  # 用于发出信号，传递被删除的日程名称
    add_zone = Signal(str)  # 发出信号，传递要添加Zone的Schedule文件路径

    def __init__(self, text, schedule_file, parent=None):
        super().__init__(parent)
        self.schedule_file = schedule_file
        self.layout = QHBoxLayout(self)
        self.label = QLabel(text)
        self.add_zone_button = QPushButton('+')
        self.remove_button = QPushButton('x')

        # 设置按钮的固定大小
        self.remove_button.setFixedSize(20, 20)
        self.add_zone_button.setFixedSize(20, 20)

        self.remove_button.clicked.connect(self.on_remove_button_clicked)
        self.add_zone_button.clicked.connect(self.on_add_zone_button_clicked)

        self.remove_button.hide()  # 默认隐藏删除按钮
        self.add_zone_button.hide()  # 默认隐藏添加Zone按钮

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.add_zone_button)
        self.layout.addWidget(self.remove_button)
        self.setLayout(self.layout)

    def enterEvent(self, event):
        self.remove_button.show()  # 鼠标进入时显示删除按钮
        self.add_zone_button.show()  # 鼠标进入时显示添加Zone按钮
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.remove_button.hide()  # 鼠标离开时隐藏删除按钮
        self.add_zone_button.hide()  # 鼠标离开时隐藏添加Zone按钮
        super().leaveEvent(event)

    def on_add_zone_button_clicked(self):
        dialog = CreateZoneDialog(self.schedule_file, self.parent())
        dialog.exec_() # 发出信号，传递Schedule文件路径

    def on_remove_button_clicked(self):
        # 弹出确认删除的对话框
        response = QMessageBox.question(self, 'Remove Schedule', f'Are you sure you want to remove "{self.label.text()}"?', QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            try:
                os.remove(self.schedule_file)  # 删除文件
                self.removed.emit(self.label.text())  # 发出信号，传递日程名称
            except Exception as e:
                QMessageBox.critical(self, 'Remove Failed', str(e))

    def mousePressEvent(self, event):
            if event.button() == Qt.RightButton:
                self.showScheduleDetails()
            super().mousePressEvent(event)
  
    def showScheduleDetails(self):
        try:
            tree = ET.parse(self.schedule_file)
            root = tree.getroot()
            building = root.find('.//building')
            if building is None:
                QMessageBox.critical(self, "Error", "No building element found in the schedule.")
                return  # 如果没有找到 building 元素，直接返回，不打开对话框
            zones = building.findall('.//zone')
            if not zones:  # 检查是否存在 zone 元素
                QMessageBox.critical(self, "Error", "No zones found in the building.")
                return  # 如果没有找到 zone 元素，直接返回，不打开对话框
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return  # 如果解析文件时出现异常，直接返回，不打开对话框

        dialog = ScheduleDetailsDialog(self.schedule_file, self.parent())
        dialog.exec_()
    
class CreateZoneDialog(QDialog):
    def __init__(self, schedule_file, parent=None):
        super().__init__(parent)
        self.schedule_file = schedule_file
        self.setWindowTitle('Create New Zone')
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)

        # 添加Zone命名的标签和输入框
        layout.addWidget(QLabel('Zone Name:'))
        self.zone_name_input = QLineEdit(self)
        layout.addWidget(self.zone_name_input)

        # 添加Zone描述的标签和输入框
        layout.addWidget(QLabel('Zone Description:'))
        self.zone_description_input = QLineEdit(self)
        layout.addWidget(self.zone_description_input)

        # 创建按钮组
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.on_accepted)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def on_accepted(self):
        zone_name = self.zone_name_input.text().strip()
        zone_description = self.zone_description_input.text().strip()

        if not zone_name:
            QMessageBox.critical(self, "Error", "Zone name cannot be empty.")
            return

        # 调用函数将Zone信息保存到XML
        self.saveZoneToXML(zone_name, zone_description)

    def saveZoneToXML(self, zone_name, zone_description):
        if not os.path.exists(self.schedule_file):
            QMessageBox.critical(self, "Error", "Schedule file does not exist.")
            return

        tree = ET.parse(self.schedule_file)
        root = tree.getroot()
        building = root.find('.//building')

        if building is None:
            QMessageBox.critical(self, "Error", "No building element found in the schedule.")
            return

        # 检查当前building下是否已有相同名称的zone
        existing_zone = building.find(f".//zone[@ID='{zone_name}']")
        if existing_zone is not None:
            QMessageBox.critical(self, "Error", f"Zone '{zone_name}' already exists.")
            return

        # 如果没有找到同名的Zone，则创建新的Zone
        new_zone = ET.SubElement(building, 'zone', ID=zone_name)
        new_zone.set('description', zone_description)

        tree.write(self.schedule_file, encoding='utf-8', xml_declaration=True)
        self.accept()

class ScheduleDetailsDialog(QDialog):
    def __init__(self, schedule_file, parent=None):
        super().__init__(parent)
        self.schedule_file = schedule_file
        self.setWindowTitle('Schedule Details')
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        self.zone_list = QVBoxLayout()  # 用于展示Zone信息的布局
        layout.addLayout(self.zone_list)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close, self)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        self.loadZones()

    def loadZones(self):
        try:
            tree = ET.parse(self.schedule_file)
            root = tree.getroot()
            building = root.find('.//building')
            if building:
                for zone in building.findall('.//zone'):
                    zone_id = zone.get('ID')
                    zone_desc = zone.get('description', 'No description provided')
                    label = QLabel(f'Zone Name: {zone_id}\nZone Description: {zone_desc}')
                    self.zone_list.addWidget(label)
            else:
                QMessageBox.critical(self, "Error", "No building element found in the schedule.")
                self.reject()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.reject()
