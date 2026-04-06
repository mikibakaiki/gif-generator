# YouTube to GIF Converter

A web-based tool that converts YouTube video clips into high-quality GIFs. Select any moment from a YouTube video, trim it to a maximum of 20 seconds, and download as standard or high-resolution GIF. Optionally upload directly to Imgur for quick sharing.

## Features

- 🎥 **Download from YouTube** - Paste any YouTube URL (regular videos, Shorts, playlists)
- ✂️ **Easy Time Selection** - Use simple start/end time inputs to select your clip
- 🔍 **Live Preview** - Embedded YouTube player shows exactly what you'll convert
- 📊 **Dual Quality Output** - Standard (360p) and high-resolution (full quality) GIF versions
- 🖼️ **Direct Imgur Upload** - Optional one-click upload to Imgur for instant sharing
- 🔐 **Authentication Support** - Handle age-restricted and members-only videos with browser cookies
- 🐳 **Docker Ready** - Full Docker and Docker Compose configuration included
- 📱 **Responsive Web UI** - Built with Streamlit for a smooth user experience

## Requirements

### Python Dependencies
- **moviepy** - Video processing and GIF creation
- **python-dotenv** - Environment variable management
- **requests** - HTTP client for API calls
- **streamlit** - Web framework
- **yt-dlp** - YouTube video downloading

### System Requirements
- Python 3.11+
- FFmpeg (for video processing)
- FFprobe (included with FFmpeg)

### Online Services (Optional)
- **Imgur Account** (optional) - For uploading GIFs to Imgur

## Installation

### Option 1: Local Setup (Recommended for Development)

1. **Clone or download the repository**
   ```bash
   cd gif-generator
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   # or
   source .venv/bin/activate  # On macOS/Linux
   ```

3. **Install FFmpeg**
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use `choco install ffmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg`

4. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a `.env` file** in the project root (see Configuration section below)
   ```bash
   cp .env.example .env  # If provided, or create manually
   ```

### Option 2: Docker Setup

1. **Build the Docker image**
   ```bash
   docker build -t gif-generator .
   ```

2. **Run with Docker**
   ```bash
   docker run -p 8501:8501 --env-file .env gif-generator
   ```

### Option 3: Docker Compose (Easiest)

1. **Create or verify your `.env` file** (see Configuration section)

2. **Start the container**
   ```bash
   docker-compose up
   ```

3. **Access the app** at `http://localhost:8501`

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following:

```
# Optional: Imgur integration for uploading GIFs
IMGUR_CLIENT_ID=your_imgur_client_id_here

# Optional: Browser cookies for downloading restricted videos
# Format: browser_name:user_name (e.g., chrome:Default or firefox:default)
YTDLP_COOKIES_FROM_BROWSER=

# Docker/deployment configuration (usually auto-configured)
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

## How to Run

### Local Development
```bash
# Make sure your virtual environment is activated
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

### Docker
```bash
docker-compose up
```

Access at `http://localhost:8501`

## How to Get an Imgur Client ID

Imgur allows anonymous uploads using a Client ID. Here's how to obtain one without creating an account:

### Steps

1. **Open Imgur Upload Page**
   - Go to [imgur.com](https://imgur.com)
   - Click on the upload button or navigate to the upload interface

2. **Upload an Image Without Login**
   - Select an image file from your computer
   - Complete the upload without creating an account or signing in
   - The upload will proceed as an anonymous user

3. **Access Browser Developer Tools**
   - After upload completes, open your browser's Developer Tools
   - On Windows/Linux: Press `F12` or `Ctrl+Shift+I`
   - On macOS: Press `Cmd+Option+I`
   - Go to the **Network** tab

4. **Find the API Request**
   - Reload the page or upload another image
   - Look for requests to `api.imgur.com`
   - Click on one of these requests and inspect the **Headers** section

5. **Extract the Client ID**
   - Look for the `Authorization` header
   - It will be formatted like: `Client-ID your_client_id_here`
   - Copy the client ID portion (the long alphanumeric string)

6. **Add to Your `.env` File**
   ```
   IMGUR_CLIENT_ID=your_copied_client_id_here
   ```

7. **Restart the App**
   - The app will now be able to upload GIFs to Imgur

### Alternative: Official Imgur API Registration
If you prefer to register officially:
1. Go to https://api.imgur.com/oauth2/addclient
2. Fill out the form and select "OAuth 2 authorization without a callback URL"
3. You'll receive Client ID and Client Secret
4. Use the Client ID in your configuration

## How to Use

### Basic Workflow

1. **Step 1: Choose Video and Time Range**
   - Paste a YouTube URL (supports regular videos, Shorts, and embeds)
   - Enter start and end times in seconds
   - Maximum clip length is 20 seconds

2. **Step 2: Preview Segment**
   - The embedded YouTube player shows your selected time range
   - Verify the timing is correct
   - Go back to edit if needed

3. **Step 3: Processing**
   - The app downloads the video
   - Converts your selection to two GIF versions:
     - **Standard**: 360p height, 15 fps (smaller file size)
     - **High-Res**: Full resolution, 24 fps (better quality)

4. **Step 4: Download or Upload**
   - Preview the standard GIF
   - Download either version to your computer
   - Optionally upload to Imgur for instant sharing
   - Create another GIF or exit

### Advanced: Age-Restricted Videos

For age-restricted, private, or members-only videos:

1. Click **"Advanced: Authentication (optional)"** in Step 1
2. Select your browser (Chrome, Firefox, Edge, Safari, etc.)
3. The app will use your browser's cookies to authenticate
4. Alternatively, upload a cookies file (JSON format) for cloud deployments

## Troubleshooting

### "Could not download this YouTube video"
- The video may be age-restricted or region-blocked
- Try enabling browser cookies in Advanced options
- Some videos may not be downloadable due to rights restrictions

### "Imgur Client ID not found"
- You haven't set `IMGUR_CLIENT_ID` in your `.env` file
- Imgur upload is optional; you can still download GIFs locally

### "MoviePy error" / GIF generation fails
- Ensure FFmpeg is installed and in your PATH
- Try a shorter clip (under 10 seconds)
- Check that your system has sufficient disk space

### Port 8501 already in use
- Change the port when running Docker: `docker run -p 8502:8501 ...`
- Or use environments variable: `STREAMLIT_SERVER_PORT=8502`

## Project Structure

```
.
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker container configuration
├── docker-compose.yml     # Docker Compose configuration
├── .env                   # Environment variables (create this)
└── README.md             # This file
```

## Technical Details

### Video Download
- Uses **yt-dlp** with fallback strategies for various YouTube formats
- Supports cookie-based authentication for restricted videos
- Merges best video and audio streams

### Video Processing
- **MoviePy** for video file handling and GIF creation
- Clips are trimmed using `subclipped()` for clean cuts
- Standard GIF: 360p height, 15 fps
- High-Res GIF: Original resolution, 24 fps

### Upload
- **Imgur API** for anonymous GIF hosting
- Requires only Client ID (no authentication needed)
- Returns shareable public links instantly

## Browser Support

Works on any modern browser:
- Chrome/Chromium
- Firefox
- Safari
- Edge

Mobile browsers are supported with responsive design.

## Limitations

- Maximum clip length: 20 seconds
- Imgur upload creates public, unlisted links
- Some videos may be unavailable due to copyright or regional restrictions
- GIF file sizes depend on clip length and quality selected (typically 1-20 MB)

## License

[Specify your license here, e.g., MIT, GPL, etc.]

## Contributing

Issues and pull requests are welcome. Please describe your use case and any errors you encounter.

## Support

For issues with:
- **yt-dlp**: See https://github.com/yt-dlp/yt-dlp
- **MoviePy**: See https://github.com/Zulko/moviepy
- **Imgur API**: See https://api.imgur.com/
- **Streamlit**: See https://docs.streamlit.io/

