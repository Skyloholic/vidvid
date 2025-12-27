# Video Downloader - Deploy on Render

## Features
- Download videos from YouTube, Instagram, TikTok, Pinterest, and 1000+ other platforms
- Videos download directly to your browser's Downloads folder
- Simple, clean web interface

## Deploy on Render

1. **Create a GitHub repo** and push this code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Go to [Render.com](https://render.com)**

3. **Create New Web Service**:
   - Connect your GitHub repo
   - Name: `video-downloader` (or any name)
   - Runtime: `Python 3.11`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
   - Plan: Free (or paid if you want more reliability)

4. **Click Deploy** and wait 2-3 minutes

5. **Your app will be live at**: `https://your-app-name.onrender.com`

## Files Included
- `app.py` - Flask backend
- `templates/index.html` - Frontend UI
- `requirements.txt` - Python dependencies
- `Procfile` - Deployment configuration

## Notes
- Videos are temporarily stored on the server, then auto-deleted
- Free tier on Render has 750 hours/month limit
- Each download uses server bandwidth (be aware of limits)
