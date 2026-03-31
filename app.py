import streamlit as st
import os
import re
import requests
import yt_dlp
from moviepy import VideoFileClip
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="YouTube to GIF", page_icon="🎥")

st.title("YouTube to GIF Converter")


# --- Custom CSS (Claymorphism & Vibrant) ---
def inject_custom_css():
    st.markdown(
        """
        <style>
        /* Base Background and Fonts */
        .stApp {
            background-color: #f0f4f8; /* Soft blue-grey background */
            font-family: 'Inter', sans-serif;
            color: #333333;
        }

        /* Main Container Styling */
        .main .block-container {
            padding: 2rem;
            max-width: 800px;
            background: #ffffff;
            border-radius: 24px;
            box-shadow:  10px 10px 20px #d1d9e6,
                         -10px -10px 20px #ffffff;
            margin-top: 2rem;
            margin-bottom: 2rem;
        }

        /* Headings */
        h1, h2, h3 {
            color: #2b3a4a;
            font-weight: 800;
        }

        /* Input Fields (Text & Number) */
        .stTextInput>div>div>input, .stNumberInput>div>div>input {
            background-color: #e6eef5 !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
            box-shadow: inset 4px 4px 8px #c8d5e1,
                        inset -4px -4px 8px #ffffff !important;
            color: #333 !important;
            font-weight: 500 !important;
        }

        .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
            box-shadow: inset 6px 6px 12px #c8d5e1,
                        inset -6px -6px 12px #ffffff,
                        0 0 0 3px rgba(66, 153, 225, 0.5) !important;
        }

        /* Buttons (Vibrant & Claymorphic) */
        .stButton>button {
            background-color: #ff6b6b !important; /* Vibrant Red/Pink */
            color: white !important;
            border: none !important;
            border-radius: 16px !important;
            padding: 12px 24px !important;
            font-weight: 700 !important;
            font-size: 16px !important;
            box-shadow:  6px 6px 12px #d1d9e6,
                         -6px -6px 12px #ffffff,
                         inset 2px 2px 4px rgba(255, 255, 255, 0.4),
                         inset -2px -2px 4px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.2s ease-in-out !important;
            width: 100% !important;
        }

        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow:  8px 8px 16px #d1d9e6,
                         -8px -8px 16px #ffffff,
                         inset 2px 2px 4px rgba(255, 255, 255, 0.4),
                         inset -2px -2px 4px rgba(0, 0, 0, 0.1) !important;
            background-color: #ff5252 !important;
        }

        .stButton>button:active {
            transform: translateY(2px);
            box-shadow: inset 4px 4px 8px rgba(0, 0, 0, 0.2),
                        inset -4px -4px 8px rgba(255, 255, 255, 0.2) !important;
        }

        /* Download Buttons specific colors */
        .stDownloadButton>button {
            background-color: #4ecdc4 !important; /* Vibrant Teal */
        }
        .stDownloadButton>button:hover {
            background-color: #45b7af !important;
        }

        /* Disabled Buttons */
        .stButton>button:disabled {
            background-color: #a0aec0 !important;
            color: #cbd5e0 !important;
            box-shadow: inset 4px 4px 8px #8a96a6,
                        inset -4px -4px 8px #b6c6da !important;
            transform: none;
            cursor: not-allowed;
        }

        /* Alerts and Info Boxes */
        .stAlert {
            border-radius: 16px !important;
            border: none !important;
            box-shadow:  4px 4px 8px #d1d9e6,
                         -4px -4px 8px #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

inject_custom_css()

# --- Initialize session state ---
if "mode" not in st.session_state:
    st.session_state.mode = "editing" # editing, preview, processing, result

def download_and_convert(url, start_time, end_time):
    video_path = "temp_video.mp4"
    gif_path = "output.gif"
    high_res_gif_path = "output_high_res.gif"

    # Define a clean download opts
    ydl_opts = {
        'format': 'best',
        'outtmpl': video_path,
        'download_ranges': yt_dlp.utils.download_range_func(None, [(start_time, end_time)]),
        'force_keyframes_at_cuts': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    clip = VideoFileClip(video_path)

    # Clip duration check, just in case download_ranges failed
    duration = end_time - start_time
    if clip.duration > duration:
        clip = clip.subclip(0, duration)

    # Standard GIF
    clip.resize(height=360).write_gif(gif_path, fps=15)

    # High-Res GIF
    clip.write_gif(high_res_gif_path, fps=24)

    clip.close()

    if os.path.exists(video_path):
        os.remove(video_path)

    return gif_path, high_res_gif_path

# --- Editing Mode ---
if st.session_state.mode == "editing":
    st.header("1. Choose a video and segment")

    url = st.text_input("YouTube URL")

    col1, col2 = st.columns(2)
    with col1:
        start_time = st.number_input("Start Time (seconds)", min_value=0, value=0)
    with col2:
        end_time = st.number_input("End Time (seconds)", min_value=1, value=10)

    duration = end_time - start_time

    if duration > 20:
        st.warning(f"Max 20s. You selected {duration}s ({duration - 20}s above limit)")
        can_proceed = False
    elif duration <= 0:
        st.error("End time must be greater than start time.")
        can_proceed = False
    else:
        st.success(f"Selected duration: {duration}s")
        can_proceed = True

    if st.button("Preview", disabled=not can_proceed or not url):
        st.session_state.url = url
        st.session_state.start_time = start_time
        st.session_state.end_time = end_time
        st.session_state.mode = "preview"
        st.rerun()

# --- Preview Mode ---
if st.session_state.mode == "preview":
    st.header("2. Preview Segment")

    url = st.session_state.url
    start_time = st.session_state.start_time
    end_time = st.session_state.end_time

    # Extract video ID for iframe
    video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
    if video_id_match:
        video_id = video_id_match.group(1)
        # Construct embed URL with start and end times
        embed_url = f"https://www.youtube.com/embed/{video_id}?start={start_time}&end={end_time}&autoplay=1"

        st.components.v1.iframe(embed_url, width=640, height=360)
    else:
        st.error("Invalid YouTube URL")
        if st.button("Back"):
            st.session_state.mode = "editing"
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate GIF"):
            st.session_state.mode = "processing"
            st.rerun()
    with col2:
        if st.button("Cancel"):
            st.session_state.mode = "editing"
            st.rerun()

# --- Processing Pipeline ---
if st.session_state.mode == "processing":
    st.header("3. Processing")
    with st.spinner("Downloading and converting to GIF... This may take a minute."):
        try:
            gif_path, high_res_gif_path = download_and_convert(
                st.session_state.url,
                st.session_state.start_time,
                st.session_state.end_time
            )
            st.session_state.gif_path = gif_path
            st.session_state.high_res_gif_path = high_res_gif_path
            st.session_state.mode = "result"
            st.rerun()
        except Exception as e:
            st.error(f"An error occurred: {e}")
            if st.button("Retry"):
                st.session_state.mode = "editing"
                st.rerun()

# --- Result Mode ---
def upload_to_imgur(image_path):
    client_id = os.getenv("IMGUR_CLIENT_ID")
    if not client_id:
        return None, "Imgur Client ID not found. Please set IMGUR_CLIENT_ID in your environment or .env file."

    headers = {"Authorization": f"Client-ID {client_id}"}
    url = "https://api.imgur.com/3/image"

    try:
        with open(image_path, "rb") as image_file:
            response = requests.post(
                url,
                headers=headers,
                files={"image": image_file}
            )

        if response.status_code == 200:
            data = response.json()
            return data["data"]["link"], None
        else:
            return None, f"Imgur API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return None, f"Exception occurred during upload: {str(e)}"

if st.session_state.mode == "result":
    st.header("4. Download or Upload")

    st.image(st.session_state.gif_path, caption="Standard GIF Preview")

    col1, col2 = st.columns(2)
    with col1:
        with open(st.session_state.gif_path, "rb") as file:
            st.download_button(
                label="Download Standard GIF",
                data=file,
                file_name="standard.gif",
                mime="image/gif"
            )

    with col2:
        with open(st.session_state.high_res_gif_path, "rb") as file:
            st.download_button(
                label="Download High-Res GIF",
                data=file,
                file_name="high_res.gif",
                mime="image/gif"
            )

    st.markdown("---")
    st.subheader("Upload to Imgur")
    st.info("By uploading to Imgur, you agree to their terms of service. The image will be publicly accessible via the link.")

    if st.button("Upload Standard GIF to Imgur"):
        with st.spinner("Uploading..."):
            link, error = upload_to_imgur(st.session_state.gif_path)
            if link:
                st.success(f"Upload successful! Link: {link}")
                st.markdown(f"[Open in Imgur]({link})")
            else:
                st.error(error)

    if st.button("Start Over"):
        st.session_state.mode = "editing"

        # Cleanup
        for path in ["output.gif", "output_high_res.gif"]:
            if os.path.exists(path):
                os.remove(path)

        st.rerun()
