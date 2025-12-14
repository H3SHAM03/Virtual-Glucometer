# 🏥 Glucometer Analyzer - Professional Medical Device Simulation

A comprehensive PyQt5 desktop application for advanced glucose level monitoring, analysis, and patient management with persistent database storage and professional reporting capabilities.

## ✨ Features

### 📊 **Monitor Tab** (Real-time Glucose Monitoring)
#### Input Panel (Left)
- Numeric input field for glucose values (mg/dL)
- Patient condition dropdown (Normal, Diabetic, Fasting)
- Analyze button to process readings
- Clear history button with dark-themed confirmation
- Reference ranges information panel

#### Status Display (Center)
- Large colored indicator showing current glucose value
- Status text (NORMAL, WARNING, CRITICAL)
- Color-coded alerts (Green, Yellow, Orange, Red)
- Detailed message based on reading and condition
- Timestamp of last reading
- Flashing border animation for critical conditions

#### Trend Graph (Right)
- Real-time matplotlib plot with dark theme
- Shows last 20 glucose readings
- Color-coded data points matching status
- Reference zones for normal/warning/critical ranges
- Automatic scaling and updates

#### History Table (Bottom)
- Complete log of all measurements
- Columns: Timestamp, Glucose Value, Status, Condition
- Color-coded status indicators
- Dark theme with alternating row colors
- Sortable and scrollable

### 📈 **Statistics Tab** (Advanced Analytics)
- **Real-time Statistical Dashboard** with 13 key metrics:
  - Total readings count
  - Average glucose level
  - Median glucose level
  - Standard deviation
  - Minimum value
  - Maximum value
  - Time in Range percentage
  - Estimated A1C (calculated from average)
  - Critical Low count
  - Warning Low count
  - Normal readings count
  - Warning High count
  - Critical High count
- Statistics calculated for last 30 days
- Visual metric cards with dark theme
- Refresh button for manual updates

### 🎯 **Goals Tab** (Goal Tracking & Management)
- Create custom health goals
- Pre-defined goal templates:
  - Maintain Time in Range >80%
  - Keep Average Below 140 mg/dL
  - Reduce Critical Events
  - Take 100 Readings
  - 30-Day Consistency
- Visual progress bars for each goal
- Target vs. Current value tracking
- Achievement status indicators
- Goal start and end dates
- Add new goals with custom targets

### 📉 **Advanced Graphs Tab** (Data Visualization)
- **Histogram**: Distribution of glucose readings
- **Box Plot**: Statistical spread analysis
- Interactive graph type selection
- Update button for on-demand rendering
- Last 30 days data visualization

### 👥 **Multi-Patient Management**
- Add unlimited patient profiles
- Patient information storage:
  - Name
  - Age
  - Diabetes type (Normal, Type 1, Type 2, Gestational, Pre-diabetic)
  - Custom target ranges
- Quick patient switching via dropdown
- Isolated data per patient
- Default patient auto-created on first run

### 💾 **Database Persistence** (SQLite)
- Automatic data saving for all readings
- Patient profile storage
- Goals and progress tracking
- Persistent across sessions
- Three-table schema with foreign keys:
  - `readings`: All glucose measurements
  - `patients`: Patient profiles and settings
  - `goals`: Health goals and targets

### 📤 **Data Export** (Multiple Formats)
Export your data in three professional formats:

#### 1. **CSV Export**
Comma-separated values for spreadsheet analysis
```csv
Timestamp,Glucose (mg/dL),Status,Condition
2025-12-14 10:30:45,120.0,NORMAL,Normal
2025-12-14 11:15:22,165.0,WARNING HIGH,Diabetic
```

#### 2. **JSON Export**
Structured data for programmatic access
```json
{
  "patient_name": "John Doe",
  "export_date": "2025-12-14",
  "readings": [
    {
      "timestamp": "2025-12-14 10:30:45",
      "glucose_value": 120.0,
      "status": "NORMAL",
      "condition": "Normal"
    }
  ]
}
```

#### 3. **PDF Report**
Professional medical report with:
- Patient information
- Export date and time
- Statistical summary (average, median, min, max)
- Complete readings table
- Professional formatting with ReportLab

### 🌓 **Theme Toggle**
- Switch between Dark and Light themes
- Consistent styling across all components
- Theme applied to all dialogs and message boxes
- Preserves user preference during session

### 🔊 **Enhanced Audio Alerts**
- **Critical conditions**: 3 consecutive beeps at 1200Hz
- **Warning conditions**: Single beep at 800Hz
- Visual flashing border (red/yellow) for 5 seconds
- Automatic alarm stop after threshold period

## 📋 Glucose Classification Rules

### Clinical Thresholds (ADA/ISO 15197 Compliant)

| Range | Status | Color | ADA Level | Action |
|-------|--------|-------|-----------|--------|
| < 54 mg/dL | **CRITICAL LOW** | Red | Level 3 | 🚨 Severe hypoglycemia - Immediate treatment required |
| 54-70 mg/dL | **WARNING LOW** | Orange | Level 1-2 | ⚠️ Hypoglycemia - Consume fast-acting carbs |
| 70-140 mg/dL | **NORMAL** | Green | Target Range | ✅ Optimal glucose level |
| 140-180 mg/dL | **WARNING HIGH** | Orange | Elevated | ⚠️ Hyperglycemia - Monitor and adjust |
| > 180 mg/dL | **CRITICAL HIGH** | Red | Severe | 🚨 Severe hyperglycemia - Seek medical attention |

### Standards Compliance

**ISO 15197:2013 - In Vitro Diagnostic Test Systems**
- Accuracy requirements for blood glucose monitoring systems
- For glucose < 100 mg/dL: System accuracy must be ±15 mg/dL
- For glucose ≥ 100 mg/dL: System accuracy must be ±15%
- 95% of measurements must meet these criteria

**ADA Clinical Practice Guidelines**
- Critical low threshold: < 54 mg/dL (Level 3 hypoglycemia)
- Hypoglycemia alert: < 70 mg/dL (Level 1-2)
- Normal fasting glucose: 70-100 mg/dL
- Normal postprandial glucose: < 140 mg/dL (2 hours after meal)
- Hyperglycemia threshold: > 180 mg/dL

**A1C Estimation Formula**
- Based on ADAG (A1C-Derived Average Glucose) study
- Formula: `A1C ≈ (average_glucose + 46.7) / 28.7`
- Provides estimated 3-month average from recent readings

## 🚀 How to Use

### Basic Workflow
1. **Select Patient**: Choose from dropdown or add new patient
2. **Enter Glucose Value**: Type a numeric value (0-1000 mg/dL)
3. **Select Condition**: Choose patient condition (Normal, Diabetic, Fasting)
4. **Analyze**: Click "ANALYZE" button or press Enter
5. **Review Results**: Check status display for classification and alerts
6. **Monitor Trends**: View the real-time graph for patterns
7. **Check Statistics**: Navigate to Statistics tab for detailed metrics
8. **Set Goals**: Create health goals in Goals tab
9. **Export Data**: Use Export button for CSV/JSON/PDF reports

### Advanced Features
- **Switch Patients**: Use patient dropdown in header
- **Add Patient**: Click "New Patient" button, fill details
- **View Statistics**: Switch to Statistics tab, click Refresh
- **Create Goals**: Go to Goals tab, click "Add New Goal"
- **Advanced Analysis**: Use Advanced Graphs tab for histograms/box plots
- **Toggle Theme**: Click theme button in header (🌙/☀️)
- **Export Data**: Click Export button, choose format
- **Clear History**: Click "CLEAR HISTORY" button (confirmation required)

## 💻 Installation & Running

### Prerequisites

#### Option 1: Install from requirements.txt (Recommended)
```bash
pip install -r requirements.txt
```

#### Option 2: Install manually
```bash
pip install PyQt5 matplotlib reportlab
```

### Run Application
```bash
python lab.py
```

The application will automatically:
- Create `glucometer_data.db` SQLite database
- Initialize database schema
- Create a default patient profile
- Load existing data if available

## 📦 Requirements

### Core Dependencies
- **Python 3.8+**
- **PyQt5** (5.15+): GUI framework
- **matplotlib** (3.0+): Data visualization
- **reportlab** (3.5+): PDF generation

### Standard Library
- **sqlite3**: Database management
- **csv**: CSV export
- **json**: JSON export
- **datetime**: Timestamp handling
- **statistics**: Statistical calculations
- **winsound** (Windows only): Audio alerts

## 🏗️ Architecture & Code Structure

### Classes

#### **DatabaseManager**
- SQLite database operations
- Three-table schema (readings, patients, goals)
- CRUD operations for all entities
- Foreign key relationships
- Data integrity management

#### **StatisticsCalculator**
- Statistical analysis engine
- 13 metrics calculation
- A1C estimation formula: `(avg_glucose + 46.7) / 28.7`
- Time-in-range percentage
- Status distribution counts

#### **GlucoseAnalyzer**
- Core medical analysis logic
- Five-level classification system
- Alarm severity determination
- Standardized result dictionaries
- Separated from UI for testability

#### **TrendPlotWidget**
- Matplotlib integration with Qt5Agg backend
- Custom QWidget for embedded plotting
- Real-time graph updates
- Color-coded data points
- Reference zones visualization
- Dark theme styling
- Last 20 readings display

#### **MainWindow**
- Main application controller
- Tab-based UI management (4 tabs)
- Patient profile management
- Database integration
- Theme switching
- Export functionality
- Alarm and animation handling
- Event-driven architecture

### Database Schema

```sql
-- Patients table
CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    age INTEGER,
    diabetes_type TEXT,
    target_min REAL DEFAULT 70,
    target_max REAL DEFAULT 140,
    created_date TEXT
);

-- Readings table
CREATE TABLE readings (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    glucose_value REAL,
    status TEXT,
    condition TEXT,
    timestamp TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- Goals table
CREATE TABLE goals (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    goal_type TEXT,
    target_value REAL,
    current_value REAL DEFAULT 0,
    start_date TEXT,
    end_date TEXT,
    achieved INTEGER DEFAULT 0,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);
```

## 🎨 Design Principles

- **Object-Oriented Programming**: Clean separation of concerns
- **MVC-like Pattern**: Model (Database) → Controller (MainWindow) → View (Widgets)
- **Dark Theme UI**: Professional medical device aesthetics
- **Responsive Layout**: Adapts to window resizing
- **User-Friendly**: Clear visual feedback and intuitive controls
- **Data Persistence**: All data automatically saved
- **Extensible Architecture**: Easy to add new features
- **Standards Compliance**: ISO 15197:2013 and ADA guidelines
- **Medical Device Standards**: Realistic behavior and alerts

## 🧪 Testing Examples

### Try These Values (ISO 15197/ADA Compliant)

| Value | Expected Result | ADA Level | Features Demonstrated |
|-------|----------------|-----------|----------------------|
| **45 mg/dL** | 🔴 Critical Low | Level 3 | Severe hypoglycemia, 3 beeps, flashing border |
| **60 mg/dL** | 🟠 Warning Low | Level 1-2 | Hypoglycemia, single beep, orange alert |
| **85 mg/dL** | 🟢 Normal (Fasting) | Target | Green status, no alarm, optimal fasting level |
| **120 mg/dL** | 🟢 Normal (Post-meal) | Target | Green status, no alarm, good postprandial |
| **160 mg/dL** | 🟠 Warning High | Elevated | Hyperglycemia, single beep, orange alert |
| **200 mg/dL** | 🔴 Critical High | Severe | Severe hyperglycemia, 3 beeps, flashing border |

### ISO 15197 Accuracy Test Values

Test these values to verify accuracy tolerance:

| Reference Value | Acceptable Range | ISO 15197 Requirement |
|----------------|------------------|----------------------|
| **50 mg/dL** | 35-65 mg/dL | ±15 mg/dL (< 100 mg/dL) |
| **75 mg/dL** | 60-90 mg/dL | ±15 mg/dL (< 100 mg/dL) |
| **100 mg/dL** | 85-115 mg/dL | ±15% (≥ 100 mg/dL) |
| **150 mg/dL** | 127.5-172.5 mg/dL | ±15% (≥ 100 mg/dL) |
| **300 mg/dL** | 255-345 mg/dL | ±15% (≥ 100 mg/dL) |

### Test Workflows

1. **Patient Management**:
   - Add patient "John Doe", age 45, Type 2 diabetes
   - Add readings for John
   - Switch to default patient
   - Verify data isolation

2. **Statistics**:
   - Add 10+ readings with varied values
   - Check Statistics tab
   - Verify average, median, A1C calculation

3. **Export**:
   - Add several readings
   - Export to CSV → Open in Excel
   - Export to JSON → Verify structure
   - Export to PDF → Check formatting

4. **Goals**:
   - Create goal: "Time in Range >80%"
   - Add readings in target range
   - Check progress bar update

## 📝 Export Examples

### Sample CSV Output
```csv
Timestamp,Glucose (mg/dL),Status,Condition
2025-12-14 10:30:45,120.0,NORMAL,Normal
2025-12-14 11:15:22,165.0,WARNING HIGH,Diabetic
2025-12-14 13:45:10,95.0,NORMAL,Fasting
2025-12-14 15:20:33,185.0,CRITICAL HIGH,Normal
```

### Sample JSON Output
```json
{
  "patient_name": "John Doe",
  "export_date": "2025-12-14 16:30:22",
  "total_readings": 4,
  "readings": [
    {
      "timestamp": "2025-12-14 10:30:45",
      "glucose_value": 120.0,
      "status": "NORMAL",
      "condition": "Normal"
    },
    {
      "timestamp": "2025-12-14 11:15:22",
      "glucose_value": 165.0,
      "status": "WARNING HIGH",
      "condition": "Diabetic"
    }
  ]
}
```

### Sample PDF Report Structure
```
╔══════════════════════════════════════════════╗
║   GLUCOSE MONITORING REPORT                  ║
║   Patient: John Doe                          ║
║   Export Date: 2025-12-14 16:30:22           ║
╠══════════════════════════════════════════════╣
║   STATISTICS SUMMARY                         ║
║   Average: 142.5 mg/dL                       ║
║   Median: 142.5 mg/dL                        ║
║   Min: 95.0 mg/dL | Max: 185.0 mg/dL         ║
╠══════════════════════════════════════════════╣
║   READINGS TABLE                             ║
║   [Last 50 readings with timestamp,          ║
║    glucose value, status, and condition]     ║
╚══════════════════════════════════════════════╝
```

## 📌 Important Notes

### General
- **Cross-Platform**: Works on Windows, macOS, Linux (audio alerts Windows-only)
- **Database**: SQLite file `glucometer_data.db` created in application directory
- **Data Persistence**: All data saved automatically, no manual save required
- **History Clearing**: Only clears current patient's display, database retained
- **Theme Preference**: Resets to dark theme on restart
- **Graph Limit**: Displays last 20 readings for optimal performance
- **Statistics Period**: Calculated for last 30 days by default
- **Export Formats**: All three formats include same data, different structures

### Standards Compliance
- **ISO 15197:2013**: Clinical thresholds align with international standards for blood glucose monitoring systems
- **ADA Guidelines**: Classification follows American Diabetes Association clinical practice recommendations
- **Severe Hypoglycemia**: Updated threshold from 50 to 54 mg/dL (ADA Level 3)
- **A1C Estimation**: Uses ADAG study formula for 3-month average glucose estimation
- **Educational Purpose**: This is a simulation tool for learning, not for clinical diagnosis
- **Accuracy Note**: Real glucometers must meet ISO 15197 ±15 mg/dL or ±15% accuracy requirements

## 🤝 Contributing

This is a medical device simulation for educational purposes. Contributions welcome for:
- Additional graph types (scatter plot, heatmap, trends)
- Import functionality (CSV/JSON)
- Data backup/restore
- Report templates
- Multi-language support
- A1C tracking over time
- Medication logging

## 📄 License

Educational project for CUFE Standards Lab 2.

## 🔗 Technologies Used

- **PyQt5**: Cross-platform GUI framework
- **Matplotlib**: Scientific visualization
- **SQLite**: Embedded database
- **ReportLab**: PDF generation
- **Qt5Agg**: Matplotlib Qt5 backend
