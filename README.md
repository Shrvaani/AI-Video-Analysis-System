# AI Video Analysis System

A comprehensive Streamlit-based application for real-time video analysis using YOLOv8, featuring person detection, identification, and payment detection capabilities.

## Features

### Core Functionality
- **Person Detection**: Real-time detection and tracking of persons in video streams
- **Person Identification**: Cross-session person identification using facial recognition
- **Payment Detection**: Automated detection of cash and card payment transactions
- **Multi-Modal Processing**: Support for detection, identification, and payment detection workflows

### User Interface
- **Modern Web Interface**: Clean, responsive Streamlit-based UI with dark/light theme support
- **Real-time Processing**: Live video processing with progress indicators and statistics
- **Session Management**: Comprehensive session tracking and control
- **Data Visualization**: Interactive pie charts and detailed statistics overview
- **Historical Data**: Access to previously processed sessions with detailed summaries

### Technical Features
- **Frame-by-Frame Analysis**: Detailed processing with frame-level statistics
- **Session Persistence**: Automatic saving and retrieval of processing sessions
- **Hash-based Tracking**: Unique video identification using MD5 hashing
- **Error Handling**: Robust error handling for video format and processing issues

## Prerequisites

- Python 3.8 or higher
- OpenCV
- YOLOv8
- Streamlit
- Plotly
- Pandas
- NumPy

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Object_Detection
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install YOLOv8**
   ```bash
   pip install ultralytics
   ```

## Usage

### Starting the Application

1. **Run the Streamlit app**
   ```bash
   streamlit run app.py
   ```

2. **Access the application**
   - Local URL: `http://localhost:8501`
   - Network URL: `http://your-ip:8501`

### Workflow Modes

#### 1. Detect & Identify Mode
- **Purpose**: Detect persons and identify them across sessions
- **Process**: 
  1. Upload video file
  2. Select "Detect & Identify" workflow
  3. Monitor real-time processing
  4. View detection summary with person counts

#### 2. Detect Mode
- **Purpose**: Basic person detection and tracking
- **Process**:
  1. Upload video file
  2. Select "Detect" workflow
  3. Track unique persons in video
  4. Generate detection statistics

#### 3. Detect, Identify & Payment Mode
- **Purpose**: Complete analysis including payment detection
- **Process**:
  1. Upload video file
  2. Select "Detect, Identify & Payment" workflow
  3. Process persons and payment transactions
  4. View comprehensive analysis results

### Understanding the Count System

The application uses a **session-based counting system**:

- **Count = 1**: Person appeared in 1 processing session
- **Count = 2**: Person appeared in 2 processing sessions
- **Count = 3**: Person appeared in 3 processing sessions

This differs from frame-based counting and provides more meaningful insights into person appearances across different processing modes.

## Data Structure

### Directory Structure
```
Object_Detection/
├── app.py                          # Main Streamlit application
├── detection_logic.py              # Person detection implementation
├── identification_logic.py         # Person identification logic
├── payment_detection_logic.py      # Payment detection module
├── known_faces/                    # Stored face data
│   ├── Detected people/            # Detection session data
│   └── Identified people/          # Identification session data
├── temp/                          # Temporary video storage
└── video_hashes.json              # Video hash tracking
```

### Session Data
- **Session ID**: Unique 8-character identifier for each processing session
- **Person ID**: Unique identifier for each detected person
- **Frame Data**: Individual frame captures for each person
- **Statistics**: Comprehensive processing statistics and metrics

## Key Components

### 1. Main Application (`app.py`)
- Streamlit interface setup and configuration
- Session state management
- Workflow control and routing
- Data visualization and statistics display

### 2. Detection Logic (`detection_logic.py`)
- YOLOv8-based person detection
- Real-time tracking and identification
- Frame capture and storage
- Person registry management

### 3. Identification Logic (`identification_logic.py`)
- Cross-session person identification
- Facial feature comparison
- Session-based counting system
- Historical data analysis

### 4. Payment Detection (`payment_detection_logic.py`)
- Cash and card payment detection
- Transaction analysis and reporting
- Payment statistics generation

## Configuration

### Customization Options
- **Max Proximity Distance**: Adjust person tracking sensitivity
- **Max Frame Gap**: Configure re-identification parameters
- **Similarity Threshold**: Modify identification accuracy settings

### Theme Support
- **Light Theme**: Default clean interface
- **Dark Theme**: Automatic detection and styling
- **Custom CSS**: Modern gradient styling and responsive design

## Statistics and Analytics

### Real-time Metrics
- **Total Unique Persons**: Number of unique persons detected
- **Persons in Current Frame**: Real-time frame analysis
- **Total Detections**: Cumulative detection count

### Historical Data
- **Session Overview**: Complete session history
- **Person Statistics**: Individual person appearance tracking
- **Processing Summary**: Detailed analysis results

### Visualization
- **Pie Charts**: Interactive statistics overview
- **Data Tables**: Detailed person and session information
- **Progress Indicators**: Real-time processing feedback

## Troubleshooting

### Common Issues

1. **Video Format Errors**
   - Ensure video files are in supported formats (MP4, AVI, MOV)
   - Check video file integrity and codec compatibility

2. **Processing Performance**
   - Adjust YOLOv8 model parameters for better performance
   - Consider video resolution and frame rate optimization

3. **Session State Issues**
   - Use the "Clear All Data" button to reset application state
   - Restart the application if session conflicts occur

### Error Messages
- **"Cannot open video file"**: Check file format and path
- **"No active session"**: Upload a video to start processing
- **"Indentation errors"**: Ensure proper Python syntax

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


---

**Note**: This application is designed for research and development purposes. Ensure compliance with local privacy and data protection regulations when processing video content.


