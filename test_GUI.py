import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QDialog
from PySide6.QtWidgets import QCalendarWidget, QListWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QMessageBox
from PySide6.QtCore import Qt, QDate
from datetime import datetime, timedelta
import os
import glob
from test_event import EventDialog
from test_schedule_system import CreateScheduleDialog

class WeeklyScheduleView(QWidget):  
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        # 创建一个表格，行数为24，代表24小时，列数为7，代表一周七天
        self.tableWidget = QTableWidget(24, 7)  # 24小时，7天
        self.tableWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 设置表头为一周的每一天和日期
        self.updateTableHeaders()

        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.tableWidget)

        # 设置时间线视图的布局
        self.setLayout(layout)  

        # 填充表格数据
        self.populateSchedule()

    def setWeekFromDate(self, date):
        # 清空当前的表头
        self.tableWidget.clear()
        # 重新设置表头
        self.updateTableHeaders(date)
        # 填充表格数据
        self.populateSchedule()

    def updateTableHeaders(self, base_date=None):
        # 如果没有提供基准日期，则使用当前日期
        if not base_date:
            base_date = QDate.currentDate()
        # 确保传入的是一个QDate对象
        if isinstance(base_date, datetime):
            base_date = QDate(base_date.year, base_date.month, base_date.day)
        
        # 获取基准日期所在周的星期一
        start_of_week = base_date.addDays(-base_date.dayOfWeek() + 1)
        
        # 设置水平头标签
        for i in range(7):
            day_date = start_of_week.addDays(i)
            header_label = f'{day_date.toString("ddd")}\n{day_date.toString("dd/MM")}'
            self.tableWidget.setHorizontalHeaderItem(i, QTableWidgetItem(header_label))
            
        # 设置垂直头标签为每个小时
        for i in range(24):
            self.tableWidget.setVerticalHeaderItem(i, QTableWidgetItem(f'{i:02d}:00'))

    def populateSchedule(self):
        # 填充表格的函数，这里只是一个示例
        for i in range(24):  # 对于每一个小时
            for j in range(7):  # 对于每一天
                # 创建一个表格项
                item = QTableWidgetItem('')
                # 将表格项添加到表格中
                self.tableWidget.setItem(i, j, item)

    # 以下函数可以添加到处理点击事件和编辑事件的逻辑

class CalendarView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 1100, 650)
        self.setWindowTitle('Building Management System')

        # 创建水平布局
        hbox = QHBoxLayout()

        # 创建左侧的垂直布局
        left_vbox = QVBoxLayout()

        # 创建新事件的按钮
        new_event_button = QPushButton('+')
        new_event_button.clicked.connect(self.on_new_event_button_clicked)
        left_vbox.addWidget(new_event_button)

        # 创建并添加月历视图
        calendar_widget = QCalendarWidget()
        calendar_widget.setGridVisible(True)
        calendar_widget.clicked[QDate].connect(self.updateTimeline)
        left_vbox.addWidget(calendar_widget)

        # 创建"My Schedule"标签和按钮的水平布局
        my_schedule_layout = QHBoxLayout()
        
        # 添加"My Schedule"标签
        my_schedule_label = QLabel('My Schedule')
        my_schedule_layout.addWidget(my_schedule_label)

        # 创建创建日程的按钮
        new_schedule_button = QPushButton('+')
        new_schedule_button.clicked.connect(self.on_new_schedule_button_clicked)  # 绑定事件处理器
        my_schedule_layout.addWidget(new_schedule_button)

        # 将“My Schedule”布局添加到左侧布局
        left_vbox.addLayout(my_schedule_layout)

        # 创建“My Schedule”列表
        self.schedule_list = QListWidget()
        self.schedule_list.setStyleSheet("QListWidget {border: 1px solid black;}")
        left_vbox.addWidget(self.schedule_list)

        # 创建中间的时间线视图并将其赋值给self.timeline_view
        self.timeline_view = WeeklyScheduleView(self)
        self.timeline_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 加载现有的日程到"My Schedule"列表
        self.loadSchedules()

        # 将左侧和中间的布局添加到水平布局
        hbox.addLayout(left_vbox, 1)
        hbox.addWidget(self.timeline_view, 4)
        
        # 设置中心窗口的布局
        central_widget = QWidget()
        central_widget.setLayout(hbox)
        self.setCentralWidget(central_widget)

    def updateTimeline(self, date):
        # 当日历中的日期被点击时，更新时间线视图
        self.timeline_view.setWeekFromDate(date)

    def on_new_event_button_clicked(self):
        # 检查是否存在日程
        schedules_dir = 'Schedules'
        if not glob.glob(os.path.join(schedules_dir, '*.xml')):
            QMessageBox.warning(self, "Warning", "You haven't created a schedule yet. \nPlease create a schedule before adding events.")
        else:
            dialog = EventDialog(self)
            if dialog.exec() == QDialog.Accepted:
                # 这里可以添加代码处理对话框的返回结果
                pass

    def on_new_schedule_button_clicked(self):
        dialog = CreateScheduleDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.operation_successful:
            schedule_name = dialog.name_input.text()

            # 检查该名称是否已经存在于列表中
            is_existing = False
            for i in range(self.schedule_list.count()):
                if self.schedule_list.item(i).text() == schedule_name:
                    is_existing = True
                    break

            # 如果名称不存在于列表中，才添加新项
            if not is_existing:
                self.schedule_list.addItem(schedule_name)
    
    def loadSchedules(self):
        # 设置存储日程的文件夹
        schedules_dir = 'Schedules'
        
        # 检查"Schedules"文件夹是否存在，如果不存在则创建
        if not os.path.isdir(schedules_dir):
            os.makedirs(schedules_dir)
        
        # 读取"Schedules"文件夹中的所有XML文件
        schedule_files = glob.glob(os.path.join(schedules_dir, '*.xml'))
        for filepath in schedule_files:
            schedule_name = os.path.splitext(os.path.basename(filepath))[0]
            self.schedule_list.addItem(schedule_name)

def main():
    app = QApplication(sys.argv)

    # 设置应用程序的风格
    app.setStyle("windowsvista")

    ex = CalendarView()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
