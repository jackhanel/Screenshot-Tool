import cv2
import os


def get_vertical_shift(prev_frame, current_frame):
    h, w, _ = prev_frame.shape
    band_height = 100
    y = h // 2 - band_height // 2

    prev_band = cv2.cvtColor(prev_frame[y : y + band_height, :], cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

    res = cv2.matchTemplate(curr_gray, prev_band, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(res)

    return abs(max_loc[1] - y)


def process_video(video_path, output_folder):
    video = cv2.VideoCapture(video_path)
    success, frame = video.read()
    frame_count = 0
    saved = []
    threshold_pixels = 100
    save_interval = 3

    reference_frame = None
    last_saved_frame_count = -1

    while success and frame is not None:
        should_save = False

        if frame_count == 0:
            should_save = True
        elif frame_count % save_interval == 0 and reference_frame is not None:
            shift = get_vertical_shift(reference_frame, frame)
            if shift >= threshold_pixels:
                should_save = True

        if should_save and frame.size > 0:
            path = os.path.join(output_folder, f"screenshot_{len(saved):02}.jpg")
            cv2.imwrite(path, frame)
            saved.append(path)
            reference_frame = frame.copy()
            last_saved_frame_count = frame_count

        success, frame = video.read()
        frame_count += 1

    if reference_frame is not None and (last_saved_frame_count != frame_count - 1):
        path = os.path.join(output_folder, f"screenshot_{len(saved):02}.jpg")
        cv2.imwrite(path, reference_frame)
        saved.append(path)

    return saved
