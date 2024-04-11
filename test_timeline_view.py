from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
from PySide6.QtCore import QDate
from PySide6.QtGui import QColor
from datetime import datetime
import xml.etree.ElementTree as ET

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

    def loadEventsFromXML(self, schedule_file_path, week_start_date):
        # 清除之前的事件再加载新的事件
        self.clearEvents()
        tree = ET.parse(schedule_file_path)
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