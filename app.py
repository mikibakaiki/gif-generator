import os
import re
import subprocess
import sys
import tempfile

import requests
import streamlit as st
import yt_dlp
from dotenv import load_dotenv
from moviepy import VideoFileClip
from streamlit.runtime.scriptrunner import get_script_run_ctx


def _ensure_streamlit_launch_mode():
    """Relaunch the script via `streamlit run` if executed as `python app.py`."""
    if __name__ != "__main__":
        return

    if get_script_run_ctx() is not None:
        return

    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__], check=False)
    raise SystemExit(0)


_ensure_streamlit_launch_mode()

load_dotenv()

st.set_page_config(page_title="YouTube to GIF", page_icon="🎥")

st.markdown(
    """
    <style>
    .st-key-upload_data [data-testid="stElementContainer"] {
        width: fit-content;
        margin: 0 auto;
    }
    .st-key-back_button [data-testid="stElementContainer"] {
        width: fit-content;
        margin: 0 auto;
    }

    .st-key-upload_data [data-testid="stButton"] > button {
        width: auto;
    }
    .st-key-back_button [data-testid="stButton"] > button {
        width: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Initialize session state ---
if "mode" not in st.session_state:
    st.session_state.mode = "editing"  # editing, preview, processing, result

if "cookies_browser" not in st.session_state:
    st.session_state.cookies_browser = ""


st.title("YouTube to GIF Converter")
st.caption("Turn any YouTube moment into a shareable GIF in four quick steps.")


def _strip_ansi_codes(text):
    return re.sub(r"\x1b\[[0-9;]*m", "", str(text))


def _extract_video_id(url):
    patterns = [
        r"(?:v=)([0-9A-Za-z_-]{11})",
        r"youtu\.be/([0-9A-Za-z_-]{11})",
        r"youtube\.com/embed/([0-9A-Za-z_-]{11})",
        r"youtube\.com/shorts/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _is_valid_youtube_url(url):
    if not url:
        return False
    return _extract_video_id(url.strip()) is not None


def _reset_workflow_state(clear_outputs=False):
    gif_path = st.session_state.get("gif_path")
    high_res_gif_path = st.session_state.get("high_res_gif_path")

    keys_to_clear = [
        "url",
        "start_time",
        "end_time",
        "gif_path",
        "high_res_gif_path",
        "standard_gif_bytes",
        "high_res_gif_bytes",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)

    if clear_outputs:
        for path in [gif_path, high_res_gif_path, "output.gif", "output_high_res.gif", "temp_video.mp4"]:
            if path and os.path.exists(path):
                os.remove(path)


def _get_cookies_from_browser_value():
    """Read optional cookie source from UI or env, e.g. chrome or firefox."""
    ui_value = st.session_state.get("cookies_browser", "").strip()
    if ui_value:
        return (ui_value,)

    raw = os.getenv("YTDLP_COOKIES_FROM_BROWSER", "").strip()
    if not raw:
        return None
    return tuple(part.strip() for part in raw.split(":") if part.strip())


def _looks_like_auth_required_error(error_text):
    lowered = error_text.lower()
    markers = [
        "sign in to confirm your age",
        "age-restricted",
        "inappropriate for some users",
        "use --cookies-from-browser",
        "private video",
        "this video is private",
        "members-only",
    ]
    return any(marker in lowered for marker in markers)


def _download_video_with_fallback(url, video_path):
    common_opts = {
        "outtmpl": video_path,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }

    attempts = [
        {
            **common_opts,
            "format": "bestvideo*+bestaudio/best",
            "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        },
        {
            **common_opts,
            "format": "best[ext=mp4]/best",
            "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        },
    ]

    cookies_from_browser = _get_cookies_from_browser_value()
    if cookies_from_browser:
        attempts.insert(
            0,
            {
                **common_opts,
                "format": "bestvideo*+bestaudio/best",
                "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
                "cookiesfrombrowser": cookies_from_browser,
            },
        )

    last_error = None
    for ydl_opts in attempts:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return
        except yt_dlp.utils.DownloadError as exc:
            last_error = exc

    cleaned_error = _strip_ansi_codes(last_error)
    if _looks_like_auth_required_error(cleaned_error):
        raise RuntimeError(
            "This video appears to require sign-in (age-restricted/private/members-only). "
            "Open 'Advanced: Authentication (optional)', choose your browser, and try again. "
            f"Last yt-dlp error: {cleaned_error}"
        )

    raise RuntimeError(
        "Could not download this YouTube video with available formats. "
        "If this continues, use 'Advanced: Authentication (optional)' and retry. "
        f"Last yt-dlp error: {cleaned_error}"
    )


def download_and_convert(url, start_time, end_time):
    temp_dir = tempfile.mkdtemp(prefix="gifgen_")
    video_path = os.path.join(temp_dir, "video.mp4")
    gif_path = os.path.join(temp_dir, "output.gif")
    high_res_gif_path = os.path.join(temp_dir, "output_high_res.gif")

    clip = None
    segment = None
    standard_segment = None
    try:
        _download_video_with_fallback(url, video_path)
        clip = VideoFileClip(video_path)

        safe_end = min(float(end_time), float(clip.duration))
        if float(start_time) >= safe_end:
            raise RuntimeError("Selected time range is outside the downloaded video duration.")

        segment = clip.subclipped(float(start_time), safe_end)

        # Standard GIF
        standard_segment = segment.resized(height=360)
        standard_segment.write_gif(gif_path, fps=15)

        # High-Res GIF
        segment.write_gif(high_res_gif_path, fps=24)

        with open(gif_path, "rb") as gif_file:
            standard_bytes = gif_file.read()
        with open(high_res_gif_path, "rb") as high_res_file:
            high_res_bytes = high_res_file.read()

        return standard_bytes, high_res_bytes
    finally:
        if standard_segment is not None:
            standard_segment.close()
        if segment is not None:
            segment.close()
        if clip is not None:
            clip.close()
        for path in [video_path, gif_path, high_res_gif_path]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.isdir(temp_dir):
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass


# --- Editing Mode ---
if st.session_state.mode == "editing":
    st.header("1. Choose Video and Time Range")
    st.write("Paste a YouTube link, choose your start and end times, then preview before generating.")

    url = st.text_input(
        "YouTube URL",
        value=st.session_state.get("url", ""),
        placeholder="https://www.youtube.com/watch?v=...",
        help="Accepted formats: watch links, youtu.be links, embed links, and Shorts.",
    )

    with st.expander("Advanced: Authentication (optional)", expanded=False):
        st.caption("Only needed for age-restricted, private, or members-only videos.")
        auth_options = ["None", "chrome", "firefox", "edge", "brave", "opera", "safari"]
        current_auth = st.session_state.get("cookies_browser", "")
        default_index = auth_options.index(current_auth) if current_auth in auth_options else 0
        selected_auth = st.selectbox(
            "Browser cookie source",
            auth_options,
            index=default_index,
            help="Used as yt-dlp --cookies-from-browser.",
        )
        st.session_state.cookies_browser = "" if selected_auth == "None" else selected_auth

    col1, col2 = st.columns(2)
    with col1:
        start_time = st.number_input(
            "Start Time (seconds)",
            min_value=0,
            value=int(st.session_state.get("start_time", 0)),
            step=1,
        )
    with col2:
        end_time = st.number_input(
            "End Time (seconds)",
            min_value=1,
            value=int(st.session_state.get("end_time", 10)),
            step=1,
        )

    duration = end_time - start_time
    can_proceed = bool(url.strip())

    if url and not _is_valid_youtube_url(url):
        st.warning("Please enter a valid YouTube URL to continue.")
        can_proceed = False
    if duration > 20:
        st.warning(f"Maximum clip length is 20 seconds. You selected {duration} seconds.")
        can_proceed = False
    elif duration <= 0:
        st.error("End time must be greater than start time.")
        can_proceed = False
    else:
        st.info(f"Clip duration: {duration} seconds")

    preview_clicked = st.button("Preview Clip", disabled=not can_proceed)

    if preview_clicked:
        if not can_proceed:
            st.stop()
        st.session_state.url = url.strip()
        st.session_state.start_time = start_time
        st.session_state.end_time = end_time
        st.session_state.mode = "preview"
        st.rerun()


# --- Preview Mode ---
if st.session_state.mode == "preview":
    st.header("2. Preview Segment")
    st.write("Check that timing looks right before generating the GIF.")

    url = st.session_state.url
    start_time = st.session_state.start_time
    end_time = st.session_state.end_time

    video_id = _extract_video_id(url)
    if video_id:
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        summary_col1.metric("Start", f"{int(start_time)}s")
        summary_col2.metric("End", f"{int(end_time)}s")
        summary_col3.metric("Duration", f"{int(end_time - start_time)}s")

        embed_url = (
            f"https://www.youtube.com/embed/{video_id}?start={int(start_time)}"
            f"&end={int(end_time)}&autoplay=1"
        )
        st.components.v1.iframe(embed_url, height=420, scrolling=False)
    else:
        st.error("The saved URL is not valid. Go back and update it.")

    action_cols = st.columns(3, vertical_alignment="center")
    back_clicked = False
    generate_clicked = False

    with action_cols[0]:
        with st.container(key="back_button"): 
            back_clicked = st.button("Back to Edit")

    with action_cols[2]:
        with st.container(key="upload_data"):
            generate_clicked = st.button("Generate GIFs", disabled=video_id is None)

    if back_clicked:
        st.session_state.mode = "editing"
        st.rerun()

    if generate_clicked:
        st.session_state.mode = "processing"
        st.rerun()


# --- Processing Pipeline ---
if st.session_state.mode == "processing":
    st.header("3. Processing")
    st.info("Downloading your clip and creating standard + high-resolution GIF outputs.")
    with st.spinner("Working..."):
        try:
            standard_gif_bytes, high_res_gif_bytes = download_and_convert(
                st.session_state.url,
                st.session_state.start_time,
                st.session_state.end_time,
            )

            st.session_state.standard_gif_bytes = standard_gif_bytes
            st.session_state.high_res_gif_bytes = high_res_gif_bytes
            st.session_state.mode = "result"
            st.rerun()
        except Exception as exc:
            st.error("GIF generation failed for this selection.")
            st.caption(str(exc))
            retry_col1, retry_col2 = st.columns(2)
            with retry_col1:
                if st.button("Back to Preview"):
                    st.session_state.mode = "preview"
                    st.rerun()
            with retry_col2:
                if st.button("Start Over"):
                    _reset_workflow_state(clear_outputs=True)
                    st.session_state.mode = "editing"
                    st.rerun()


# --- Result Mode ---
def upload_to_imgur(image_bytes):
    client_id = os.getenv("IMGUR_CLIENT_ID")
    if not client_id:
        return None, "Imgur Client ID not found. Set IMGUR_CLIENT_ID in your .env file."

    headers = {"Authorization": f"Client-ID {client_id}"}
    url = "https://api.imgur.com/3/image"

    try:
        response = requests.post(
            url,
            headers=headers,
            files={"image": ("standard.gif", image_bytes, "image/gif")},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            return data["data"]["link"], None
        return None, f"Imgur API error: {response.status_code} - {response.text}"
    except requests.RequestException as exc:
        return None, f"Network error during upload: {exc}"
    except Exception as exc:
        return None, f"Upload failed: {exc}"


if st.session_state.mode == "result":
    st.header("4. Download Your GIF")
    st.write("Your GIF is ready. Download either version, then create another if you want.")

    standard_bytes = st.session_state.get("standard_gif_bytes")
    high_res_bytes = st.session_state.get("high_res_gif_bytes")

    if not standard_bytes or not high_res_bytes:
        st.error("Your GIF files are missing or could not be loaded. Please generate again.")
        if st.button("Back to Edit"):
            _reset_workflow_state(clear_outputs=True)
            st.session_state.mode = "editing"
            st.rerun()
    else:
        st.image(standard_bytes, caption="Preview (standard GIF)")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download Standard GIF",
                data=standard_bytes,
                file_name="standard.gif",
                mime="image/gif",
            )

        with col2:
            st.download_button(
                label="Download High-Resolution GIF",
                data=high_res_bytes,
                file_name="high_res.gif",
                mime="image/gif",
            )

        with st.expander("Optional: Upload to Imgur", expanded=False):
            st.info(
                "Uploading to Imgur creates a public link. Make sure you are okay with public visibility."
            )
            if st.button("Upload Standard GIF to Imgur"):
                with st.spinner("Uploading..."):
                    link, error = upload_to_imgur(standard_bytes)
                    if link:
                        st.success(f"Upload complete: {link}")
                        st.markdown(f"[Open in Imgur]({link})")
                    else:
                        st.error(error)

    if st.button("Create Another GIF"):
        _reset_workflow_state(clear_outputs=True)
        st.session_state.mode = "editing"
        st.rerun()
