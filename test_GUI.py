import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QDialog
from PySide6.QtWidgets import QCalendarWidget, QListWidget, QPushButton, QLabel
from PySide6.QtWidgets import QListWidgetItem, QTableWidget, QTableWidgetItem, QMessageBox
from PySide6.QtCore import Qt, QDate, QDateTime
from PySide6.QtGui import QColor
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import os
import glob
from test_event import EventDialog
from test_schedule_system import CreateScheduleDialog
from test_zone import ListItemWidget

class WeeklyScheduleView(QWidget):  
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        # 创建一个表格，行数为24，代表24小时，列数为7，代表一周七天
        self.tableWidget = QTableWidget(24, 7)  # 24小时，7天

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
            self.tableWidget.setColumnWidth(i, 151)
            self.tableWidget.setRowHeight(i, 40)
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

    def loadEventsFromXML(self, week_start_date):
        # 清除之前的事件再加载新的事件
        self.clearEvents()
        schedules_dir = 'Schedules'
        schedule_files = glob.glob(os.path.join(schedules_dir, '*.xml'))
        for filepath in schedule_files:
            tree = ET.parse(filepath)
            root = tree.getroot()
            for event in root.findall('.//event'):
                event_name = event.get('ID')
                event_time = event.find('eventTime')
                start_date_time_str = event_time.get('start')
                end_date_time_str = event_time.get('end')
                
                # 将字符串格式的日期时间转换为datetime对象
                start_date_time = self.parse_datetime_from_string(start_date_time_str)
                end_date_time = self.parse_datetime_from_string(end_date_time_str)
                                
                # 只加载在当前周显示的事件
                if self.isDateInCurrentWeek(start_date_time.date(), week_start_date):
                    # 计算事件在网格中的位置
                    start_index = self.calculatePositionInGrid(start_date_time, week_start_date)
                    end_index = self.calculatePositionInGrid(end_date_time, week_start_date)
                    
                    if start_index is not None and end_index is not None:
                        # 检查事件的确切日期是否与表格中的日期匹配
                        event_day = start_date_time.date().weekday()
                        event_date = week_start_date.addDays(event_day)
                        if start_date_time.date() == event_date:
                            # 如果事件的日期与表格中的日期相匹配，则添加到表格中
                            for hour in range(start_index[0], end_index[0] + 1):
                                item = self.tableWidget.item(hour, event_day)
                                if item is None:
                                    item = QTableWidgetItem()
                                    self.tableWidget.setItem(hour, event_day, item)
                                item.setText(event_name)
                                item.setBackground(QColor('blue'))  # 设置背景颜色为蓝色

    def calculatePositionInGrid(self, date_time, week_start_date):

        # 首先将QDate转换为datetime.date对象
        week_start_date_py = datetime(week_start_date.year(), week_start_date.month(), week_start_date.day()).date()
        
        # 计算从周开始日期到事件日期的天数差
        day_offset = (date_time.date() - week_start_date_py).days
        # 计算事件的小时
        hour = date_time.hour  # 正确获取小时数
        # 计算星期几（列的位置），星期一是0，星期二是1，依此类推
        day_of_week = date_time.weekday()
        
        return (hour, day_of_week)

    def isDateInCurrentWeek(self, date, week_start_date):
        # Check if the date is in the week starting on week_start_date
        week_end_date = week_start_date.addDays(6)
        return week_start_date <= date <= week_end_date

    def clearEvents(self):
        # Clear all the events from the table before loading new ones
        for i in range(24):  # For each hour
            for j in range(7):  # For each day of the week
                self.tableWidget.setItem(i, j, QTableWidgetItem(''))

    def parse_datetime_from_string(self, date_time_str):
        return datetime.strptime(date_time_str, '%Y%m%d%H%M')
    
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
        hbox.addWidget(self.timeline_view, 3)
        
        # 设置中心窗口的布局
        central_widget = QWidget()
        central_widget.setLayout(hbox)
        self.setCentralWidget(central_widget)

    def refreshEvents(self, date):
        # 计算所选日期所在周的周一日期
        week_start_date = date.addDays(-date.dayOfWeek() + 1)
        self.timeline_view.loadEventsFromXML(week_start_date)

    def on_new_event_button_clicked(self):
        # 检查是否存在日程
        schedules_dir = 'Schedules'
        if not glob.glob(os.path.join(schedules_dir, '*.xml')):
            QMessageBox.warning(self, "Warning", "You haven't created a schedule yet. \nPlease create a schedule before adding events.")
        else:
            dialog = EventDialog(self)
            # 当事件被创建时，连接event_created信号到refreshEvents函数
            dialog.event_created.connect(self.on_event_created)
            if dialog.exec() == QDialog.Accepted:
                # 如果用户成功创建了一个事件，刷新事件显示
                pass
    
    def on_event_created(self, event_date):
        self.timeline_view.setWeekFromDate(event_date)
        self.refreshEvents(event_date)

    def updateTimeline(self, date):
        # 当日历中的日期被点击时，更新时间线视图
        self.timeline_view.clearEvents()
        self.timeline_view.setWeekFromDate(date)
        self.refreshEvents(date)  # 传递所选日期

    def on_new_schedule_button_clicked(self):
        dialog = CreateScheduleDialog(self)
        dialog.schedule_created.connect(self.loadSchedules)  # 连接信号到槽
        if dialog.exec() == QDialog.Accepted and dialog.operation_successful:
            pass

    def getBuildingNameFromSchedule(self, schedule_file):
        tree = ET.parse(schedule_file)
        root = tree.getroot()
        building_element = root.find('.//building')
        if building_element is not None:
            return building_element.get('ID', '')  # 返回Building ID属性
        return ''
    
    def loadSchedules(self):

        self.schedule_list.clear()

        # 设置存储日程的文件夹
        schedules_dir = 'Schedules'
        
        # 检查"Schedules"文件夹是否存在，如果不存在则创建
        if not os.path.isdir(schedules_dir):
            os.makedirs(schedules_dir)
        
        # 读取"Schedules"文件夹中的所有XML文件
        schedule_files = glob.glob(os.path.join(schedules_dir, '*.xml'))
        for filepath in schedule_files:
            schedule_name = os.path.splitext(os.path.basename(filepath))[0]
            building_name = self.getBuildingNameFromSchedule(filepath)  # 获取Building名称
            display_name = f"{schedule_name} - {building_name}" 
            item_widget = ListItemWidget(display_name, filepath)
            item_widget.removed.connect(self.remove_schedule)  # 连接信号到槽函数
            item = QListWidgetItem(self.schedule_list)
            item.setSizeHint(item_widget.sizeHint())
            self.schedule_list.addItem(item)
            self.schedule_list.setItemWidget(item, item_widget)
        
        # 加载事件到时间线
        current_date = QDate.currentDate()  # 获取当前日期
        self.refreshEvents(current_date)  # 使用当前日期刷新事件
    
    def remove_schedule(self, schedule_name):
        # 找到并删除列表项和文件
        items = self.schedule_list.findItems(schedule_name, Qt.MatchExactly)
        if items:
            for item in items:
                row = self.schedule_list.row(item)
                self.schedule_list.takeItem(row)
        self.loadSchedules() 

def main():
    app = QApplication(sys.argv)

    # 设置应用程序的风格
    app.setStyle("windowsvista")

    ex = CalendarView()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
