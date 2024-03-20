from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox
from PySide6.QtCore import QTimer
import xml.etree.ElementTree as ET
import os

class CreateScheduleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.operation_successful = False
        self.setWindowTitle('Create New Schedule')
        self.setupUI()
        self.resize(326, 155)

    def setupUI(self):
        layout = QVBoxLayout(self)

        # 添加日程命名的标签和输入框
        layout.addWidget(QLabel('Schedule Name:'))
        self.name_input = QLineEdit(self)
        layout.addWidget(self.name_input)

        # 创建按钮组
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.on_accepted)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def on_accepted(self):
        # 用户点击"保存"时的操作逻辑
        schedule_name = self.name_input.text().strip()  # 使用 strip() 移除前后空白字符
        if not schedule_name:  # 检查名称是否为空
            QMessageBox.critical(self, "Error", "Schedule name cannot be empty.")  # 显示错误消息
            return  # 返回，不继续执行保存逻辑
        
        if schedule_name:
            # 确保"Schedules"文件夹存在
            schedules_dir = 'Schedules'
            if not os.path.isdir(schedules_dir):
                os.makedirs(schedules_dir)

            # 检查"Schedules"文件夹中文件是否存在
            filename = os.path.join(schedules_dir, f'{schedule_name}.xml')
            if os.path.exists(filename):
                self.confirm_replacement(filename)
            else:
                self.createScheduleXML(schedule_name)
                self.operation_successful = True  # 设置操作成功标志
                self.accept()

    def confirm_replacement(self, filename):
        schedule_name = os.path.basename(filename)  # 获取不带路径的文件名
        base_name = os.path.splitext(schedule_name)[0]  # 去除文件扩展名
        reply = QMessageBox.warning(self, 'Confirm Replacement', 
                                    f'"{base_name}" already exists.\nDo you want to replace it?', 
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.createScheduleXML(os.path.splitext(os.path.basename(filename))[0])
            self.operation_successful = True  # 用户确认替换，操作成功
            self.accept()
        else:
            self.replaced = False  # 用户选择不替换时，设置标志为False

    def createScheduleXML(self, schedule_name):
        # 确保"Schedules"文件夹存在
        schedules_dir = 'Schedules'
        if not os.path.isdir(schedules_dir):
            os.makedirs(schedules_dir)
        
        # 定义文件的完整路径
        filename = os.path.join(schedules_dir, f'{schedule_name}.xml')

        # 创建XML元素
        schedule = ET.Element('schedule', name=schedule_name)

        # 创建XML树并写入文件
        tree = ET.ElementTree(schedule)
        tree.write(filename, encoding='utf-8', xml_declaration=True)

        # 如果需要更新UI列表或者执行其他操作，可以在这里添加代码