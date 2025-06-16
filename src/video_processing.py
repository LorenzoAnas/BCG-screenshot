import cv2
import os

def extract_screenshot(video_path, output_path, timestamp_seconds=13):
    """
    Extract a screenshot from a video at a specific timestamp.
    
    Args:
        video_path (str): Path to the input video file
        output_path (str): Path where the screenshot will be saved
        timestamp_seconds (int): Timestamp in seconds to extract the frame
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return False
    
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        return False
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    # Check if timestamp is within video duration
    if timestamp_seconds > duration:
        print(f"Warning: Timestamp {timestamp_seconds}s exceeds video duration {duration:.2f}s, using last frame")
        timestamp_seconds = max(0, duration - 1)
    
    # Calculate frame number for the timestamp
    frame_number = int(timestamp_seconds * fps)
    
    # Set video position to the desired frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    # Read the frame
    ret, frame = cap.read()
    
    if not ret:
        print(f"Error: Could not read frame at timestamp {timestamp_seconds}s")
        cap.release()
        return False
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save the frame as an image
    success = cv2.imwrite(output_path, frame)
    
    if success:
        print(f"Screenshot saved: {os.path.basename(output_path)}")
    else:
        print(f"Error: Could not save screenshot to: {output_path}")
    
    # Release the video capture object
    cap.release()
    
    return success
