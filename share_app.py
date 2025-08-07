import subprocess
import time
from pyngrok import ngrok

# Start Streamlit in background
print("Starting Streamlit app...")
streamlit_process = subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "8501"])

# Wait a moment for Streamlit to start
time.sleep(3)

# Create ngrok tunnel
print("Creating public URL...")
public_url = ngrok.connect(8501)
print(f"\n🎉 Your app is now available at: {public_url}")
print("Share this URL with anyone!")
print("\nPress Ctrl+C to stop the server")

try:
    # Keep the script running
    streamlit_process.wait()
except KeyboardInterrupt:
    print("\nShutting down...")
    streamlit_process.terminate()
    ngrok.kill() 