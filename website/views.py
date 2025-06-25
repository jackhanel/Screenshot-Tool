from flask import (Blueprint, render_template, request, send_file, session, redirect, url_for)
import os, uuid, shutil
from werkzeug.utils import secure_filename
from .functions import process_video
from zipfile import ZipFile
import tempfile

views = Blueprint("views", __name__)


@views.route("/", methods=["GET", "POST"])
def upload():
    screenshots = []

    if request.method == "POST":
        video = request.files.get("video")
        if video:
            user_id = uuid.uuid4().hex
            session["user_id"] = user_id

            # Create temp directory
            temp_dir = tempfile.mkdtemp(prefix=f"user_{user_id}_")
            upload_path = os.path.join(temp_dir, secure_filename(video.filename))
            video.save(upload_path)

            # Process video and get screenshot paths
            screenshot_paths = process_video(upload_path, temp_dir)
            session["temp_dir"] = temp_dir  # Store for download cleanup

            # Store relative names for download
            screenshots = [os.path.basename(path) for path in screenshot_paths]

    return render_template("index.html", screenshots=screenshots)


@views.route("/preview/<filename>")
def preview_file(filename):
    temp_dir = session.get("temp_dir")
    if not temp_dir:
        return "Session expired", 404

    file_path = os.path.join(temp_dir, filename)
    if not os.path.exists(file_path):
        return "File not found", 404

    return send_file(file_path, mimetype="image/jpeg")


@views.route("/download_all")
def download_all():
    temp_dir = session.get("temp_dir")
    if not temp_dir:
        return "Session expired", 404

    zip_path = os.path.join(temp_dir, "screenshots.zip")
    with ZipFile(zip_path, "w") as zipf:
        for fname in os.listdir(temp_dir):
            if fname.endswith(".jpg"):
                zipf.write(os.path.join(temp_dir, fname), fname)

    # Send zip then delete everything
    response = send_file(zip_path, as_attachment=True)

    @response.call_on_close
    def cleanup():
        shutil.rmtree(temp_dir, ignore_errors=True)

    return response
