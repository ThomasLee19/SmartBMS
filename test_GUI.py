import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QDialog
from PySide6.QtWidgets import QCalendarWidget, QListWidget, QPushButton, QLabel
from PySide6.QtWidgets import QListWidgetItem, QMessageBox,  QSpacerItem
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from datetime import datetime
import xml.etree.ElementTree as ET
import os
import glob

from test_event_creation import EventDialog
from test_schedule_system import CreateScheduleDialog
from test_zone import ListItemWidget
from test_timeline_view import WeeklyScheduleView

class CalendarView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 1100, 650)
        self.current_schedule_path = None
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
        self.schedule_list.itemClicked.connect(self.on_schedule_item_clicked) 
        left_vbox.addWidget(self.schedule_list)

        # 创建时间线视图上方的水平布局
        timeline_top_hbox = QHBoxLayout()

        # 添加一个水平空间（spacer）
        spacer = QSpacerItem(8.5, 10)
        timeline_top_hbox.addItem(spacer)

        # 创建“Today”按钮
        today_button = QPushButton('Today')
        today_button.clicked.connect(self.on_today_button_clicked)
        today_button.setFixedSize(80, 40)
        timeline_top_hbox.addWidget(today_button)

        # 添加一个水平空间
        spacer = QSpacerItem(20, 10)
        timeline_top_hbox.addItem(spacer)

        # 创建显示当前年份和月份的标签
        self.current_date_label = QLabel() 
        self.current_date_label.setFont(QFont('Segoe UI', 16)) 
        timeline_top_hbox.addWidget(self.current_date_label)

        # 创建中间的时间线视图并将其赋值给self.timeline_view
        self.timeline_view = WeeklyScheduleView(self)
        self.timeline_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 创建包含时间线视图和其上方布局的垂直布局
        timeline_vbox = QVBoxLayout()
        timeline_vbox.addLayout(timeline_top_hbox)
        timeline_vbox.addWidget(self.timeline_view)
    
        # 创建一个QWidget并设置其布局为timeline_vbox
        timeline_widget = QWidget()
        timeline_widget.setLayout(timeline_vbox)

        # 加载现有的日程到"My Schedule"列表
        self.loadSchedules()

        # 将左侧和中间的布局添加到水平布局
        hbox.addLayout(left_vbox, 1)
        hbox.addWidget(timeline_widget, 3)
        
        # 设置中心窗口的布局
        central_widget = QWidget()
        central_widget.setLayout(hbox)
        self.setCentralWidget(central_widget)

    def on_today_button_clicked(self):
        current_date = QDate.currentDate()  # 获取当前日期
        self.updateTimeline(current_date)

    def refreshEvents(self, date):
        # 计算所选日期所在周的周一日期
        week_start_date = date.addDays(-date.dayOfWeek() + 1)

        # 如果当前有选中的日程文件路径，则加载该日程中的事件
        if self.current_schedule_path:
            self.timeline_view.loadEventsFromXML(self.current_schedule_path, week_start_date)
        else:
            # 如果没有选中的日程，则清空时间线
            self.timeline_view.clearEvents()

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

        # 当日历中的日期被点击时，更新年份与月份标签
        self.updateLabel(date)

    def updateLabel(self, date):
        start_date = date.addDays(-date.dayOfWeek() + 1)
        end_date = start_date.addDays(6)

        label_text = self.format_timeline_label(start_date, end_date)
        self.current_date_label.setText(label_text)  # 更新已存在的标签文本

    def format_timeline_label(self, start_date, end_date):
        # 清空当前标签
        self.current_date_label.setText("")

        # 首先将QDate转换为datetime.date对象
        start_date = datetime(start_date.year(), start_date.month(), start_date.day()).date()
        end_date = datetime(end_date.year(), end_date.month(), end_date.day()).date()

        # 月份和年份的格式化
        month_name = start_date.strftime("%B")
        start_month = start_date.strftime("%b")
        end_month = end_date.strftime("%b")
        start_year = start_date.year
        end_year = end_date.year

        if start_year != end_year:
            return f"{start_month} {start_year} - {end_month} {end_year}"
        elif start_date.month != end_date.month:
            return f"{start_month} - {end_month} {start_year}"
        else:
            return f"{month_name} {start_year}"

        
    def on_new_schedule_button_clicked(self):
        dialog = CreateScheduleDialog(self)
        dialog.schedule_created.connect(self.loadSchedules)  # 连接信号到槽
        if dialog.exec() == QDialog.Accepted and dialog.operation_successful:
            pass

    def on_schedule_item_clicked(self, item):
        # 获取被点击的日程项对应的ListItemWidget
        item_widget = self.schedule_list.itemWidget(item)

        if item_widget:
            # 更新当前选中的日程文件路径
            self.current_schedule_path = item_widget.schedule_file

            # 获取当前时间线视图的周开始日期
            week_start_date_str = self.timeline_view.tableWidget.horizontalHeaderItem(0).text().split('\n')[1]
            # 获取当前年份
            current_year = QDate.currentDate().year()
            # 将年份添加到日期字符串中
            full_date_str = f"{week_start_date_str}/{current_year}"
            # 转换为QDate对象
            week_start_date = QDate.fromString(full_date_str, 'dd/MM/yyyy')

            # 调用refreshEvents来更新视图
            self.refreshEvents(week_start_date)

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
        self.updateLabel(current_date)
        
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
