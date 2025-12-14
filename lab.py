"""
PyQt5 Glucometer Analyzer - Medical Device Simulation
A professional desktop application for glucose level monitoring and analysis
"""

import sys
import csv
import json
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QFrame, QComboBox,
                             QHeaderView, QMessageBox, QFileDialog, QDialog,
                             QGridLayout, QSpinBox, QDoubleSpinBox, QGroupBox,
                             QRadioButton, QButtonGroup, QProgressBar, QTabWidget,
                             QScrollArea, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import winsound
import statistics
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch


class GlucoseAnalyzer:
    """
    Core analysis logic for glucose level classification
    Handles all medical device logic separate from UI
    
    Thresholds based on:
    - ADA (American Diabetes Association) Clinical Guidelines
    - ISO 15197:2013 compliance for accuracy requirements
    - Severe hypoglycemia threshold: < 54 mg/dL (Level 3)
    - Hypoglycemia threshold: < 70 mg/dL (Level 1-2)
    - Normal fasting: 70-100 mg/dL
    - Normal postprandial: < 140 mg/dL
    - Hyperglycemia: > 180 mg/dL
    
    Note: ISO 15197:2013 requires:
    - For glucose < 100 mg/dL: ±15 mg/dL accuracy
    - For glucose ≥ 100 mg/dL: ±15% accuracy
    """
    
    # Classification thresholds (mg/dL) - Updated to match ADA/ISO 15197 standards
    CRITICAL_LOW = 54    # Severe hypoglycemia (ADA Level 3)
    WARNING_LOW = 70     # Hypoglycemia (ADA Level 1-2)
    NORMAL_LOW = 70
    NORMAL_HIGH = 140    # Upper limit for postprandial glucose
    WARNING_HIGH = 180   # Hyperglycemia threshold
    
    @staticmethod
    def analyze(glucose_value):
        """
        Analyze glucose level and return status information
        
        Args:
            glucose_value (float): Glucose level in mg/dL
            
        Returns:
            dict: Contains status, color, severity, and message
        """
        result = {
            'value': glucose_value,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if glucose_value < GlucoseAnalyzer.CRITICAL_LOW:
            result['status'] = 'CRITICAL LOW'
            result['color'] = '#FF4444'
            result['severity'] = 'critical'
            result['message'] = '⚠️ CRITICAL: Severe Hypoglycemia! Immediate action required!'
            result['alarm'] = True
            
        elif glucose_value < GlucoseAnalyzer.WARNING_LOW:
            result['status'] = 'WARNING LOW'
            result['color'] = '#FFA500'
            result['severity'] = 'warning'
            result['message'] = '⚠️ WARNING: Low glucose level detected.'
            result['alarm'] = True
            
        elif glucose_value <= GlucoseAnalyzer.NORMAL_HIGH:
            result['status'] = 'NORMAL'
            result['color'] = '#4CAF50'
            result['severity'] = 'normal'
            result['message'] = '✓ Glucose level is within normal range.'
            result['alarm'] = False
            
        elif glucose_value <= GlucoseAnalyzer.WARNING_HIGH:
            result['status'] = 'WARNING HIGH'
            result['color'] = '#FFA500'
            result['severity'] = 'warning'
            result['message'] = '⚠️ WARNING: Elevated glucose level detected.'
            result['alarm'] = True
            
        else:  # > WARNING_HIGH
            result['status'] = 'CRITICAL HIGH'
            result['color'] = '#FF4444'
            result['severity'] = 'critical'
            result['message'] = '⚠️ CRITICAL: Severe Hyperglycemia! Immediate action required!'
            result['alarm'] = True
            
        return result


class DatabaseManager:
    """
    Manages SQLite database operations for persistent data storage
    """
    
    def __init__(self, db_name="glucometer_data.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Readings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                glucose_value REAL,
                status TEXT,
                condition TEXT,
                timestamp TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        ''')
        
        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                age INTEGER,
                diabetes_type TEXT,
                target_min REAL DEFAULT 70,
                target_max REAL DEFAULT 140,
                created_date TEXT
            )
        ''')
        
        # Goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                goal_type TEXT,
                target_value REAL,
                current_value REAL,
                start_date TEXT,
                end_date TEXT,
                achieved INTEGER DEFAULT 0,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_patient(self, name, age, diabetes_type):
        """Add a new patient"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO patients (name, age, diabetes_type, created_date)
                VALUES (?, ?, ?, ?)
            ''', (name, age, diabetes_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            patient_id = cursor.lastrowid
            conn.close()
            return patient_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def get_patients(self):
        """Get all patients"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM patients')
        patients = cursor.fetchall()
        conn.close()
        return patients
    
    def get_patient_by_name(self, name):
        """Get patient by name"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM patients WHERE name = ?', (name,))
        patient = cursor.fetchone()
        conn.close()
        return patient
    
    def update_patient_targets(self, patient_id, target_min, target_max):
        """Update patient target ranges"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE patients SET target_min = ?, target_max = ?
            WHERE id = ?
        ''', (target_min, target_max, patient_id))
        conn.commit()
        conn.close()
    
    def add_reading(self, patient_id, glucose_value, status, condition, timestamp):
        """Add a new glucose reading"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO readings (patient_id, glucose_value, status, condition, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (patient_id, glucose_value, status, condition, timestamp))
        conn.commit()
        conn.close()
    
    def get_readings(self, patient_id, days=None):
        """Get readings for a patient, optionally filtered by days"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            cursor.execute('''
                SELECT * FROM readings 
                WHERE patient_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (patient_id, cutoff_date))
        else:
            cursor.execute('''
                SELECT * FROM readings 
                WHERE patient_id = ?
                ORDER BY timestamp DESC
            ''', (patient_id,))
        
        readings = cursor.fetchall()
        conn.close()
        return readings
    
    def add_goal(self, patient_id, goal_type, target_value, start_date, end_date):
        """Add a new goal"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO goals (patient_id, goal_type, target_value, current_value, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (patient_id, goal_type, target_value, 0, start_date, end_date))
        conn.commit()
        conn.close()
    
    def get_goals(self, patient_id):
        """Get all goals for a patient"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM goals WHERE patient_id = ?', (patient_id,))
        goals = cursor.fetchall()
        conn.close()
        return goals
    
    def update_goal_progress(self, goal_id, current_value, achieved=0):
        """Update goal progress"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE goals SET current_value = ?, achieved = ?
            WHERE id = ?
        ''', (current_value, achieved, goal_id))
        conn.commit()
        conn.close()


class StatisticsCalculator:
    """
    Calculate statistical metrics for glucose readings
    """
    
    @staticmethod
    def calculate_statistics(readings):
        """Calculate comprehensive statistics from readings"""
        if not readings:
            return None
        
        values = [r[2] for r in readings]  # glucose_value is at index 2
        
        stats = {
            'count': len(values),
            'average': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
            'min': min(values),
            'max': max(values),
            'range': max(values) - min(values)
        }
        
        # Calculate time in range
        normal_count = sum(1 for v in values if 70 <= v <= 140)
        stats['time_in_range'] = (normal_count / len(values)) * 100
        
        # Estimate A1C (formula: A1C ≈ (average_glucose + 46.7) / 28.7)
        # Based on ADAG study - converts average glucose to estimated A1C
        stats['estimated_a1c'] = round((stats['average'] + 46.7) / 28.7, 1)
        
        # Count by status - Updated to match ADA/ISO 15197 thresholds
        stats['critical_low'] = sum(1 for v in values if v < 54)      # Severe hypoglycemia
        stats['warning_low'] = sum(1 for v in values if 54 <= v < 70)  # Hypoglycemia
        stats['normal'] = normal_count
        stats['warning_high'] = sum(1 for v in values if 140 < v <= 180)  # Hyperglycemia
        stats['critical_high'] = sum(1 for v in values if v > 180)    # Severe hyperglycemia
        
        return stats


class TrendPlotWidget(QWidget):
    """
    Custom widget for plotting glucose trends using matplotlib
    Embedded matplotlib canvas in PyQt5
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(6, 4), facecolor='#2b2b2b')
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Data storage
        self.glucose_values = []
        self.timestamps = []
        self.max_points = 20  # Show last 20 readings
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Initial plot setup
        self.setup_plot()
        
    def setup_plot(self):
        """Configure plot appearance"""
        self.ax.set_facecolor('#1e1e1e')
        self.ax.set_xlabel('Reading Number', color='white', fontsize=10)
        self.ax.set_ylabel('Glucose (mg/dL)', color='white', fontsize=10)
        self.ax.set_title('Glucose Trend Analysis', color='white', fontsize=12, fontweight='bold')
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.grid(True, alpha=0.3, color='gray', linestyle='--')
        
        # Add reference zones
        self.ax.axhspan(70, 140, alpha=0.1, color='green', label='Normal Range')
        self.ax.axhspan(140, 180, alpha=0.1, color='orange')
        self.ax.axhspan(50, 70, alpha=0.1, color='orange')
        
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        
    def add_reading(self, glucose_value):
        """Add a new glucose reading to the plot"""
        self.glucose_values.append(glucose_value)
        self.timestamps.append(len(self.glucose_values))
        
        # Keep only last N points
        if len(self.glucose_values) > self.max_points:
            self.glucose_values.pop(0)
            self.timestamps.pop(0)
        
        self.update_plot()
        
    def update_plot(self):
        """Redraw the plot with current data"""
        self.ax.clear()
        self.setup_plot()
        
        if self.glucose_values:
            # Plot line
            line = self.ax.plot(self.timestamps, self.glucose_values, 
                               'o-', color='#00D4FF', linewidth=2, 
                               markersize=6, label='Glucose Level')
            
            # Color-code points based on status
            for i, val in enumerate(self.glucose_values):
                if val < 50 or val > 180:
                    color = '#FF4444'
                elif val < 70 or val > 140:
                    color = '#FFA500'
                else:
                    color = '#4CAF50'
                self.ax.plot(self.timestamps[i], val, 'o', 
                           color=color, markersize=8, zorder=5)
            
            # Adjust y-axis limits
            y_min = min(self.glucose_values) - 20
            y_max = max(self.glucose_values) + 20
            self.ax.set_ylim(max(0, y_min), y_max)
            
            self.ax.legend(loc='upper left', fontsize=8, facecolor='#2b2b2b', 
                          edgecolor='white', labelcolor='white')
        
        self.canvas.draw()
        
    def clear_plot(self):
        """Clear all data and reset the plot"""
        self.glucose_values.clear()
        self.timestamps.clear()
        self.ax.clear()
        self.setup_plot()
        self.canvas.draw()


class MainWindow(QMainWindow):
    """
    Main application window for Glucometer Analyzer
    Coordinates all UI components and handles user interactions
    """
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.setWindowTitle("Glucometer Analyzer - Professional Medical Device")
        self.setGeometry(100, 100, 1500, 850)
        
        # Database and data management
        self.db = DatabaseManager()
        self.history = []
        
        # Patient management
        self.current_patient_id = None
        self.current_patient_name = "Default Patient"
        self.ensure_default_patient()
        
        # Theme state
        self.dark_mode = True
        
        # Alarm state
        self.alarm_active = False
        self.flash_state = False
        
        # Create UI
        self.init_ui()
        
        # Apply styles
        self.apply_styles()
        
        # Setup alarm timer
        self.alarm_timer = QTimer()
        self.alarm_timer.timeout.connect(self.flash_alarm)
        
        # Load existing data (after UI is created)
        self.load_patient_data()
    
    def ensure_default_patient(self):
        """Ensure a default patient exists"""
        patient = self.db.get_patient_by_name("Default Patient")
        if not patient:
            self.current_patient_id = self.db.add_patient("Default Patient", 30, "Normal")
        else:
            self.current_patient_id = patient[0]
        
    def init_ui(self):
        """Initialize all UI components"""
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header with theme toggle and patient selector
        header = self.create_enhanced_header()
        main_layout.addWidget(header)
        
        # Tab widget for different views
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 10))
        
        # Tab 1: Main Monitor
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout(main_tab)
        
        # Main content area (horizontal split)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left panel: Input controls
        left_panel = self.create_input_panel()
        content_layout.addWidget(left_panel, 1)
        
        # Middle panel: Status display
        middle_panel = self.create_status_panel()
        content_layout.addWidget(middle_panel, 1)
        
        # Right panel: Trend graph
        right_panel = self.create_graph_panel()
        content_layout.addWidget(right_panel, 2)
        
        main_tab_layout.addLayout(content_layout, 2)
        
        # Bottom panel: History table
        history_panel = self.create_history_panel()
        main_tab_layout.addWidget(history_panel, 1)
        
        self.tabs.addTab(main_tab, "📊 Monitor")
        
        # Tab 2: Statistics
        stats_tab = self.create_statistics_tab()
        self.tabs.addTab(stats_tab, "📈 Statistics")
        
        # Tab 3: Goals
        goals_tab = self.create_goals_tab()
        self.tabs.addTab(goals_tab, "🎯 Goals")
        
        # Tab 4: Advanced Graphs
        graphs_tab = self.create_advanced_graphs_tab()
        self.tabs.addTab(graphs_tab, "📉 Advanced Graphs")
        
        main_layout.addWidget(self.tabs)
        
    def create_enhanced_header(self):
        """Create enhanced application header with controls"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        
        # Title section
        title = QLabel("🏥 Glucometer Analyzer Pro")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #00D4FF;")
        
        subtitle = QLabel("Advanced Medical Device Monitoring")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #888;")
        
        title_layout = QVBoxLayout()
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Patient selector
        patient_label = QLabel("Patient:")
        patient_label.setFont(QFont("Segoe UI", 10))
        header_layout.addWidget(patient_label)
        
        self.patient_combo = QComboBox()
        self.patient_combo.setFont(QFont("Segoe UI", 10))
        self.patient_combo.setMinimumWidth(150)
        self.patient_combo.currentTextChanged.connect(self.switch_patient)
        self.load_patients_combo()
        header_layout.addWidget(self.patient_combo)
        
        # Add patient button
        add_patient_btn = QPushButton("+ New Patient")
        add_patient_btn.setFont(QFont("Segoe UI", 9))
        add_patient_btn.clicked.connect(self.show_add_patient_dialog)
        add_patient_btn.setFixedHeight(30)
        header_layout.addWidget(add_patient_btn)
        
        # Theme toggle
        self.theme_btn = QPushButton("☀️ Light Mode")
        self.theme_btn.setFont(QFont("Segoe UI", 9))
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setFixedHeight(30)
        header_layout.addWidget(self.theme_btn)
        
        # Export button
        export_btn = QPushButton("📤 Export")
        export_btn.setFont(QFont("Segoe UI", 9))
        export_btn.clicked.connect(self.show_export_dialog)
        export_btn.setFixedHeight(30)
        header_layout.addWidget(export_btn)
        
        return header_frame
    
    def create_header(self):
        """Legacy method - redirects to enhanced header"""
        return self.create_enhanced_header()
        
    def create_input_panel(self):
        """Create input controls panel"""
        panel = QFrame()
        panel.setObjectName("inputPanel")
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📊 Input Data")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #00D4FF;")
        layout.addWidget(title)
        
        # Glucose input
        glucose_label = QLabel("Glucose Level (mg/dL):")
        glucose_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(glucose_label)
        
        self.glucose_input = QLineEdit()
        self.glucose_input.setPlaceholderText("Enter value (e.g., 120)")
        self.glucose_input.setFont(QFont("Segoe UI", 12))
        self.glucose_input.setFixedHeight(40)
        self.glucose_input.returnPressed.connect(self.analyze_glucose)
        layout.addWidget(self.glucose_input)
        
        # Patient condition dropdown
        condition_label = QLabel("Patient Condition:")
        condition_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(condition_label)
        
        self.condition_combo = QComboBox()
        self.condition_combo.addItems(["Normal", "Diabetic", "Fasting"])
        self.condition_combo.setFont(QFont("Segoe UI", 11))
        self.condition_combo.setFixedHeight(40)
        layout.addWidget(self.condition_combo)
        
        # Analyze button
        self.analyze_btn = QPushButton("🔬 ANALYZE")
        self.analyze_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.analyze_btn.setFixedHeight(50)
        self.analyze_btn.clicked.connect(self.analyze_glucose)
        self.analyze_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.analyze_btn)
        
        # Clear history button
        clear_btn = QPushButton("🗑️ Clear History")
        clear_btn.setFont(QFont("Segoe UI", 10))
        clear_btn.setFixedHeight(40)
        clear_btn.clicked.connect(self.clear_history)
        clear_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(clear_btn)
        
        layout.addStretch()
        
        # Info panel
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_layout = QVBoxLayout(info_frame)
        
        info_title = QLabel("ℹ️ Reference Ranges (ISO 15197/ADA)")
        info_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        info_layout.addWidget(info_title)
        
        ranges = [
            "Normal: 70-140 mg/dL",
            "Warning Low: 54-70 mg/dL",
            "Warning High: 140-180 mg/dL",
            "Critical Low: <54 mg/dL",
            "Critical High: >180 mg/dL"
        ]
        
        for range_text in ranges:
            label = QLabel(range_text)
            label.setFont(QFont("Segoe UI", 9))
            label.setStyleSheet("color: #aaa;")
            info_layout.addWidget(label)
        
        layout.addWidget(info_frame)
        
        return panel
        
    def create_status_panel(self):
        """Create status display panel"""
        panel = QFrame()
        panel.setObjectName("statusPanel")
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("📈 Analysis Result")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #00D4FF;")
        layout.addWidget(title)
        
        # Status indicator (large colored box)
        self.status_indicator = QFrame()
        self.status_indicator.setObjectName("statusIndicator")
        self.status_indicator.setFixedHeight(200)
        indicator_layout = QVBoxLayout(self.status_indicator)
        
        self.status_value_label = QLabel("--")
        self.status_value_label.setFont(QFont("Segoe UI", 48, QFont.Bold))
        self.status_value_label.setAlignment(Qt.AlignCenter)
        indicator_layout.addWidget(self.status_value_label)
        
        self.status_unit_label = QLabel("mg/dL")
        self.status_unit_label.setFont(QFont("Segoe UI", 16))
        self.status_unit_label.setAlignment(Qt.AlignCenter)
        self.status_unit_label.setStyleSheet("color: #888;")
        indicator_layout.addWidget(self.status_unit_label)
        
        layout.addWidget(self.status_indicator)
        
        # Status text
        self.status_text_label = QLabel("AWAITING INPUT")
        self.status_text_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.status_text_label.setAlignment(Qt.AlignCenter)
        self.status_text_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_text_label)
        
        # Message box
        self.message_label = QLabel("Enter a glucose value and click Analyze")
        self.message_label.setFont(QFont("Segoe UI", 11))
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: #aaa; padding: 15px;")
        layout.addWidget(self.message_label)
        
        # Timestamp
        self.timestamp_label = QLabel("")
        self.timestamp_label.setFont(QFont("Segoe UI", 9))
        self.timestamp_label.setAlignment(Qt.AlignCenter)
        self.timestamp_label.setStyleSheet("color: #666;")
        layout.addWidget(self.timestamp_label)
        
        layout.addStretch()
        
        return panel
        
    def create_graph_panel(self):
        """Create trend graph panel"""
        panel = QFrame()
        panel.setObjectName("graphPanel")
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("📉 Glucose Trend")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #00D4FF;")
        layout.addWidget(title)
        
        # Graph widget
        self.trend_plot = TrendPlotWidget()
        layout.addWidget(self.trend_plot)
        
        return panel
        
    def create_history_panel(self):
        """Create history table panel"""
        panel = QFrame()
        panel.setObjectName("historyPanel")
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("📋 Measurement History")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #00D4FF;")
        layout.addWidget(title)
        
        # Table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Timestamp", "Glucose (mg/dL)", "Status", "Condition"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setFont(QFont("Segoe UI", 10))
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.history_table)
        
        return panel
    
    def create_statistics_tab(self):
        """Create statistics dashboard tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📊 Statistical Analysis Dashboard")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #00D4FF;")
        layout.addWidget(title)
        
        # Scroll area for statistics
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Statistics panels in grid
        stats_grid = QGridLayout()
        
        # Create stat display widgets
        self.stat_labels = {}
        stat_names = [
            ("Total Readings", "count"),
            ("Average Glucose", "average"),
            ("Median", "median"),
            ("Std Deviation", "std_dev"),
            ("Minimum", "min"),
            ("Maximum", "max"),
            ("Time in Range", "time_in_range"),
            ("Estimated A1C", "estimated_a1c"),
            ("Critical Low", "critical_low"),
            ("Warning Low", "warning_low"),
            ("Normal", "normal"),
            ("Warning High", "warning_high"),
            ("Critical High", "critical_high")
        ]
        
        row, col = 0, 0
        for display_name, key in stat_names:
            stat_frame = QFrame()
            stat_frame.setObjectName("statCard")
            stat_layout = QVBoxLayout(stat_frame)
            
            name_label = QLabel(display_name)
            name_label.setFont(QFont("Segoe UI", 10))
            name_label.setStyleSheet("color: #aaa;")
            name_label.setAlignment(Qt.AlignCenter)
            
            value_label = QLabel("--")
            value_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
            value_label.setStyleSheet("color: #00D4FF;")
            value_label.setAlignment(Qt.AlignCenter)
            
            stat_layout.addWidget(value_label)
            stat_layout.addWidget(name_label)
            
            self.stat_labels[key] = value_label
            stats_grid.addWidget(stat_frame, row, col)
            
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        scroll_layout.addLayout(stats_grid)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Statistics")
        refresh_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        refresh_btn.setFixedHeight(45)
        refresh_btn.clicked.connect(self.update_statistics)
        scroll_layout.addWidget(refresh_btn)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return tab
    
    def create_goals_tab(self):
        """Create goals and targets tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🎯 Goals & Targets")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #00D4FF;")
        layout.addWidget(title)
        
        # Goals display area
        self.goals_layout = QVBoxLayout()
        
        goals_scroll = QScrollArea()
        goals_scroll.setWidgetResizable(True)
        goals_content = QWidget()
        goals_content.setLayout(self.goals_layout)
        goals_scroll.setWidget(goals_content)
        
        layout.addWidget(goals_scroll)
        
        # Add goal button
        add_goal_btn = QPushButton("+ Add New Goal")
        add_goal_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        add_goal_btn.setFixedHeight(45)
        add_goal_btn.clicked.connect(self.show_add_goal_dialog)
        layout.addWidget(add_goal_btn)
        
        # Load goals
        self.load_goals()
        
        return tab
    
    def create_advanced_graphs_tab(self):
        """Create advanced visualization tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📉 Advanced Data Visualization")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #00D4FF;")
        layout.addWidget(title)
        
        # Graph type selector
        selector_layout = QHBoxLayout()
        
        graph_label = QLabel("Graph Type:")
        graph_label.setFont(QFont("Segoe UI", 10))
        selector_layout.addWidget(graph_label)
        
        self.graph_type_combo = QComboBox()
        self.graph_type_combo.addItems([
            "Distribution Histogram",
            "Box Plot",
            "Time of Day Heatmap",
            "Weekly Comparison",
            "Monthly Trend"
        ])
        self.graph_type_combo.setFont(QFont("Segoe UI", 10))
        self.graph_type_combo.currentTextChanged.connect(self.update_advanced_graph)
        selector_layout.addWidget(self.graph_type_combo)
        
        selector_layout.addStretch()
        
        update_graph_btn = QPushButton("🔄 Update")
        update_graph_btn.clicked.connect(self.update_advanced_graph)
        selector_layout.addWidget(update_graph_btn)
        
        layout.addLayout(selector_layout)
        
        # Advanced graph widget
        self.advanced_graph = TrendPlotWidget()
        layout.addWidget(self.advanced_graph)
        
        return tab
        
    def analyze_glucose(self):
        """Main analysis function - processes glucose input"""
        try:
            # Get input value
            glucose_str = self.glucose_input.text().strip()
            if not glucose_str:
                self.show_message_box("Input Error", "Please enter a glucose value.")
                return
                
            glucose_value = float(glucose_str)
            
            # Validate input
            if glucose_value < 0 or glucose_value > 1000:
                self.show_message_box("Input Error", "Please enter a valid glucose value (0-1000 mg/dL).")
                return
            
            # Get patient condition
            condition = self.condition_combo.currentText()
            
            # Analyze using GlucoseAnalyzer
            result = GlucoseAnalyzer.analyze(glucose_value)
            
            # Save to database
            self.db.add_reading(self.current_patient_id, glucose_value, 
                              result['status'], condition, result['timestamp'])
            
            # Update UI with results
            self.update_status_display(result)
            
            # Add to history
            self.add_to_history(result, condition)
            
            # Update graph
            self.trend_plot.add_reading(glucose_value)
            
            # Handle alarm
            if result['alarm']:
                self.trigger_alarm()
                self.play_alarm_sound()
            else:
                self.stop_alarm()
            
            # Auto-refresh statistics
            self.update_statistics()
            
            # Clear input
            self.glucose_input.clear()
            self.glucose_input.setFocus()
            
        except ValueError:
            self.show_message_box("Input Error", "Please enter a valid numeric value.")
            
    def update_status_display(self, result):
        """Update the status panel with analysis results"""
        # Update value display
        self.status_value_label.setText(f"{result['value']:.1f}")
        
        # Update status text
        self.status_text_label.setText(result['status'])
        self.status_text_label.setStyleSheet(f"color: {result['color']}; font-weight: bold;")
        
        # Update message
        self.message_label.setText(result['message'])
        
        # Update timestamp
        self.timestamp_label.setText(f"Last reading: {result['timestamp']}")
        
        # Update indicator background
        self.status_indicator.setStyleSheet(f"""
            QFrame#statusIndicator {{
                background-color: {result['color']};
                border-radius: 10px;
                border: 3px solid white;
            }}
        """)
        
    def add_to_history(self, result, condition):
        """Add measurement to history table"""
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        
        # Add data
        items = [
            result['timestamp'],
            f"{result['value']:.1f}",
            result['status'],
            condition
        ]
        
        for col, text in enumerate(items):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            
            # Color-code status column
            if col == 2:
                color = QColor(result['color'])
                item.setForeground(color)
                item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            
            self.history_table.setItem(row, col, item)
        
        # Store in history list
        self.history.append(result)
        
        # Scroll to bottom
        self.history_table.scrollToBottom()
        
    def trigger_alarm(self):
        """Activate visual alarm (flashing)"""
        self.alarm_active = True
        self.alarm_timer.start(500)  # Flash every 500ms
        
    def stop_alarm(self):
        """Deactivate alarm"""
        self.alarm_active = False
        self.alarm_timer.stop()
        self.flash_state = False
        
    def flash_alarm(self):
        """Toggle alarm flash state"""
        if not self.alarm_active:
            return
            
        self.flash_state = not self.flash_state
        
        if self.flash_state:
            # Flash on
            self.status_indicator.setStyleSheet("""
                QFrame#statusIndicator {
                    background-color: #FF4444;
                    border-radius: 10px;
                    border: 5px solid #FFFF00;
                }
            """)
        else:
            # Flash off - restore current color
            current_color = self.status_text_label.styleSheet().split("color: ")[1].split(";")[0]
            self.status_indicator.setStyleSheet(f"""
                QFrame#statusIndicator {{
                    background-color: {current_color};
                    border-radius: 10px;
                    border: 3px solid white;
                }}
            """)
            
    def play_alarm_sound(self):
        """Play system beep for critical alerts"""
        try:
            # Determine if critical based on current status
            status_text = self.status_text_label.text()
            
            if 'CRITICAL' in status_text:
                # Critical condition: play 3 urgent beeps
                for i in range(3):
                    winsound.Beep(1200, 200)  # 1200 Hz for 200ms (urgent tone)
                    if i < 2:  # Don't wait after last beep
                        QTimer.singleShot(250, lambda: None)  # Short pause between beeps
            else:
                # Warning condition: play single beep
                winsound.Beep(800, 300)  # 800 Hz for 300ms (warning tone)
        except:
            # If winsound fails, silently continue
            pass
            
    def clear_history(self):
        """Clear all history and reset the application"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Clear History")
        msg_box.setText("Are you sure you want to clear all measurements?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #00D4FF;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #00B8E6;
            }
        """)
        reply = msg_box.exec_()
        
        if reply == QMessageBox.Yes:
            # Clear table
            self.history_table.setRowCount(0)
            
            # Clear history list
            self.history.clear()
            
            # Clear graph
            self.trend_plot.clear_plot()
            
            # Reset status display
            self.status_value_label.setText("--")
            self.status_text_label.setText("AWAITING INPUT")
            self.status_text_label.setStyleSheet("color: #888;")
            self.message_label.setText("Enter a glucose value and click Analyze")
            self.timestamp_label.setText("")
            
            self.status_indicator.setStyleSheet("""
                QFrame#statusIndicator {
                    background-color: #333;
                    border-radius: 10px;
                    border: 3px solid #555;
                }
            """)
            
            # Stop any active alarms
            self.stop_alarm()
    
    def show_message_box(self, title, message, icon_type="warning"):
        """Show a styled message box"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if icon_type == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        elif icon_type == "information":
            msg_box.setIcon(QMessageBox.Information)
        elif icon_type == "error":
            msg_box.setIcon(QMessageBox.Critical)
        
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #00D4FF;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #00B8E6;
            }
        """)
        msg_box.exec_()
    
    # ========== NEW FEATURE METHODS ==========
    
    def load_patients_combo(self):
        """Load patients into combo box"""
        self.patient_combo.clear()
        patients = self.db.get_patients()
        for patient in patients:
            self.patient_combo.addItem(patient[1])  # patient name
        
        # Set current patient
        if self.current_patient_name:
            index = self.patient_combo.findText(self.current_patient_name)
            if index >= 0:
                self.patient_combo.setCurrentIndex(index)
    
    def switch_patient(self, patient_name):
        """Switch to a different patient"""
        if not patient_name:
            return
        
        # Check if UI is initialized
        if not hasattr(self, 'history_table'):
            return
        
        patient = self.db.get_patient_by_name(patient_name)
        if patient:
            self.current_patient_id = patient[0]
            self.current_patient_name = patient[1]
            self.load_patient_data()
            self.update_statistics()
            self.load_goals()
    
    def show_add_patient_dialog(self):
        """Show dialog to add new patient"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Patient")
        dialog.setModal(True)
        dialog.setFixedSize(400, 250)
        
        layout = QVBoxLayout(dialog)
        
        # Name
        name_label = QLabel("Patient Name:")
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter patient name")
        
        # Age
        age_label = QLabel("Age:")
        age_input = QSpinBox()
        age_input.setRange(1, 120)
        age_input.setValue(30)
        
        # Diabetes Type
        type_label = QLabel("Diabetes Type:")
        type_combo = QComboBox()
        type_combo.addItems(["Normal", "Type 1", "Type 2", "Gestational", "Pre-diabetic"])
        
        layout.addWidget(name_label)
        layout.addWidget(name_input)
        layout.addWidget(age_label)
        layout.addWidget(age_input)
        layout.addWidget(type_label)
        layout.addWidget(type_combo)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        def save_patient():
            name = name_input.text().strip()
            if not name:
                self.show_message_box("Error", "Please enter a patient name")
                return
            
            patient_id = self.db.add_patient(name, age_input.value(), type_combo.currentText())
            if patient_id:
                self.load_patients_combo()
                self.patient_combo.setCurrentText(name)
                dialog.accept()
            else:
                self.show_message_box("Error", "Patient name already exists")
        
        save_btn.clicked.connect(save_patient)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        # Apply dark theme to dialog
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 11pt;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #333;
                color: white;
                border: 2px solid #444;
                border-radius: 5px;
                padding: 8px;
                font-size: 10pt;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 2px solid #00D4FF;
            }
            QPushButton {
                background-color: #00D4FF;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00B8E6;
            }
            QPushButton:pressed {
                background-color: #0099CC;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #333;
                color: white;
                selection-background-color: #00D4FF;
                border: 1px solid #444;
            }
        """)
        dialog.exec_()
    
    def load_patient_data(self):
        """Load patient data from database"""
        if not self.current_patient_id:
            return
        
        # Check if UI is initialized
        if not hasattr(self, 'history_table'):
            return
        
        # Clear current data
        self.history_table.setRowCount(0)
        self.trend_plot.clear_plot()
        self.history.clear()
        
        # Load from database
        readings = self.db.get_readings(self.current_patient_id)
        
        for reading in reversed(readings):  # Reverse to show oldest first
            # reading: (id, patient_id, glucose_value, status, condition, timestamp)
            result = {
                'value': reading[2],
                'status': reading[3],
                'timestamp': reading[5],
                'color': self.get_color_for_status(reading[3])
            }
            self.add_to_history(result, reading[4])
            self.trend_plot.add_reading(reading[2])
    
    def get_color_for_status(self, status):
        """Get color code for status"""
        if 'CRITICAL' in status:
            return '#FF4444'
        elif 'WARNING' in status:
            return '#FFA500'
        else:
            return '#4CAF50'
    
    def update_statistics(self):
        """Update statistics dashboard"""
        if not self.current_patient_id:
            return
        
        # Check if UI is initialized
        if not hasattr(self, 'stat_labels'):
            return
        
        readings = self.db.get_readings(self.current_patient_id, days=30)  # Last 30 days
        
        if not readings:
            # Clear statistics
            for key in self.stat_labels:
                self.stat_labels[key].setText("--")
            return
        
        stats = StatisticsCalculator.calculate_statistics(readings)
        
        if stats:
            self.stat_labels['count'].setText(str(stats['count']))
            self.stat_labels['average'].setText(f"{stats['average']:.1f} mg/dL")
            self.stat_labels['median'].setText(f"{stats['median']:.1f} mg/dL")
            self.stat_labels['std_dev'].setText(f"{stats['std_dev']:.1f}")
            self.stat_labels['min'].setText(f"{stats['min']:.1f} mg/dL")
            self.stat_labels['max'].setText(f"{stats['max']:.1f} mg/dL")
            self.stat_labels['time_in_range'].setText(f"{stats['time_in_range']:.1f}%")
            self.stat_labels['estimated_a1c'].setText(f"{stats['estimated_a1c']}%")
            self.stat_labels['critical_low'].setText(str(stats['critical_low']))
            self.stat_labels['warning_low'].setText(str(stats['warning_low']))
            self.stat_labels['normal'].setText(str(stats['normal']))
            self.stat_labels['warning_high'].setText(str(stats['warning_high']))
            self.stat_labels['critical_high'].setText(str(stats['critical_high']))
    
    def show_export_dialog(self):
        """Show export options dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Export Data")
        dialog.setModal(True)
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        title = QLabel("Select Export Format:")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Export options
        csv_btn = QPushButton("📄 Export to CSV")
        csv_btn.setFixedHeight(50)
        csv_btn.clicked.connect(lambda: self.export_data('csv', dialog))
        
        json_btn = QPushButton("📋 Export to JSON")
        json_btn.setFixedHeight(50)
        json_btn.clicked.connect(lambda: self.export_data('json', dialog))
        
        pdf_btn = QPushButton("📕 Export to PDF Report")
        pdf_btn.setFixedHeight(50)
        pdf_btn.clicked.connect(lambda: self.export_data('pdf', dialog))
        
        layout.addWidget(csv_btn)
        layout.addWidget(json_btn)
        layout.addWidget(pdf_btn)
        layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #00D4FF;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 20px;
                font-size: 12pt;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #00B8E6;
            }
            QPushButton:pressed {
                background-color: #0099CC;
            }
        """)
        dialog.exec_()
    
    def export_data(self, format_type, dialog):
        """Export data in specified format"""
        if not self.current_patient_id:
            self.show_message_box("Error", "No patient selected")
            return
        
        readings = self.db.get_readings(self.current_patient_id)
        
        if not readings:
            self.show_message_box("Error", "No data to export")
            return
        
        if format_type == 'csv':
            file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", 
                                                      f"{self.current_patient_name}_glucose_data.csv",
                                                      "CSV Files (*.csv)")
            if file_path:
                self.export_to_csv(readings, file_path)
                
        elif format_type == 'json':
            file_path, _ = QFileDialog.getSaveFileName(self, "Save JSON",
                                                      f"{self.current_patient_name}_glucose_data.json",
                                                      "JSON Files (*.json)")
            if file_path:
                self.export_to_json(readings, file_path)
                
        elif format_type == 'pdf':
            file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF",
                                                      f"{self.current_patient_name}_glucose_report.pdf",
                                                      "PDF Files (*.pdf)")
            if file_path:
                self.export_to_pdf(readings, file_path)
        
        if file_path:
            self.show_message_box("Success", f"Data exported successfully to:\n{file_path}", "information")
            dialog.accept()
    
    def export_to_csv(self, readings, file_path):
        """Export to CSV file"""
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Glucose (mg/dL)', 'Status', 'Condition'])
            
            for reading in readings:
                writer.writerow([reading[5], reading[2], reading[3], reading[4]])
    
    def export_to_json(self, readings, file_path):
        """Export to JSON file"""
        data = {
            'patient_name': self.current_patient_name,
            'export_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'readings': []
        }
        
        for reading in readings:
            data['readings'].append({
                'timestamp': reading[5],
                'glucose_value': reading[2],
                'status': reading[3],
                'condition': reading[4]
            })
        
        with open(file_path, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=4)
    
    def export_to_pdf(self, readings, file_path):
        """Export to PDF report"""
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"<b>Glucose Monitoring Report</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Patient info
        patient_info = Paragraph(f"<b>Patient:</b> {self.current_patient_name}<br/>" + 
                                f"<b>Report Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>" +
                                f"<b>Total Readings:</b> {len(readings)}", styles['Normal'])
        elements.append(patient_info)
        elements.append(Spacer(1, 0.3*inch))
        
        # Statistics
        stats = StatisticsCalculator.calculate_statistics(readings)
        if stats:
            stats_text = f"<b>Statistical Summary:</b><br/>" + \
                        f"Average Glucose: {stats['average']:.1f} mg/dL<br/>" + \
                        f"Time in Range: {stats['time_in_range']:.1f}%<br/>" + \
                        f"Estimated A1C: {stats['estimated_a1c']}%<br/>" + \
                        f"Range: {stats['min']:.1f} - {stats['max']:.1f} mg/dL"
            elements.append(Paragraph(stats_text, styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
        
        # Table data
        table_data = [['Timestamp', 'Glucose', 'Status', 'Condition']]
        for reading in readings[:50]:  # Limit to 50 most recent
            table_data.append([reading[5], f"{reading[2]:.1f}", reading[3], reading[4]])
        
        table = Table(table_data, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
    
    def toggle_theme(self):
        """Toggle between dark and light themes"""
        self.dark_mode = not self.dark_mode
        
        if self.dark_mode:
            self.theme_btn.setText("☀️ Light Mode")
            self.apply_styles()
        else:
            self.theme_btn.setText("🌙 Dark Mode")
            self.apply_light_theme()
    
    def apply_light_theme(self):
        """Apply light theme"""
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QFrame#headerFrame { background-color: #ffffff; border: 1px solid #ddd; border-radius: 10px; padding: 15px; }
            QFrame#inputPanel, QFrame#statusPanel, QFrame#graphPanel, QFrame#historyPanel, QFrame#statCard {
                background-color: #ffffff; border: 1px solid #ddd; border-radius: 10px; padding: 15px;
            }
            QLabel { color: #333; }
            QLineEdit, QComboBox, QSpinBox { background-color: #fff; color: #333; border: 2px solid #ccc; border-radius: 5px; padding: 8px; }
            QPushButton { background-color: #007acc; color: white; border: none; border-radius: 5px; padding: 10px; }
            QPushButton:hover { background-color: #005a9e; }
            QTableWidget { background-color: #fff; color: #333; gridline-color: #ddd; border: 1px solid #ddd; }
            QHeaderView::section { background-color: #e0e0e0; color: #333; padding: 8px; border: 1px solid #ccc; }
            QTabWidget::pane { border: 1px solid #ddd; background-color: #fff; }
            QTabBar::tab { background-color: #e0e0e0; color: #333; padding: 10px 20px; border: 1px solid #ccc; }
            QTabBar::tab:selected { background-color: #fff; border-bottom: 3px solid #007acc; }
        """)
    
    def load_goals(self):
        """Load and display goals"""
        # Check if UI is initialized
        if not hasattr(self, 'goals_layout'):
            return
        
        # Clear existing goals
        while self.goals_layout.count():
            child = self.goals_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.current_patient_id:
            return
        
        goals = self.db.get_goals(self.current_patient_id)
        
        if not goals:
            no_goals_label = QLabel("No goals set. Click 'Add New Goal' to create one.")
            no_goals_label.setFont(QFont("Segoe UI", 11))
            no_goals_label.setStyleSheet("color: #888; padding: 20px;")
            no_goals_label.setAlignment(Qt.AlignCenter)
            self.goals_layout.addWidget(no_goals_label)
            return
        
        for goal in goals:
            goal_widget = self.create_goal_widget(goal)
            self.goals_layout.addWidget(goal_widget)
    
    def create_goal_widget(self, goal):
        """Create a widget for displaying a goal"""
        # goal: (id, patient_id, goal_type, target_value, current_value, start_date, end_date, achieved)
        goal_frame = QFrame()
        goal_frame.setObjectName("statCard")
        layout = QVBoxLayout(goal_frame)
        
        # Goal title
        title = QLabel(f"🎯 {goal[2]}")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Progress
        progress_label = QLabel(f"Target: {goal[3]:.1f} | Current: {goal[4]:.1f}")
        progress_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(progress_label)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setMaximum(int(goal[3]))
        progress_bar.setValue(int(goal[4]))
        layout.addWidget(progress_bar)
        
        # Dates
        dates_label = QLabel(f"Period: {goal[5]} to {goal[6]}")
        dates_label.setFont(QFont("Segoe UI", 9))
        dates_label.setStyleSheet("color: #888;")
        layout.addWidget(dates_label)
        
        # Achievement status
        if goal[7]:
            achieved_label = QLabel("✓ Achieved!")
            achieved_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            layout.addWidget(achieved_label)
        
        return goal_frame
    
    def show_add_goal_dialog(self):
        """Show dialog to add new goal"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Goal")
        dialog.setModal(True)
        dialog.setFixedSize(400, 350)
        
        layout = QVBoxLayout(dialog)
        
        # Goal type
        type_label = QLabel("Goal Type:")
        type_combo = QComboBox()
        type_combo.addItems([
            "Maintain Time in Range >80%",
            "Keep Average Below 140 mg/dL",
            "Reduce Critical Events",
            "Take 100 Readings",
            "30-Day Consistency"
        ])
        
        # Target value
        target_label = QLabel("Target Value:")
        target_input = QDoubleSpinBox()
        target_input.setRange(0, 1000)
        target_input.setValue(80)
        target_input.setSuffix(" %")
        
        # End date
        end_label = QLabel("End Date:")
        end_date = QLabel((datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"))
        
        layout.addWidget(type_label)
        layout.addWidget(type_combo)
        layout.addWidget(target_label)
        layout.addWidget(target_input)
        layout.addWidget(end_label)
        layout.addWidget(end_date)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Goal")
        cancel_btn = QPushButton("Cancel")
        
        def save_goal():
            start = datetime.now().strftime("%Y-%m-%d")
            end = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            self.db.add_goal(self.current_patient_id, type_combo.currentText(),
                           target_input.value(), start, end)
            self.load_goals()
            dialog.accept()
        
        save_btn.clicked.connect(save_goal)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.setStyleSheet(self.styleSheet())
        dialog.exec_()
    
    def update_advanced_graph(self):
        """Update advanced graph based on selected type"""
        graph_type = self.graph_type_combo.currentText()
        
        if not self.current_patient_id:
            return
        
        readings = self.db.get_readings(self.current_patient_id, days=30)
        if not readings:
            return
        
        values = [r[2] for r in readings]
        
        self.advanced_graph.ax.clear()
        
        if graph_type == "Distribution Histogram":
            self.advanced_graph.ax.hist(values, bins=20, color='#00D4FF', edgecolor='white', alpha=0.7)
            self.advanced_graph.ax.set_xlabel('Glucose (mg/dL)', color='white')
            self.advanced_graph.ax.set_ylabel('Frequency', color='white')
            self.advanced_graph.ax.set_title('Glucose Distribution', color='white', fontweight='bold')
            
        elif graph_type == "Box Plot":
            box = self.advanced_graph.ax.boxplot([values], vert=True, patch_artist=True)
            for patch in box['boxes']:
                patch.set_facecolor('#00D4FF')
            self.advanced_graph.ax.set_ylabel('Glucose (mg/dL)', color='white')
            self.advanced_graph.ax.set_title('Glucose Variability', color='white', fontweight='bold')
        
        self.advanced_graph.ax.set_facecolor('#1e1e1e')
        self.advanced_graph.ax.tick_params(colors='white')
        self.advanced_graph.canvas.draw()
            
    def apply_styles(self):
        """Apply modern CSS stylesheet to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            
            QFrame#headerFrame {
                background-color: #252525;
                border-radius: 10px;
                padding: 15px;
            }
            
            QFrame#inputPanel, QFrame#statusPanel, QFrame#graphPanel, QFrame#historyPanel {
                background-color: #252525;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #333;
            }
            
            QFrame#infoFrame, QFrame#statCard {
                background-color: #2b2b2b;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #444;
            }
            
            QTabWidget::pane {
                border: 1px solid #333;
                background-color: #1e1e1e;
            }
            
            QTabBar::tab {
                background-color: #252525;
                color: white;
                padding: 10px 20px;
                border: 1px solid #333;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                border-bottom: 3px solid #00D4FF;
            }
            
            QTabBar::tab:hover {
                background-color: #2b2b2b;
            }
            
            QSpinBox, QDoubleSpinBox {
                background-color: #333;
                color: white;
                border: 2px solid #444;
                border-radius: 5px;
                padding: 8px;
            }
            
            QProgressBar {
                border: 2px solid #444;
                border-radius: 5px;
                text-align: center;
                background-color: #333;
                color: white;
            }
            
            QProgressBar::chunk {
                background-color: #00D4FF;
                border-radius: 3px;
            }
            
            QLabel {
                color: #ffffff;
            }
            
            QLineEdit {
                background-color: #333;
                color: white;
                border: 2px solid #444;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }
            
            QLineEdit:focus {
                border: 2px solid #00D4FF;
            }
            
            QComboBox {
                background-color: #333;
                color: white;
                border: 2px solid #444;
                border-radius: 5px;
                padding: 8px;
                font-size: 11px;
            }
            
            QComboBox:hover {
                border: 2px solid #00D4FF;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 10px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #333;
                color: white;
                selection-background-color: #00D4FF;
                border: 1px solid #444;
            }
            
            QPushButton {
                background-color: #00D4FF;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #00B8E6;
            }
            
            QPushButton:pressed {
                background-color: #0099CC;
            }
            
            QTableWidget {
                background-color: #2b2b2b;
                color: white;
                gridline-color: #444;
                border: 1px solid #444;
                border-radius: 5px;
                alternate-background-color: #2b2b2b;
            }
            
            QTableWidget::item {
                padding: 8px;
                background-color: #2b2b2b;
            }
            
            QTableWidget::item:alternate {
                background-color: #252525;
            }
            
            QTableWidget::item:selected {
                background-color: #00D4FF;
                color: white;
            }
            
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 8px;
                border: 1px solid #444;
                font-weight: bold;
            }
            
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
            
            QScrollBar:horizontal {
                background-color: #2b2b2b;
                height: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #555;
                border-radius: 6px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #666;
            }
        """)


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for modern look
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
