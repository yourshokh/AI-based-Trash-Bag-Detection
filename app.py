


from flask import Flask, render_template, request, send_from_directory
from ultralytics import YOLO
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from collections import Counter
from datetime import datetime
import requests

# Initialize Flask app
app = Flask(__name__)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///upload_history.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Define the Database Model
class TrashHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(255), nullable=False)
    trash_type = db.Column(db.String(50), nullable=False)
    trash_bag_number = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)

# Create the database and tables
with app.app_context():
    db.create_all()

# Folder to save uploaded images
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
OUTPUT_FOLDER = os.path.join(os.getcwd(), "outputs")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# Ensure the uploads and outputs directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Load your YOLO model
model = YOLO(r"D:\capstone\trashbag_modelv11\runs\detect\train7\weights\best.pt")  # Replace with your model's path

# Class names as per your YOLO model
class_names = ['Food-garbage', 'Gunnysack', 'Non-Compliant', 'Other', 'Paid-Bag', 'Recycling']

# Separate variables for history and map data
map_upload_history = []  # For map rendering
upload_history_historypage = []  # For history page

# Function to get address from KakaoMap
def get_address_from_coordinates_kakao(latitude, longitude):
    api_key = "940ec600d473beb6137e9ed687297f71"  # Use your REST API key
    url = f"https://dapi.kakao.com/v2/local/geo/coord2address.json?x={longitude}&y={latitude}"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    response = requests.get(url, headers=headers)
    data = response.json()

    if "documents" in data and len(data["documents"]) > 0:
        # Return the address from the API response
        address_info = data["documents"][0]["address"]
        return address_info["address_name"]
    else:
        return "Address not found"

# Route to serve images from the outputs folder
@app.route('/outputs/<filename>')
def serve_output_image(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route("/", methods=["GET", "POST"])
def index():
    detection_results = None
    location = None
    timestamp = None
    output_image_name = None  # To store the name of the output image

    if request.method == "POST":
        # Handle file upload and object detection
        if "file" in request.files:
            file = request.files["file"]
            if file.filename != "":  # Check if a file is selected
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)

                # Perform object detection using YOLO
                results = model(file_path)
                detected_classes = [class_names[int(cls)] for cls in results[0].boxes.cls]
                class_counts = Counter(detected_classes)
                detection_results = ", ".join([f"{count} {cls}" for cls, count in class_counts.items()])

                # Save output image with bounding boxes
                output_image_name = filename  # Assuming output image is saved with the same name
                output_image_path = os.path.join(app.config["OUTPUT_FOLDER"], output_image_name)

                # Save the output image to 'outputs' folder (assumed functionality)
                results[0].save(output_image_path)  # Save the output with bounding boxes

        # Handle location and timestamp
        if "latitude" in request.form and "longitude" in request.form:
            latitude = float(request.form.get("latitude"))
            longitude = float(request.form.get("longitude"))

            # Get human-readable address using KakaoMap API
            location = get_address_from_coordinates_kakao(latitude, longitude)

            # Add current timestamp
            now = datetime.now()
            timestamp = now.strftime("%I:%M %p %m/%d/%Y")

            # Save the upload data in history
            upload_data = {
                "upload_number": len(map_upload_history) + 1,
                "response": detection_results,
                "location": location,
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": timestamp,
            }
            map_upload_history.append(upload_data)  # Store data for map rendering

            # Split the response by trash types for history page
            trash_items = detection_results.split(", ")
            for item in trash_items:
                count, trash_type = item.split(" ", 1)  # Split the count and the trash type
                # Save each row to the database for history page
                new_entry = TrashHistory(
                    location=location,
                    trash_type=trash_type,
                    trash_bag_number=int(count),
                    timestamp=timestamp
                )
                db.session.add(new_entry)
                db.session.commit()

                # Save the data for history page in a separate list
                upload_history_historypage.append({
                    "location": location,
                    "trash_type": trash_type,
                    "trash_bag_number": int(count),
                    "timestamp": timestamp
                })

    return render_template("index.html", detection_results=detection_results, location=location, timestamp=timestamp, output_image_name=output_image_name)

@app.route("/history")
def history():
    # Display data for the history page
    return render_template("history.html", upload_history=upload_history_historypage)

@app.route("/map")
def map_view():
    # Pass map-specific history data (as JSON) to the map page
    return render_template("map.html", upload_history=map_upload_history)

@app.route("/statistics", methods=["GET", "POST"])
def statistics():
    if request.method == "POST":
        # Get selected trash types from the form
        selected_trash_types = request.form.getlist("trash_types")  # Fetch selected checkboxes
        
        if selected_trash_types:
            # Filter data based on selected trash types
            filtered_data = TrashHistory.query.filter(TrashHistory.trash_type.in_(selected_trash_types)).all()
        else:
            # Fetch all data if no filters are applied
            filtered_data = TrashHistory.query.all()
    else:
        # GET request: show all data
        filtered_data = TrashHistory.query.all()

    return render_template("statistics.html", all_data=filtered_data, trash_types=class_names)


if __name__ == "__main__":
    app.run(debug=True)
