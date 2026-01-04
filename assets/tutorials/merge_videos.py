import os
from moviepy import VideoFileClip, AudioFileClip

def merge_audio_video(video_path, audio_path, output_path):
    print(f"Processing {video_path}...")
    if not os.path.exists(video_path):
        print(f"Error: Video not found at {video_path}")
        return
    if not os.path.exists(audio_path):
        print(f"Error: Audio not found at {audio_path}")
        return

    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        
        # MoviePy v2 uses 'with_audio' instead of 'set_audio'
        # and 'with_duration' instead of 'set_duration'
        final_video = video.with_audio(audio)
        
        # Ensure duration matches the shortest stream to avoid errors
        duration = min(video.duration, audio.duration)
        final_video = final_video.with_duration(duration)
        
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        print(f"Successfully created {output_path}")
        
    except Exception as e:
        print(f"Failed to process {video_path}: {e}")

def main():
    base_dir = r"c:\Users\umutc\OneDrive\Masaüstü\ai-trading-coach\assets\tutorials"
    
    tasks = [
        ("dashboard_demo.mp4", "dashboard_voice.mp3", "dashboard_bella.mp4"),
        ("backtest_demo.mp4", "backtest_voice.mp3", "backtest_bella.mp4"),
        ("api_setup_demo.mp4", "api_setup_voice.mp3", "api_setup_bella.mp4"),
        ("ai_chat_demo.webp", "ai_chat_voice.mp3", "ai_chat_final.mp4")
    ]
    
    for v, a, out in tasks:
        v_path = os.path.join(base_dir, v)
        a_path = os.path.join(base_dir, a)
        out_path = os.path.join(base_dir, out)
        
        merge_audio_video(v_path, a_path, out_path)

if __name__ == "__main__":
    main()
