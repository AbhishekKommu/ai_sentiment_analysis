# 🎭 AI Sentiment Analysis

Beautiful sentiment analysis web app with animated backgrounds, glassmorphism UI, and real NLP-powered emotion detection.

## ✨ Features

- 🤖 **Real AI Sentiment Analysis** (TextBlob NLP)
- 🎨 **Animated gradient background** with floating orbs & particles
- 💎 **Glassmorphism** UI with blur effects
- 📊 **Statistics dashboard** (positive / neutral / negative)
- 📝 **History tracking** with search & filter
- 📤 **Export CSV / JSON**
- 🎲 **Random examples** for quick testing
- ⌨️ **Ctrl+Enter** to analyze instantly
- 📱 Fully responsive

## 🚀 Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download TextBlob corpora (first time only)
python -m textblob.download_corpora

# 5. Run
python app.py