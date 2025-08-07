# Social Media Caption Generator

A Streamlit app that generates creative social media captions using Anthropic's Claude AI.

## Features
- Generate captions for different brand types
- Choose from various tones (funny, serious, inspirational, etc.)
- Support for multiple social media platforms
- AI-powered creative content generation

## Deployment Instructions

### Option 1: Streamlit Cloud (Recommended)

1. **Create a GitHub repository** and push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Sign in with GitHub** and connect your repository

4. **Deploy your app** by selecting your repository and main file (`app.py`)

5. **Add your API key** as a secret in Streamlit Cloud:
   - Go to your app settings
   - Add a secret with key: `ANTHROPIC_API_KEY`
   - Value: Your complete Anthropic API key

### Option 2: Heroku

1. Create a `Procfile`:
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. Deploy to Heroku using their CLI or GitHub integration

### Option 3: Railway

1. Connect your GitHub repository to Railway
2. Railway will automatically detect it's a Python app
3. Add your API key as an environment variable

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)

## Note
Make sure to keep your API key secure and never commit it to version control. 