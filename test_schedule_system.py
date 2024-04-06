from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
from PySide6.QtWidgets import QMessageBox, QHBoxLayout, QPushButton, QWidget
from PySide6.QtCore import Signal
import xml.etree.ElementTree as ET
import glob
import os

class CreateScheduleDialog(QDialog):

    schedule_created = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.operation_successful = False
        self.setWindowTitle('Create New Schedule')
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)

        # 添加日程命名的标签和输入框
        layout.addWidget(QLabel('Schedule Name:'))
        self.name_input = QLineEdit(self)
        layout.addWidget(self.name_input)

        # 添加Building ID的标签和输入框
        layout.addWidget(QLabel('Building ID:'))
        self.building_id_input = QLineEdit(self)
        layout.addWidget(self.building_id_input)

        # 创建按钮组
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.on_accepted)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def on_accepted(self):
        # 用户点击"保存"时的操作逻辑
        schedule_name = self.name_input.text().strip()  # 使用 strip() 移除前后空白字符
        building_id = self.building_id_input.text().strip()

        # 检查Schedule Name和Building ID是否为空
        if not schedule_name or not building_id:  # 检查名称是否为空
            QMessageBox.critical(self, "Error", "Schedule name and Building ID cannot be empty.")  # 显示错误消息
            return  # 返回，不继续执行保存逻辑
        
        # 检查Building ID是否唯一
        duplicate_check = self.is_building_id_duplicate(building_id)
        if duplicate_check:
            # 如果Building ID不唯一，显示警告框
            duplicate_schedule_name = duplicate_check[1]  # 从返回值中获取schedule名称
            QMessageBox.critical(self, "Error", f"{building_id} already exists in {duplicate_schedule_name}.")
            return

        # 确保"Schedules"文件夹存在
        schedules_dir = 'Schedules'
        if not os.path.isdir(schedules_dir):
            os.makedirs(schedules_dir)

        # 检查"Schedules"文件夹中文件是否存在
        filename = os.path.join(schedules_dir, f'{schedule_name}.xml')
        if os.path.exists(filename):
            self.confirm_replacement(filename, building_id)  # 现在传递building_id参数
        else:
            self.createScheduleXML(schedule_name, building_id)
            self.operation_successful = True  # 设置操作成功标志
            self.schedule_created.emit()  # 日程创建成功，发射信号
            self.accept()
        
    def confirm_replacement(self, filename, building_id):
        schedule_name = os.path.basename(filename)  # 获取不带路径的文件名
        base_name = os.path.splitext(schedule_name)[0]  # 去除文件扩展名
        reply = QMessageBox.warning(self, 'Confirm Replacement', 
                                    f'"{base_name}" already exists.\nDo you want to replace it?', 
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.createScheduleXML(base_name, building_id)
            self.operation_successful = True
            self.schedule_created.emit()  # 用户确认替换，操作成功
            self.accept()
        else:
             self.operation_successful = False  # 用户选择不替换时，设置操作未成功

    def is_building_id_duplicate(self, building_id):
        # 检查Building ID是否在现有的XML文件中已存在
        schedules_dir = 'Schedules'
        schedule_files = glob.glob(os.path.join(schedules_dir, '*.xml'))
        for filepath in schedule_files:
            tree = ET.parse(filepath)
            root = tree.getroot()
            if root.findall(f".//building[@ID='{building_id}']"):
                schedule_name = root.attrib.get('name')  # 获取该schedule的name属性
                return (True, schedule_name)  # 返回True和schedule名称
        return None  # 如果没有找到重复，返回None

    def createScheduleXML(self, schedule_name, building_id):
        # 确保"Schedules"文件夹存在
        schedules_dir = 'Schedules'
        if not os.path.isdir(schedules_dir):
            os.makedirs(schedules_dir)
        
        # 定义文件的完整路径
        filename = os.path.join(schedules_dir, f'{schedule_name}.xml')

        # 创建XML元素
        schedule = ET.Element('schedule', name=schedule_name)

        #创建building_id元素
        building_element = ET.SubElement(schedule, 'building', ID=building_id)

        # 创建XML树并写入文件
        tree = ET.ElementTree(schedule)
        tree.write(filename, encoding='utf-8', xml_declaration=True)

class ListItemWidget(QWidget):
    removed = Signal(str)  # 用于发出信号，传递被删除的日程名称

    def __init__(self, text, schedule_file, parent=None):
        super().__init__(parent)
        self.schedule_file = schedule_file
        self.layout = QHBoxLayout(self)
        self.label = QLabel(text)
        self.remove_button = QPushButton('x')
        self.remove_button.clicked.connect(self.on_remove_button_clicked)

        # 设置x按钮的固定大小
        self.remove_button.setFixedSize(20, 20)

        self.remove_button.hide()  # 默认隐藏删除按钮

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.remove_button)
        self.setLayout(self.layout)

    def enterEvent(self, event):
        self.remove_button.show()  # 鼠标进入时显示删除按钮
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.remove_button.hide()  # 鼠标离开时隐藏删除按钮
        super().leaveEvent(event)

    def on_remove_button_clicked(self):
        # 弹出确认删除的对话框
        response = QMessageBox.question(self, 'Remove Schedule', f'Are you sure you want to remove "{self.label.text()}"?', QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            try:
                os.remove(self.schedule_file)  # 删除文件
                self.removed.emit(self.label.text())  # 发出信号，传递日程名称
            except Exception as e:
                QMessageBox.critical(self, 'Remove Failed', str(e))
    