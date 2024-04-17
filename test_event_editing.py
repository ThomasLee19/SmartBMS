from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class EventEditor:
    def __init__(self, parent=None):
        self.parent = parent

    def view_event(self, event_name, event_time, schedule_name, zone_id):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Event Infor")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Event Name: {event_name}"))
        layout.addWidget(QLabel(f"Event Time: {event_time.strftime('%Y-%m-%d %H:%M')}"))
        layout.addWidget(QLabel(f"Schedule: {schedule_name}"))
        layout.addWidget(QLabel(f"Zone: {zone_id}"))
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        dialog.setLayout(layout)
        dialog.exec_()