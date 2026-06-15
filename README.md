# ROI Bounding Box Tool for WhisperX SceneDetect

A simple Python Tkinter desktop application for drawing resizable bounding boxes on video frames to define Region of Interest (ROI) coordinates for WhisperX SceneDetect.

## Features

- **Load Video Files** - Open any video format supported by OpenCV (MP4, MKV, MOV, AVI, etc.)
- **Video Scrubbing** - Drag slider or use keyboard to navigate through video
- **Playback Control** - Play/pause video with frame-by-frame navigation
- **Draw & Resize Bounding Box** - Click and drag to define the ROI area
- **Live Preview** - See the cropped region in real-time
- **Zoom & Pan** - Zoom in/out for precise coordinate selection
- **Multiple ROI Storage** - Save different ROIs for different sections of video
- **ROI History** - View all saved ROIs with timestamps
- **Export ROIs** - Save ROI history to JSON file
- **Multiple Output Formats** - Copy to clipboard and save to files
- **YAML Configuration** - Easy config file for defaults and settings

## Installation

1. **Install Python** (3.8+)

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Quick Start (with config file)

1. **Edit `roi_config.yaml`** - Set your video path:
   ```yaml
   video_path: "C:/path/to/your/video.mp4"
   ```

2. **Run the tool:**
   ```bash
   python roi_tool.py
   ```

### Command Line Usage

Load a video directly without editing config:
```bash
python roi_tool.py --video "C:/path/to/video.mp4"
```

Use a custom config file:
```bash
python roi_tool.py --config "custom_config.yaml" --video "path/to/video.mp4"
```

## How to Use the Tool

1. **Load Video** - Click "Load Video" button or set in config
2. **Draw ROI** - Click and drag on the video to create a bounding box
3. **Adjust** - Resize the box by dragging corners/edges
4. **Preview** - See the cropped area in the preview panel on the right
5. **Zoom** - Use "Zoom In/Out" or mouse wheel for precise coordinates
6. **Save** - Click "Save ROI" to output coordinates

## Output & Storage

### Single ROI (Clipboard)
When you save, coordinates are copied in WhisperX `SCENE_ROI` format:
```
x1 y1 x2 y2
```

Example:
```
184 10 1941 1096
```

### Multiple ROIs (History)
The tool stores ROIs for different frames/timestamps:
- **ROI History Panel** - Shows all saved ROIs with timestamps
- **Auto-load** - Switches to nearby ROI when you seek to a frame within 1 second
- **Export** - Save entire ROI history to JSON file

**Files created:**
- `roi_history.json` - JSON file with all saved ROIs (use Export button)
- Clipboard - Last ROI coordinates for pasting

## Workflow for Multiple Scenes

1. **Load video**
2. **Navigate to first scene** - Use slider or arrow keys
3. **Draw ROI** - Click and drag to define bounding box
4. **Click "Save ROI"** - Stores ROI for that frame
5. **Jump to next scene** - Use slider or playback buttons
6. **Repeat steps 3-4** for each scene
7. **Click "Export"** - Saves all ROIs to JSON with timestamps
8. **Use JSON** - Reference different ROI coordinates for each section

## Configuration File (`roi_config.yaml`)

Key settings:

```yaml
# Video to load
video_path: null  # Set to your video path, or use --video command line arg

# Initial ROI (optional)
initial_roi: null

# Window size
window:
  width: 1400
  height: 900

# Display settings
display:
  zoom: 1.0
  grid_spacing: 0  # Snap-to-grid increment (0 = disabled)

# Output options
output:
  output_file: "roi.txt"
  copy_to_clipboard: true

# UI appearance
ui:
  box_color: "#00FF00"
  box_thickness: 2
  preview_opacity: 0.3
```

## Keyboard & Mouse Controls

### Mouse
| Action | Control |
|--------|---------|
| Draw ROI | Click + drag |
| Zoom In | Mouse wheel up or "Zoom In" button |
| Zoom Out | Mouse wheel down or "Zoom Out" button |

### Keyboard
| Action | Key |
|--------|-----|
| Next Frame | Right Arrow |
| Previous Frame | Left Arrow |
| Jump +1 Second | Up Arrow |
| Jump -1 Second | Down Arrow |
| Play/Pause | Space |
| Go to Start | Home |
| Go to End | End |

### Buttons
| Action | Button |
|--------|--------|
| Fit Window | "Fit Window" |
| Reset ROI | "Reset ROI" |
| Save ROI | "Save ROI" (green) |
| Clear History | "Clear History" |

## Integration with WhisperX

Once you have your ROI coordinates, use them with WhisperX:

### Via Environment Variable
```bash
export SCENE_ROI="184 10 1941 1096"
docker compose run --rm scenes
```

### Via Config File
Edit `config.yaml` in WhisperX:
```yaml
scenes:
  roi: "184 10 1941 1096"
```

## Troubleshooting

**"Failed to open video"**
- Ensure the video path is correct and the file exists
- Check that the video format is supported by OpenCV

**"No image display"**
- Click "Fit Window" button to auto-scale video to window
- Video may be loading - wait a moment

**Clipboard not working**
- Install pyperclip: `pip install pyperclip`
- On Linux, may need xclip: `sudo apt-get install xclip`

**Performance issues with large videos**
- Zoom out to see full frame
- Use "Fit Window" for faster rendering

## File Structure

```
D:\Claude\CalculateROI\
├── roi_tool.py          # Main application
├── roi_config.yaml      # Configuration file
├── requirements.txt     # Python dependencies
├── roi.txt              # Output file (created after saving)
└── README.md            # This file
```

## Author Notes

- Built with Tkinter (no external GUI dependencies beyond OpenCV & PIL)
- Coordinates are in pixel format (0,0 is top-left)
- ROI is defined as: `(top-left-x, top-left-y, bottom-right-x, bottom-right-y)`
- Works on Windows, macOS, and Linux

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Edit `roi_config.yaml` with your video path
3. Run: `python roi_tool.py`
4. Draw your ROI and save!
