# AI-based-Trash-Bag-Detection

AI-based trash bag detection and counting model with a dashboard website featuring Kakao Map integration.

## Features
- Detect and count trash bags in uploaded photos.
- Display the detected number of trash bags on a map.
- Provide location-specific information for better tracking.

---

## Requirements
Make sure you have the following installed before running the project:
- Python 3.x
- Required Python libraries (installable via `pip` - see below)
- Kakao Map API key (if necessary for the map integration)

---

## Installation & Setup

### 1. Save the `.pt` file
Download and save the trained PyTorch `.pt` file in a convenient location on your system.

---

### 2. Save the Project Files
Ensure the following files are saved together in **one folder**:
- `app.py`  
- Four HTML files (`index.html`, etc.)  
- The `.pt` file saved in step 1.

---

### 3. Edit File Paths
Open the `app.py` file in any text editor and **update the file path** to point to the location of the `.pt` file saved in step 1.

```python
# Example:
model_path = "path_to_your_file/trashbag_model.pt"
