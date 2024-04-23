from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt

class EventEditor:
    def __init__(self, parent=None):
        self.parent = parent

    def view_event(self, event_name, event_time, setpoint_value, setpoint_type, schedule_name, zone_id, event_colour):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Event Information")
        dialog.setFixedSize(400, 200)

        # Create a widget to hold the buttons with a fixed width
        button_container = QWidget()
        button_container.setFixedHeight(40)  # Set the fixed width of the container

        # Create horizontal layout for buttons within the container
        button_layout = QHBoxLayout(button_container)

        # Color display
        rgb_tuple = eval(event_colour)
        rgb_css = f"rgb({rgb_tuple[0]}, {rgb_tuple[1]}, {rgb_tuple[2]})"
        color_label = QLabel()
        color_label.setFixedSize(40, 30)  # Set the size of the color display area
        color_label.setStyleSheet(f"background-color: {rgb_css};")
        button_layout.addWidget(color_label)

        button_layout.addStretch(1)

        # Edit button with icon and fixed size
        edit_button = QPushButton()
        edit_button.setIcon(QIcon('Images/edit_event.jpg'))
        edit_button.setFixedSize(30, 30)
        edit_button.clicked.connect(lambda: self.edit_event(event_name, dialog))
        
        # Delete button with icon and fixed size
        delete_button = QPushButton()
        delete_button.setIcon(QIcon('Images/delete_event.jpg'))
        delete_button.setFixedSize(30, 30)
        delete_button.clicked.connect(lambda: self.delete_event(event_name, dialog))
        
        # Add buttons to the horizontal layout
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Add button container to the main layout
        layout.addWidget(button_container)

        # Set Font
        font = QFont()
        font.setPointSize(14)

        # Event information labels
        event_name_label = QLabel(f"Name: {event_name}")
        event_name_label.setFont(font)
        layout.addWidget(event_name_label)

        layout.addWidget(QLabel(f"Time: {event_time.strftime('%Y-%m-%d %H:%M')}"))
        layout.addWidget(QLabel(f"Setpoint Value: {setpoint_value}"))
        layout.addWidget(QLabel(f"Setpoint Type: {setpoint_type}"))
        layout.addWidget(QLabel(f"Schedule: {schedule_name}"))
        layout.addWidget(QLabel(f"Zone: {zone_id}"))
        
        # Set the dialog layout
        dialog.setLayout(layout)
        dialog.exec_()

    def delete_event(self, event_name, dialog):
        print(f"Deleting event: {event_name}")
        dialog.accept()

    def edit_event(self, event_name, dialog):
        print(f"Editing event: {event_name}")
        dialog.accept()
