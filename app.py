"""
🎭 AI Sentiment Analysis — Self-Contained Version
No TextBlob, No NLTK — Works out of the box!
"""

from flask import Flask, render_template, request, jsonify, make_response
import sqlite3
import os
import csv
import io
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# ═══════════════════════════════════════════════════════════════
#                       APP CONFIG
# ═══════════════════════════════════════════════════════════════

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
DB_PATH = 'database/sentiment.db'
MAX_TEXT_LENGTH = 10000
MAX_BATCH_SIZE = 100
VERSION = '3.0.0'


# ═══════════════════════════════════════════════════════════════
#                   SENTIMENT LEXICONS
# ═══════════════════════════════════════════════════════════════

POSITIVE_WORDS = {
    'amazing': 2.5, 'awesome': 2.5, 'excellent': 2.5, 'fantastic': 2.5,
    'wonderful': 2.5, 'outstanding': 2.5, 'brilliant': 2.3, 'perfect': 2.5,
    'love': 2.0, 'loved': 2.0, 'loves': 2.0, 'adore': 2.2, 'adored': 2.2,
    'best': 2.2, 'great': 1.8, 'good': 1.5, 'nice': 1.3, 'happy': 1.8,
    'delighted': 2.0, 'pleased': 1.5, 'glad': 1.5, 'enjoy': 1.6,
    'enjoyed': 1.6, 'enjoyable': 1.6, 'recommend': 1.5, 'recommended': 1.5,
    'superb': 2.2, 'impressive': 1.8, 'exceptional': 2.3, 'phenomenal': 2.4,
    'super': 1.7, 'beautiful': 1.8, 'gorgeous': 2.0, 'stunning': 2.0,
    'cool': 1.2, 'incredible': 2.3, 'magnificent': 2.3, 'favorite': 1.8,
    'favourite': 1.8, 'satisfied': 1.4, 'satisfaction': 1.4, 'positive': 1.2,
    'success': 1.5, 'win': 1.5, 'winner': 1.8, 'smile': 1.4, 'fun': 1.3,
    'terrific': 2.0, 'yay': 1.5, 'wow': 1.6, 'yes': 1.0, 'like': 1.0,
    'liked': 1.0, 'likes': 1.0, 'thanks': 1.2, 'thank': 1.2, 'helpful': 1.5,
    'help': 1.0, 'helping': 1.0, 'supported': 1.2, 'supportive': 1.3,
    'friendly': 1.5, 'kind': 1.4, 'generous': 1.5, 'polite': 1.3,
    'fast': 1.2, 'quick': 1.2, 'speedy': 1.3, 'efficient': 1.4,
    'clean': 1.2, 'fresh': 1.2, 'bright': 1.2, 'smooth': 1.2,
    'powerful': 1.3, 'strong': 1.2, 'safe': 1.3, 'secure': 1.3,
    'reliable': 1.4, 'trust': 1.4, 'trusted': 1.5, 'trustworthy': 1.5,
    'honest': 1.4, 'sincere': 1.4, 'genuine': 1.3, 'authentic': 1.3,
    'valuable': 1.4, 'worth': 1.3, 'worthwhile': 1.4, 'quality': 1.2,
    'easy': 1.2, 'simple': 1.0, 'convenient': 1.3, 'useful': 1.3,
    'works': 1.0, 'worked': 1.2, 'working': 1.0, 'improved': 1.3,
    'improvement': 1.3, 'better': 1.4, 'bestest': 2.0, 'sweet': 1.2,
    'cute': 1.3, 'lovely': 1.6, 'charming': 1.4, 'elegant': 1.4,
}

NEGATIVE_WORDS = {
    'terrible': -2.5, 'awful': -2.5, 'horrible': -2.5, 'hate': -2.5,
    'hated': -2.5, 'hates': -2.5, 'worst': -2.5, 'disgusting': -2.5,
    'pathetic': -2.3, 'useless': -2.2, 'garbage': -2.3, 'trash': -2.2,
    'rubbish': -2.2, 'bad': -1.5, 'poor': -1.5, 'sad': -1.8,
    'unhappy': -1.8, 'disappointed': -2.0, 'disappointing': -2.0,
    'disappointment': -2.0, 'annoying': -1.7, 'annoyed': -1.7,
    'angry': -2.0, 'furious': -2.3, 'mad': -1.8, 'upset': -1.7,
    'frustrated': -1.8, 'frustrating': -1.8, 'frustration': -1.8,
    'boring': -1.5, 'bored': -1.3, 'ugly': -1.8, 'stupid': -2.0,
    'dumb': -1.9, 'idiot': -2.2, 'idiotic': -2.2, 'waste': -2.0,
    'wasted': -2.0, 'wasteful': -2.0, 'failure': -2.0, 'fail': -1.8,
    'failed': -1.8, 'fails': -1.8, 'broken': -1.5, 'defective': -1.8,
    'faulty': -1.7, 'wrong': -1.3, 'error': -1.2, 'problem': -1.3,
    'problems': -1.3, 'issue': -1.0, 'issues': -1.0, 'refund': -1.3,
    'complaint': -1.4, 'complain': -1.4, 'complained': -1.4, 'scam': -2.5,
    'fraud': -2.5, 'cheat': -2.3, 'cheated': -2.3, 'lie': -2.0,
    'lied': -2.0, 'liar': -2.2, 'disaster': -2.2, 'nightmare': -2.3,
    'disgusted': -2.3, 'repulsive': -2.4, 'gross': -1.8, 'nasty': -1.8,
    'yuck': -2.0, 'sick': -1.5, 'sickening': -2.2, 'foul': -2.0,
    'slow': -1.2, 'broken': -1.5, 'damaged': -1.6, 'damage': -1.6,
    'rude': -2.0, 'mean': -1.5, 'unfriendly': -1.7, 'unhelpful': -1.8,
    'unhelp': -1.5, 'ignored': -1.6, 'ignore': -1.4, 'ignorant': -1.8,
    'dislike': -1.5, 'disliked': -1.5, 'unpleasant': -1.8, 'uncomfortable': -1.5,
    'dangerous': -1.8, 'unsafe': -1.8, 'harmful': -1.8, 'hurt': -1.5,
    'pain': -1.5, 'painful': -1.6, 'suffering': -1.8, 'misery': -2.0,
    'miserable': -2.0, 'depressed': -2.0, 'depressing': -1.8,
    'stress': -1.3, 'stressed': -1.5, 'stressful': -1.5,
    'never': -0.8, 'no': -0.8, 'not': -0.7, 'cannot': -1.0, 'cant': -1.0,
    'wont': -0.9, 'didnt': -0.8, 'doesnt': -0.8, 'worse': -1.8,
    'poorly': -1.5, 'lousy': -2.0, 'sucks': -2.3, 'sucked': -2.3,
    'regret': -1.8, 'regretful': -1.8, 'sorry': -1.2, 'unfortunately': -1.3,
}

# Intensifiers boost the sentiment strength
INTENSIFIERS = {
    'very': 1.5, 'really': 1.5, 'extremely': 2.0, 'absolutely': 2.0,
    'completely': 1.8, 'totally': 1.8, 'so': 1.5, 'super': 1.7,
    'incredibly': 2.0, 'highly': 1.6, 'deeply': 1.5, 'truly': 1.5,
    'quite': 1.3, 'rather': 1.3, 'pretty': 1.2, 'somewhat': 1.2,
}

# Negations flip sentiment
NEGATIONS = {'not', 'no', 'never', 'none', 'nobody', 'nothing', 'neither',
             'nowhere', 'hardly', 'barely', 'scarcely', "don't", "doesn't",
             "didn't", "won't", "wouldn't", "can't", "cannot", "couldn't",
             "shouldn't", "isn't", "aren't", "wasn't", "weren't"}

EMOTION_LEXICON = {
    'joy': {'happy', 'happiness', 'joy', 'joyful', 'delighted', 'cheerful',
            'excited', 'excitement', 'thrilled', 'ecstatic', 'elated',
            'pleased', 'glad', 'smile', 'smiling', 'laugh', 'laughing',
            'love', 'loved', 'adore', 'wonderful', 'amazing', 'fantastic',
            'awesome', 'great', 'brilliant', 'celebrate', 'yay', 'wow'},
    'sadness': {'sad', 'sadness', 'unhappy', 'depressed', 'down',
                'blue', 'cry', 'crying', 'tears', 'miserable',
                'heartbroken', 'devastated', 'disappointed', 'lonely',
                'hopeless', 'sorrow', 'grief', 'regret', 'miss'},
    'anger': {'angry', 'anger', 'furious', 'fury', 'rage', 'raging', 'mad',
              'outraged', 'irritated', 'irritating', 'annoyed', 'annoying',
              'frustrated', 'frustrating', 'hate', 'hated', 'hatred',
              'disgusted', 'infuriated', 'enraged', 'livid'},
    'fear': {'afraid', 'scared', 'frightened', 'terrified', 'fear',
             'fearful', 'anxious', 'anxiety', 'worried', 'worry',
             'nervous', 'panic', 'dread', 'horror', 'horrified',
             'petrified', 'scary'},
    'surprise': {'surprised', 'surprising', 'surprise', 'shocked',
                 'shocking', 'amazed', 'astonished', 'stunned',
                 'unexpected', 'unbelievable', 'incredible', 'wow',
                 'whoa', 'unreal'},
    'disgust': {'disgusted', 'disgusting', 'disgust', 'revolting',
                'repulsive', 'gross', 'nasty', 'yuck', 'yucky', 'sick',
                'sickening', 'vile', 'filthy', 'foul'},
    'trust': {'trust', 'trusted', 'trustworthy', 'reliable', 'honest',
              'sincere', 'loyal', 'loyalty', 'faithful', 'dependable',
              'authentic', 'genuine'},
    'anticipation': {'hope', 'hopeful', 'hoping', 'expect', 'expecting',
                     'expected', 'anticipate', 'anticipating', 'wait',
                     'waiting', 'soon', 'eager', 'eagerly', 'forward',
                     'tomorrow', 'future'},
}

ASPECT_KEYWORDS = {
    'product': ['product', 'item', 'goods', 'merchandise'],
    'service': ['service', 'support', 'assistance', 'staff'],
    'price': ['price', 'cost', 'value', 'expensive', 'cheap', 'affordable'],
    'quality': ['quality', 'build', 'material', 'durability'],
    'delivery': ['delivery', 'shipping', 'arrival', 'package', 'courier'],
    'usability': ['easy', 'difficult', 'usable', 'interface', 'intuitive'],
    'design': ['design', 'look', 'appearance', 'style', 'aesthetic'],
    'performance': ['performance', 'speed', 'fast', 'slow'],
}

STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'else', 'when',
    'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
    'through', 'during', 'before', 'after', 'above', 'below', 'to',
    'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
    'again', 'further', 'once', 'here', 'there', 'all', 'any', 'both',
    'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    'can', 'will', 'just', 'should', 'now', 'i', 'me', 'my', 'we',
    'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it',
    'its', 'they', 'them', 'their', 'what', 'which', 'who', 'whom',
    'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was',
    'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
    'do', 'does', 'did', 'doing', 'would', 'could', 'should', 'may',
    'might', 'must', 'shall', 'as', 'of', 'also', 'get', 'got',
    'go', 'going', 'went', 'come', 'came', 'see', 'saw', 'seen',
    'know', 'knew', 'think', 'thought', 'say', 'said', 'tell', 'told',
    'make', 'made', 'take', 'took', 'give', 'gave', 'find', 'found',
    'use', 'used', 'using', 'one', 'two', 'three', 'first', 'last',
    'new', 'old', 'big', 'small', 'long', 'short',
    'high', 'low', 'right', 'left', 'well', 'much', 'many', 'lot',
    'really', 'still', 'even', 'back', 'way', 'time', 'day', 'year',
    'may', 'us', 'let', 'put', 'every', 'why', 'how', 'where',
    'because', 'while', 'since', 'until', 'though',
}

LANGUAGE_PATTERNS = {
    'English': r'\b(the|and|is|are|you|have|this|that|with|for)\b',
    'Spanish': r'\b(el|la|los|las|es|son|y|de|que|en|por|con)\b',
    'French': r'\b(le|la|les|est|sont|et|de|que|pour|avec|dans)\b',
    'German': r'\b(der|die|das|ist|sind|und|von|mit|für|auf)\b',
    'Italian': r'\b(il|la|gli|è|sono|e|di|che|per|con|in)\b',
    'Portuguese': r'\b(o|a|os|as|é|são|e|de|que|para|com)\b',
    'Hindi': r'[\u0900-\u097F]',
    'Chinese': r'[\u4e00-\u9fff]',
    'Japanese': r'[\u3040-\u309F\u30A0-\u30FF]',
    'Korean': r'[\uAC00-\uD7AF]',
    'Arabic': r'[\u0600-\u06FF]',
    'Russian': r'[\u0400-\u04FF]',
}


# ═══════════════════════════════════════════════════════════════
#                    DATABASE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs('database', exist_ok=True)
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        sentiment TEXT NOT NULL,
        polarity REAL NOT NULL,
        subjectivity REAL NOT NULL,
        confidence REAL NOT NULL,
        emotion TEXT DEFAULT 'neutral',
        emotion_score REAL DEFAULT 0,
        language TEXT DEFAULT 'English',
        word_count INTEGER DEFAULT 0,
        char_count INTEGER DEFAULT 0,
        sentence_count INTEGER DEFAULT 0,
        keywords TEXT DEFAULT '[]',
        aspects TEXT DEFAULT '{}',
        is_batch INTEGER DEFAULT 0,
        session_id TEXT DEFAULT '',
        source TEXT DEFAULT 'web',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
        last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
        analysis_count INTEGER DEFAULT 0
    )''')

    c.execute('CREATE INDEX IF NOT EXISTS idx_sentiment ON analyses(sentiment)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_created ON analyses(created_at)')

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
#                  SENTIMENT ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════

def detect_language(text):
    """Detect language using character & word patterns."""
    for lang in ('Hindi', 'Chinese', 'Japanese', 'Korean', 'Arabic', 'Russian'):
        if re.search(LANGUAGE_PATTERNS[lang], text):
            return lang

    scores = defaultdict(int)
    for lang in ('English', 'Spanish', 'French', 'German',
                 'Italian', 'Portuguese'):
        matches = re.findall(LANGUAGE_PATTERNS[lang], text.lower())
        scores[lang] = len(matches)

    if scores and max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return 'English'


def extract_keywords(text, top_n=15):
    """Extract keywords by frequency + position."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    words = [w for w in words if w not in STOPWORDS]

    if not words:
        return []

    freq = Counter(words)
    total = len(words)

    scored = {}
    for i, word in enumerate(words):
        pos_score = 1 - (i / max(total, 1)) * 0.5
        scored[word] = scored.get(word, 0) + pos_score

    final_scores = {w: freq[w] * scored[w] for w in freq}
    sorted_words = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    return [
        {'word': w, 'count': freq[w], 'score': round(s, 2)}
        for w, s in sorted_words[:top_n]
    ]


def extract_bigrams(text):
    """Extract two-word phrases."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    bigrams = []
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        if w1 not in STOPWORDS and w2 not in STOPWORDS:
            bigrams.append(f"{w1} {w2}")
    return [{'phrase': p, 'count': c}
            for p, c in Counter(bigrams).most_common(10)]


def detect_emotion(text):
    """Detect dominant emotion."""
    words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
    scores = {}
    for emotion, lexicon in EMOTION_LEXICON.items():
        scores[emotion] = len(words & lexicon)

    if not scores or max(scores.values()) == 0:
        return 'neutral', 0.0

    dominant = max(scores, key=scores.get)
    total = sum(scores.values())
    score = round((scores[dominant] / total) * 100, 1) if total > 0 else 0
    return dominant, score


def calculate_polarity(text):
    """
    Custom sentiment scoring engine.
    Handles: intensifiers, negations, positive/negative words.
    Returns polarity in [-1, 1].
    """
    words = re.findall(r"\b[a-zA-Z']+\b", text.lower())

    if not words:
        return 0.0

    total_score = 0
    scored_words = 0

    for i, word in enumerate(words):
        # Check for intensifier before this word
        multiplier = 1.0
        if i > 0 and words[i - 1] in INTENSIFIERS:
            multiplier = INTENSIFIERS[words[i - 1]]

        # Check for negation within last 3 words
        negated = False
        for j in range(max(0, i - 3), i):
            if words[j] in NEGATIONS:
                negated = True
                break

        word_score = 0
        if word in POSITIVE_WORDS:
            word_score = POSITIVE_WORDS[word] * multiplier
        elif word in NEGATIVE_WORDS:
            word_score = NEGATIVE_WORDS[word] * multiplier

        if word_score != 0:
            if negated:
                word_score = -word_score * 0.7  # flip with reduced strength
            total_score += word_score
            scored_words += 1

    if scored_words == 0:
        return 0.0

    # Normalize to [-1, 1]
    avg = total_score / scored_words
    normalized = max(-1.0, min(1.0, avg / 2.5))

    # Add slight boost for longer texts with consistent sentiment
    if scored_words > 3:
        normalized = max(-1.0, min(1.0, normalized * 1.1))

    return normalized


def calculate_subjectivity(text):
    """Estimate subjectivity: ratio of opinion words to total words."""
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    if not words:
        return 0.0

    opinion_words = 0
    for w in words:
        if w in POSITIVE_WORDS or w in NEGATIVE_WORDS:
            opinion_words += 1
        elif w in INTENSIFIERS or w in NEGATIONS:
            opinion_words += 1

    # Also count first-person pronouns (subjective)
    first_person = {'i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours'}
    opinion_words += sum(1 for w in words if w in first_person)

    ratio = opinion_words / len(words)
    return min(1.0, ratio * 2)  # scale up


def detect_aspects(text):
    """Aspect-based sentiment."""
    text_lower = text.lower()
    aspects = {}

    for aspect, keywords in ASPECT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                idx = text_lower.find(keyword)
                context = text[max(0, idx - 80):min(len(text), idx + 120)]
                polarity = calculate_polarity(context)

                if aspect not in aspects:
                    aspects[aspect] = {'mentions': 0, 'polarity': 0, 'contexts': []}
                aspects[aspect]['mentions'] += 1
                aspects[aspect]['polarity'] += polarity
                if len(aspects[aspect]['contexts']) < 3:
                    aspects[aspect]['contexts'].append(context.strip())

    for aspect in aspects:
        a = aspects[aspect]
        a['polarity'] = round(a['polarity'] / a['mentions'], 3)
        if a['polarity'] > 0.1:
            a['sentiment'] = 'positive'
        elif a['polarity'] < -0.1:
            a['sentiment'] = 'negative'
        else:
            a['sentiment'] = 'neutral'

    return aspects


def analyze_sentiment(text):
    """Master sentiment analysis function."""
    polarity = calculate_polarity(text)
    subjectivity = calculate_subjectivity(text)

    if polarity > 0.5:
        sentiment, emoji, color = 'Very Positive', '😄', '#43e97b'
    elif polarity > 0.1:
        sentiment, emoji, color = 'Positive', '🙂', '#38f9d7'
    elif polarity >= -0.1:
        sentiment, emoji, color = 'Neutral', '😐', '#fee140'
    elif polarity >= -0.5:
        sentiment, emoji, color = 'Negative', '🙁', '#fa709a'
    else:
        sentiment, emoji, color = 'Very Negative', '😡', '#f5576c'

    confidence = round(abs(polarity) * 100, 1)
    emotion, emotion_score = detect_emotion(text)
    language = detect_language(text)
    keywords = extract_keywords(text, top_n=15)
    bigrams = extract_bigrams(text)
    aspects = detect_aspects(text)

    words = re.findall(r'\b\w+\b', text)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    char_count = len(text)

    sentence_analysis = []
    for sentence in sentences:
        s_pol = calculate_polarity(sentence)
        if s_pol > 0.1:
            s_sent = 'positive'
        elif s_pol < -0.1:
            s_sent = 'negative'
        else:
            s_sent = 'neutral'
        sentence_analysis.append({
            'text': sentence,
            'polarity': round(s_pol, 3),
            'sentiment': s_sent
        })

    intensity = 'low'
    if abs(polarity) > 0.7:
        intensity = 'very high'
    elif abs(polarity) > 0.4:
        intensity = 'high'
    elif abs(polarity) > 0.15:
        intensity = 'medium'

    avg_sent_len = len(words) / max(len(sentences), 1)
    readability = ('easy' if avg_sent_len < 15
                   else 'medium' if avg_sent_len < 25
                   else 'complex')

    return {
        'text': text,
        'sentiment': sentiment,
        'emoji': emoji,
        'color': color,
        'polarity': round(polarity, 3),
        'subjectivity': round(subjectivity, 3),
        'confidence': confidence,
        'emotion': emotion,
        'emotion_score': emotion_score,
        'language': language,
        'intensity': intensity,
        'readability': readability,
        'word_count': len(words),
        'char_count': char_count,
        'sentence_count': len(sentences),
        'avg_sentence_length': round(avg_sent_len, 1),
        'keywords': keywords,
        'bigrams': bigrams,
        'aspects': aspects,
        'sentences': sentence_analysis,
        'analyzed_at': datetime.now().isoformat()
    }


# ═══════════════════════════════════════════════════════════════
#                         ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json or {}
    text = (data.get('text') or '').strip()
    session_id = data.get('session_id', '')
    source = data.get('source', 'web')

    if not text:
        return jsonify({'error': 'Text is required'}), 400
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({'error': f'Text too long (max {MAX_TEXT_LENGTH} chars)'}), 400

    result = analyze_sentiment(text)

    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO analyses
                 (text, sentiment, polarity, subjectivity, confidence,
                  emotion, emotion_score, language, word_count, char_count,
                  sentence_count, keywords, aspects, session_id, source)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (text, result['sentiment'], result['polarity'],
               result['subjectivity'], result['confidence'],
               result['emotion'], result['emotion_score'],
               result['language'], result['word_count'],
               result['char_count'], result['sentence_count'],
               json.dumps(result['keywords']),
               json.dumps(result['aspects']),
               session_id, source))
    new_id = c.lastrowid

    if session_id:
        c.execute('''INSERT INTO sessions (id, analysis_count) VALUES (?, 1)
                     ON CONFLICT(id) DO UPDATE SET
                     last_seen = CURRENT_TIMESTAMP,
                     analysis_count = analysis_count + 1''', (session_id,))

    conn.commit()
    conn.close()

    result['id'] = new_id
    result['created_at'] = datetime.now().isoformat()
    return jsonify(result)


@app.route('/api/batch', methods=['POST'])
def batch_analyze():
    data = request.json or {}
    texts = data.get('texts', [])
    session_id = data.get('session_id', '')

    if not texts or not isinstance(texts, list):
        return jsonify({'error': 'Array of texts required'}), 400
    if len(texts) > MAX_BATCH_SIZE:
        return jsonify({'error': f'Max {MAX_BATCH_SIZE} texts'}), 400

    results = []
    conn = get_db()
    c = conn.cursor()

    for text in texts:
        text = str(text).strip()
        if not text or len(text) > MAX_TEXT_LENGTH:
            continue
        result = analyze_sentiment(text)
        c.execute('''INSERT INTO analyses
                     (text, sentiment, polarity, subjectivity, confidence,
                      emotion, emotion_score, language, word_count, char_count,
                      sentence_count, keywords, aspects, is_batch, session_id)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)''',
                  (text, result['sentiment'], result['polarity'],
                   result['subjectivity'], result['confidence'],
                   result['emotion'], result['emotion_score'],
                   result['language'], result['word_count'],
                   result['char_count'], result['sentence_count'],
                   json.dumps(result['keywords']),
                   json.dumps(result['aspects']), session_id))
        result['id'] = c.lastrowid
        results.append(result)

    conn.commit()
    conn.close()

    if results:
        polarities = [r['polarity'] for r in results]
        summary = {
            'total': len(results),
            'positive': sum(1 for r in results if 'Positive' in r['sentiment']),
            'neutral': sum(1 for r in results if r['sentiment'] == 'Neutral'),
            'negative': sum(1 for r in results if 'Negative' in r['sentiment']),
            'avg_polarity': round(sum(polarities) / len(polarities), 3),
            'max_polarity': max(polarities),
            'min_polarity': min(polarities),
            'emotion_distribution': dict(Counter(r['emotion'] for r in results)),
        }
    else:
        summary = {'total': 0}

    return jsonify({'results': results, 'summary': summary})


@app.route('/api/compare', methods=['POST'])
def compare_texts():
    data = request.json or {}
    text_a = (data.get('text_a') or '').strip()
    text_b = (data.get('text_b') or '').strip()

    if not text_a or not text_b:
        return jsonify({'error': 'Both texts required'}), 400

    result_a = analyze_sentiment(text_a)
    result_b = analyze_sentiment(text_b)
    polarity_diff = round(result_b['polarity'] - result_a['polarity'], 3)

    if polarity_diff > 0.1:
        winner, verdict = 'B', f"Text B is more positive by {abs(polarity_diff):.2f}"
    elif polarity_diff < -0.1:
        winner, verdict = 'A', f"Text A is more positive by {abs(polarity_diff):.2f}"
    else:
        winner, verdict = 'tie', "Both texts have similar sentiment"

    return jsonify({
        'a': result_a, 'b': result_b,
        'comparison': {
            'polarity_diff': polarity_diff,
            'winner': winner,
            'verdict': verdict
        }
    })


@app.route('/api/history', methods=['GET'])
def get_history():
    sentiment = request.args.get('sentiment', '')
    emotion = request.args.get('emotion', '')
    language = request.args.get('language', '')
    search = request.args.get('search', '').strip()
    limit = min(request.args.get('limit', 50, type=int), 500)
    offset = request.args.get('offset', 0, type=int)

    query = "SELECT * FROM analyses WHERE 1=1"
    params = []

    if sentiment:
        query += " AND sentiment = ?"
        params.append(sentiment)
    if emotion:
        query += " AND emotion = ?"
        params.append(emotion)
    if language:
        query += " AND language = ?"
        params.append(language)
    if search:
        query += " AND text LIKE ?"
        params.append(f'%{search}%')

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    conn = get_db()
    c = conn.cursor()
    c.execute(query, params)
    rows = [dict(row) for row in c.fetchall()]

    for row in rows:
        try:
            row['keywords'] = json.loads(row.get('keywords') or '[]')
        except Exception:
            row['keywords'] = []
        try:
            row['aspects'] = json.loads(row.get('aspects') or '{}')
        except Exception:
            row['aspects'] = {}

    c.execute("SELECT COUNT(*) FROM analyses")
    total = c.fetchone()[0]
    conn.close()

    return jsonify({'history': rows, 'count': len(rows), 'total': total})


@app.route('/api/history/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Analysis not found'}), 404

    result = dict(row)
    try:
        result['keywords'] = json.loads(result.get('keywords') or '[]')
        result['aspects'] = json.loads(result.get('aspects') or '{}')
    except Exception:
        pass
    return jsonify(result)


@app.route('/api/history/<int:analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM analyses WHERE id = ?', (analysis_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/history/bulk-delete', methods=['POST'])
def bulk_delete():
    data = request.json or {}
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'error': 'No IDs provided'}), 400

    conn = get_db()
    c = conn.cursor()
    placeholders = ','.join('?' * len(ids))
    c.execute(f'DELETE FROM analyses WHERE id IN ({placeholders})', ids)
    deleted = c.rowcount
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'deleted': deleted})


@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM analyses')
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM analyses')
    total = c.fetchone()[0]

    if total == 0:
        conn.close()
        return jsonify({
            'total': 0, 'distribution': {},
            'averages': {'polarity': 0, 'subjectivity': 0, 'confidence': 0},
            'emotions': {}, 'languages': {}, 'daily': [], 'top_keywords': []
        })

    c.execute('SELECT sentiment, COUNT(*) as cnt FROM analyses GROUP BY sentiment')
    distribution = {row['sentiment']: row['cnt'] for row in c.fetchall()}

    c.execute('''SELECT AVG(polarity) as avg_pol,
                        AVG(subjectivity) as avg_sub,
                        AVG(confidence) as avg_conf,
                        AVG(word_count) as avg_words
                 FROM analyses''')
    row = c.fetchone()
    averages = {
        'polarity': round(row['avg_pol'] or 0, 3),
        'subjectivity': round(row['avg_sub'] or 0, 3),
        'confidence': round(row['avg_conf'] or 0, 1),
        'word_count': round(row['avg_words'] or 0, 1)
    }

    c.execute('SELECT emotion, COUNT(*) as cnt FROM analyses GROUP BY emotion')
    emotions = {row['emotion']: row['cnt'] for row in c.fetchall()}

    c.execute('SELECT language, COUNT(*) as cnt FROM analyses GROUP BY language')
    languages = {row['language']: row['cnt'] for row in c.fetchall()}

    c.execute('''SELECT date(created_at) as day,
                        COUNT(*) as cnt,
                        AVG(polarity) as avg_polarity
                 FROM analyses
                 WHERE created_at >= date('now', '-14 days')
                 GROUP BY day ORDER BY day ASC''')
    daily = [dict(row) for row in c.fetchall()]

    keyword_counter = Counter()
    c.execute('SELECT keywords FROM analyses ORDER BY created_at DESC LIMIT 500')
    for row in c.fetchall():
        try:
            kws = json.loads(row['keywords'] or '[]')
            for kw in kws:
                keyword_counter[kw['word']] += kw.get('count', 1)
        except Exception:
            pass

    top_keywords = [{'word': w, 'count': cnt}
                    for w, cnt in keyword_counter.most_common(20)]

    conn.close()

    return jsonify({
        'total': total,
        'distribution': distribution,
        'averages': averages,
        'emotions': emotions,
        'languages': languages,
        'daily': daily,
        'top_keywords': top_keywords
    })


@app.route('/api/stats/trend', methods=['GET'])
def get_trend():
    days = request.args.get('days', 30, type=int)
    since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT date(created_at) as day,
                        AVG(polarity) as avg_polarity,
                        COUNT(*) as cnt
                 FROM analyses
                 WHERE created_at >= ?
                 GROUP BY day ORDER BY day ASC''', (since,))
    trend = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({'trend': trend, 'days': days})


@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, text, sentiment, polarity, subjectivity, confidence, emotion, language, word_count, created_at FROM analyses ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Text', 'Sentiment', 'Polarity', 'Subjectivity',
                     'Confidence', 'Emotion', 'Language', 'Words', 'Created'])
    for row in rows:
        writer.writerow(tuple(row))

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = \
        f'attachment; filename=sentiment_{datetime.now().strftime("%Y%m%d")}.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


@app.route('/api/export/json', methods=['GET'])
def export_json():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM analyses ORDER BY created_at DESC')
    rows = [dict(row) for row in c.fetchall()]
    conn.close()

    response = make_response(json.dumps(rows, indent=2))
    response.headers['Content-Disposition'] = \
        f'attachment; filename=sentiment_{datetime.now().strftime("%Y%m%d")}.json'
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/api/examples', methods=['GET'])
def get_examples():
    return jsonify({
        'examples': [
            "I absolutely love this product! It exceeded all my expectations!",
            "The service was okay, nothing special but not bad either.",
            "This is the worst experience I've ever had. Completely disappointed.",
            "Amazing quality and fast delivery. Highly recommend to everyone!",
            "The food was cold and the waiter was rude. Never coming back.",
            "It's fine. Does what it's supposed to do.",
            "Best purchase I've made this year! Incredible value for money!",
            "Terrible customer support. They never responded to my emails.",
            "Pretty good overall, but could use some improvements.",
            "Outstanding! I'm blown away by how great this is!",
            "Not bad at all, actually quite good.",
            "I don't like this at all. Very disappointing.",
            "This is not good. Not good at all.",
            "The product is amazing but the shipping was slow.",
            "Beautiful design, works perfectly, and the price is great!"
        ]
    })


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': VERSION,
        'engine': 'custom-lexicon'
    })


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    init_db()
    print("=" * 60)
    print(f"🎭 AI Sentiment Analysis v{VERSION}")
    print("=" * 60)
    print("🌐 Server:     http://localhost:5000")
    print("📊 Dashboard:  http://localhost:5000")
    print("🔧 Health:     http://localhost:5000/api/health")
    print("⚡ Engine:     Custom Lexicon (no external deps)")
    print("=" * 60)
    app.run(debug=True, port=5000, host='0.0.0.0')