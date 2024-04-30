from PySide6.QtWidgets import QVBoxLayout, QWidget,  QPushButton
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
from PySide6.QtCore import QDate
from datetime import datetime
import xml.etree.ElementTree as ET

from test_event_infor import EventInfor

class WeeklyScheduleView(QWidget):  
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.event_infor = EventInfor(self)

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
        schedule_name = root.get('name')  # Directly use root to get the schedule name

        building = root.find('building')
        if building is not None:

            # 遍历每个 zone
            for zone in building.findall('zone'):
                zone_id = zone.get('ID')
                events_by_cell = {}  # 用于存储每个单元格的事件列表

                for event in zone.findall('event'):
                    event_name = event.get('ID')
                    event_time = event.find('eventTime')
                    event_setpoint = event.find('setpoint')
                    event_outstation = event.get('outstation')
                    event_colour = event.get('colour', '(255, 255, 255)')
                    date_time_str = event_time.text.strip().strip('"')

                    # 将字符串格式的日期时间转换为datetime对象
                    date_time = self.parse_datetime_from_string(date_time_str)

                    # 获取setpoint的value和type属性
                    setpoint_value = event_setpoint.get('value')
                    setpoint_type = self.convert_setpoint_type(event_setpoint.get('type'))

                    # 解析重复规则
                    repeat_rules = []
                    for rrule in event.findall('rrule'):
                        repeat = rrule.find('repeat')
                        repeat_type = repeat.get('type')
                        repeat_specifier = repeat.get('specifier')
                        exc_days = [exc_day.text.strip().strip('"') for exc_day in rrule.findall('excDay')]
                        repeat_rules.append((repeat_type, repeat_specifier, *exc_days))

                    # 只加载在当前周显示的事件
                    if self.isDateInCurrentWeek(date_time.date(), week_start_date):
                        # 计算事件在网格中的位置
                        start_index = self.calculatePositionInGrid(date_time, week_start_date)

                        if start_index is not None:
                            hour, event_day = start_index
                            # 初始化单元格的事件列表
                            if (hour, event_day) not in events_by_cell:
                                events_by_cell[(hour, event_day)] = []
                            
                            # 添加事件到列表
                            events_by_cell[(hour, event_day)].append({
                                'date_time': date_time,
                                'event_name': event_name,
                                'event_colour': event_colour,
                                'setpoint_value': setpoint_value,
                                'setpoint_type': setpoint_type,
                                'event_outstation': event_outstation,
                                'repeat_rules': repeat_rules
                            })

                # 遍历每个单元格，按时间排序事件并创建按钮
                for (hour, event_day), events in events_by_cell.items():
                    # 按时间排序
                    events.sort()
                    widget = self.tableWidget.cellWidget(hour, event_day)
                    if widget is None:
                        widget = QWidget()
                        layout = QVBoxLayout()
                        widget.setLayout(layout)
                        self.tableWidget.setCellWidget(hour, event_day, widget)

                    for event_info in events:
                        # 格式化时间显示为HH:MM
                        time_display = event_info['date_time'].strftime('%H:%M')
                        button_text = f"{event_info['event_name']} {time_display}"
                        button = QPushButton(button_text)

                        # 解析 RGB 字符串并应用颜色
                        rgb_tuple = eval(event_info['event_colour'])  # 将字符串 '(255, 255, 255)' 转换为元组 (255, 255, 255)
                        css_color = f"rgb{rgb_tuple}"  # 转换为 CSS 需要的格式
                        button.setStyleSheet(f"background-color: {css_color}; color: black;")
                        widget.layout().addWidget(button)

                        # 调整行高以适应新的按钮
                        required_height = button.sizeHint().height() * widget.layout().count()
                        current_height = self.tableWidget.rowHeight(hour)
                        if required_height > current_height:
                            self.tableWidget.setRowHeight(hour, required_height)

                        # 连接按钮的点击信号到一个槽函数
                        button.clicked.connect(lambda en=event_info['event_name'], dt=event_info['date_time'], sv=event_info['setpoint_value'], st=event_info['setpoint_type'], rr=event_info['repeat_rules'], sn=schedule_name, zi=zone_id, eo=event_info['event_outstation'], ec=event_info['event_colour']: self.handle_event_click(en, dt, sv, st, rr, sn, zi, eo, ec))

    def calculatePositionInGrid(self, date_time, week_start_date):
        # 首先将QDate转换为datetime.date对象
        week_start_date = datetime(week_start_date.year(), week_start_date.month(), week_start_date.day()).date()

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
        # Clear all the events from the table and reset row heights
        default_row_height = 40
        for i in range(24):  # For each hour
            for j in range(7):  # For each day of the week
                widget = self.tableWidget.cellWidget(i, j)
                if widget:
                    # 清除布局中的所有子部件
                    while widget.layout().count():
                        child = widget.layout().takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
                    # 移除现有的widget
                    self.tableWidget.removeCellWidget(i, j)
                # 设置一个新的空白QTableWidgetItem
                self.tableWidget.setItem(i, j, QTableWidgetItem(''))
            # 重置行高
            self.tableWidget.setRowHeight(i, default_row_height)

    def parse_datetime_from_string(self, date_time_str):
        # 去除所有非数字字符
        date_time_str = ''.join(filter(str.isdigit, date_time_str))
        return datetime.strptime(date_time_str, '%Y%m%d%H%M')
    
    def convert_setpoint_type(self, setpoint_type):
        type_to_description = {
            "lt": "Less Than",
            "eq": "Equal To",
            "gt": "Greater Than"
        }
        return type_to_description.get(setpoint_type, "Unknown")
    
    def handle_event_click(self, event_name, date_time, setpoint_value, setpoint_type, repeat_rules, event_schedule, event_zone, event_outstation, event_colour):
        # 调用 EventEditor 的方法
        self.event_infor.view_event(event_name, date_time, setpoint_value, setpoint_type, repeat_rules, event_schedule, event_zone, event_outstation, event_colour)
    
    def updateEventsTimeline(self, schedule_path, date):
        # 计算所选日期所在周的周一日期
        week_start_date = date.addDays(-date.dayOfWeek() + 1)

        # 如果当前有选中的日程文件路径，则加载该日程中的事件
        if schedule_path:
            self.loadEventsFromXML(schedule_path, week_start_date)
        else:
            # 如果没有选中的日程，则清空时间线
            self.clearEvents()
    