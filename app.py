import os
import time
import json
import re
import boto3
import uuid
import requests
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError
import PyPDF2
import docx
from moviepy.editor import VideoFileClip
import speech_recognition as sr
import urllib.request
from urllib.parse import urlparse

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'langaurd-secret-key-2023'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# -------------------------
# Config
# -------------------------
AWS_PROFILE = "aiu-sso"
BUCKET_NAME = "language-preserve-demo-bucket-12345"

# Amazon Transcribe language codes
TRANSCRIBE_LANGUAGE_CODES = {
    'english': 'en-US',
    'malay': 'ms-MY',
    'spanish': 'es-US',
    'french': 'fr-FR',
    'german': 'de-DE',
    'arabic': 'ar-SA',
    'hindi': 'hi-IN',
    'chinese': 'zh-CN',
    'japanese': 'ja-JP',
    'korean': 'ko-KR',
    'portuguese': 'pt-BR',
    'russian': 'ru-RU',
    'italian': 'it-IT'
}

# Standard language codes for translation
STANDARD_LANGUAGE_CODES = {
    'english': 'en',
    'malay': 'ms',
    'spanish': 'es',
    'french': 'fr',
    'german': 'de',
    'arabic': 'ar',
    'hindi': 'hi',
    'chinese': 'zh-CN',
    'japanese': 'ja',
    'korean': 'ko',
    'portuguese': 'pt',
    'russian': 'ru',
    'italian': 'it'
}

# Reverse mapping for language codes
LANGUAGE_CODE_TO_NAME = {v: k for k, v in STANDARD_LANGUAGE_CODES.items()}

# Polly voices by language
POLLY_VOICES = {
    'en': 'Joanna',
    'es': 'Lupe',
    'fr': 'Lea',
    'de': 'Vicki',
    'it': 'Bianca',
    'pt': 'Camila',
    'ru': 'Tatyana',
    'ja': 'Mizuki',
    'ko': 'Seoyeon',
    'zh-CN': 'Zhiyu'
}

# Allowed file extensions
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'docx', 'txt'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

# Sample flashcards data for Malay-English
MALAY_ENGLISH_FLASHCARDS = [
    {'malay': 'selamat pagi', 'english': 'good morning', 'pronunciation': 'suh-lah-maht pah-gee', 'category': 'greetings'},
    {'malay': 'terima kasih', 'english': 'thank you', 'pronunciation': 'tuh-ree-mah kah-seeh', 'category': 'greetings'},
    {'malay': 'apa khabar', 'english': 'how are you', 'pronunciation': 'ah-pah kah-bar', 'category': 'greetings'},
    {'malay': 'nama saya', 'english': 'my name is', 'pronunciation': 'nah-mah sah-yah', 'category': 'introductions'},
    {'malay': 'saya suka', 'english': 'I like', 'pronunciation': 'sah-yah soo-kah', 'category': 'expressions'},
    {'malay': 'saya tidak suka', 'english': 'I don\'t like', 'pronunciation': 'sah-yah tee-dak soo-kah', 'category': 'expressions'},
    {'malay': 'berapa harga', 'english': 'how much does it cost', 'pronunciation': 'buh-rap-pah har-gah', 'category': 'shopping'},
    {'malay': 'di mana', 'english': 'where is', 'pronunciation': 'dee mah-nah', 'category': 'directions'},
    {'malay': 'tolong', 'english': 'please help', 'pronunciation': 'toh-long', 'category': 'emergency'},
    {'malay': 'saya faham', 'english': 'I understand', 'pronunciation': 'sah-yah fah-ham', 'category': 'conversation'}
]

# Sample cultural stories
MALAY_CULTURAL_STORIES = [
    {
        'title': 'The Legend of Hang Tuah',
        'malay_title': 'Lagenda Hang Tuah',
        'content': '''
Hang Tuah adalah seorang pahlawan Melayu yang terkenal dari Kesultanan Melaka. 
Dia dikenali dengan kesetiaannya yang tidak berbelah bahagi kepada Sultan Melaka 
dan kehebatannya dalam seni mempertahankan diri. Kata-kata masyhurnya, 
"Takkan Melayu hilang di dunia," menjadi simbol semangat dan ketahanan bangsa Melayu.
        
Hang Tuah dan empat sahabatnya - Hang Jebat, Hang Kasturi, Hang Lekir, dan Hang Lekiu - 
adalah pahlawan yang gagah berani yang mempertahankan Melaka dari pelbagai ancaman.
''',
        'english_translation': '''
Hang Tuah was a famous Malay warrior from the Malacca Sultanate. 
He was known for his unwavering loyalty to the Sultan of Malacca 
and his prowess in martial arts. His famous words, 
"Never shall the Malays vanish from the face of the earth," became a symbol of the spirit and resilience of the Malay people.
        
Hang Tuah and his four companions - Hang Jebat, Hang Kasturi, Hang Lekir, and Hang Lekiu - 
were brave warriors who defended Malacca from various threats.
''',
        'category': 'legends'
    },
    {
        'title': 'The Story of Bawang Putih and Bawang Merah',
        'malay_title': 'Cerita Bawang Putih dan Bawang Merah',
        'content': '''
Ini adalah cerita rakyat tentang dua gadis bersaudara, Bawang Putih yang baik hati 
dan Bawang Merah yang jahat. Ibu tiri dan Bawang Merah selalu menyusahkan Bawang Putih.
        
Suatu hari, Bawang Putih menemui labu ajaib yang berisi emas dan permata, 
sementara Bawang Merah menemui labu yang berisi ular dan kala jengking. 
Cerita ini mengajar tentang nilai kebaikan dan balasan bagi perbuatan jahat.
''',
        'english_translation': '''
This is a folk tale about two sisters, the kind-hearted Bawang Putih 
and the wicked Bawang Merah. The stepmother and Bawang Merah always made life difficult for Bawang Putih.
        
One day, Bawang Putih found a magical pumpkin filled with gold and jewels, 
while Bawang Merah found a pumpkin filled with snakes and scorpions. 
This story teaches about the value of goodness and the consequences of wicked deeds.
''',
        'category': 'folktales'
    },
    {
        'title': 'The Origin of the Name Malaysia',
        'malay_title': 'Asal Usul Nama Malaysia',
        'content': '''
Nama "Malaysia" dipercayai berasal dari gabungan perkataan "Malay" dan Latin-Greek "-sia". 
Perkataan "Malay" sendiri berasal dari Sungai Melayu di Sumatera, atau mungkin dari 
perkataan "malay" yang bermaksud "orang gunung" dalam bahasa tempatan.
        
Pada tahun 1963, nama Malaysia dipilih untuk negara baru yang merdeka yang terdiri dari 
Persekutuan Tanah Melayu, Singapura, Sabah, dan Sarawak. Nama ini melambangkan 
penyatuan berbagai wilayah dan budaya dalam satu negara.
''',
        'english_translation': '''
The name "Malaysia" is believed to come from a combination of the word "Malay" and the Latin-Greek "-sia". 
The word "Malay" itself originates from the Melayu River in Sumatra, or possibly from 
the word "malay" meaning "mountain people" in the local language.
        
In 1963, the name Malaysia was chosen for the new independent nation consisting of 
the Federation of Malaya, Singapore, Sabah, and Sarawak. This name symbolizes 
the unification of various regions and cultures into one nation.
''',
        'category': 'history'
    }
]

# -------------------------
# AWS clients
# -------------------------
try:
    session = boto3.Session(profile_name=AWS_PROFILE)
    s3_client = session.client("s3")
    transcribe_client = session.client("transcribe")
    polly_client = session.client("polly")
    comprehend_client = session.client("comprehend")
    textract_client = session.client("textract")
except Exception as e:
    print(f"AWS initialization error: {e}")
    s3_client = transcribe_client = polly_client = comprehend_client = textract_client = None

# -------------------------
# Translation Service
# -------------------------
class TranslationService:
    def __init__(self):
        self.fallback_url = "https://translate.googleapis.com/translate_a/single"
    
    def translate_text(self, text, source_lang, target_lang):
        """
        Translate text using multiple fallback methods
        """
        # Method 1: Try Google Translate API directly
        try:
            return self._google_translate_direct(text, source_lang, target_lang)
        except Exception as e:
            print(f"Google Translate direct failed: {e}")
        
        # Method 2: Try AWS Translate (if available)
        try:
            return self._aws_translate(text, source_lang, target_lang)
        except Exception as e:
            print(f"AWS Translate failed: {e}")
        
        # Method 3: Simple word mapping fallback (for demo purposes)
        try:
            return self._simple_translation_fallback(text, source_lang, target_lang)
        except Exception as e:
            print(f"Fallback translation failed: {e}")
            raise Exception("All translation methods failed")
    
    def _google_translate_direct(self, text, source_lang, target_lang):
        """Direct HTTP call to Google Translate"""
        params = {
            'client': 'gtx',
            'sl': source_lang,
            'tl': target_lang,
            'dt': 't',
            'q': text
        }
        
        response = requests.get(self.fallback_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0 and data[0]:
            # Extract translated text from the response
            translated_parts = [part[0] for part in data[0] if part[0]]
            return ' '.join(translated_parts)
        else:
            raise Exception("Empty response from Google Translate")
    
    def _aws_translate(self, text, source_lang, target_lang):
        """Use AWS Translate service"""
        try:
            translate_client = session.client('translate')
            response = translate_client.translate_text(
                Text=text,
                SourceLanguageCode=source_lang,
                TargetLanguageCode=target_lang
            )
            return response['TranslatedText']
        except Exception as e:
            # Check if it's an access denied error
            if "AccessDenied" in str(e):
                print("AWS Translate access denied. Using fallback methods.")
            raise e
    
    def _simple_translation_fallback(self, text, source_lang, target_lang):
        """Simple fallback translation for demo purposes"""
        # This is a very basic fallback and should be replaced with proper translation
        print(f"Using fallback translation from {source_lang} to {target_lang}")
        
        # For demo purposes, return the original text with a note
        if source_lang != target_lang:
            return f"[Translation from {source_lang} to {target_lang}] {text}"
        return text

# Initialize translation service
translation_service = TranslationService()

# -------------------------
# Helpers
# -------------------------
def allowed_file(filename, file_type):
    if file_type == 'audio':
        extensions = ALLOWED_AUDIO_EXTENSIONS
    elif file_type == 'document':
        extensions = ALLOWED_DOCUMENT_EXTENSIONS
    elif file_type == 'video':
        extensions = ALLOWED_VIDEO_EXTENSIONS
    elif file_type == 'image':
        extensions = ALLOWED_IMAGE_EXTENSIONS
    else:
        return False
        
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def download_file_from_url(url, file_type):
    """Download file from URL and save it locally"""
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL")
        
        # Generate unique filename
        file_ext = os.path.splitext(parsed_url.path)[1] or f".{file_type}"
        filename = f"{uuid.uuid4().hex}{file_ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Download the file
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        
        return filepath, filename
    except Exception as e:
        raise Exception(f"Failed to download file from URL: {str(e)}")

def upload_file_to_s3(local_path: str, bucket: str, key: str):
    """Upload local file to S3."""
    try:
        s3_client.upload_file(local_path, bucket, key)
        return True
    except Exception as e:
        print(f"Upload error: {e}")
        return False

def wait_for_transcribe_and_get_transcript(bucket: str, job_name: str, timeout=600, poll_interval=5):
    """Poll for transcription job completion then read the transcript JSON from S3."""
    started = time.time()
    while True:
        try:
            status_resp = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            job = status_resp["TranscriptionJob"]
            status = job["TranscriptionJobStatus"]
            
            if status == "COMPLETED":
                break
            elif status == "FAILED":
                raise RuntimeError(f"Transcription job failed: {job.get('FailureReason')}")
                
            if time.time() - started > timeout:
                raise TimeoutError("Transcription job timed out.")
                
            time.sleep(poll_interval)
        except transcribe_client.exceptions.BadRequestException:
            time.sleep(poll_interval)

    transcript_s3_key = f"{job_name}.json"
    
    # Read from S3
    obj = s3_client.get_object(Bucket=bucket, Key=transcript_s3_key)
    transcript_json = obj["Body"].read().decode("utf-8")
    data = json.loads(transcript_json)
    text = data["results"]["transcripts"][0]["transcript"]
    return text

def detect_language(text: str):
    """Detect the language of the text using Amazon Comprehend."""
    try:
        response = comprehend_client.detect_dominant_language(Text=text)
        languages = response['Languages']
        if languages:
            top_language = max(languages, key=lambda x: x['Score'])
            lang_code = top_language['LanguageCode']
            confidence = top_language['Score']
            
            lang_name = LANGUAGE_CODE_TO_NAME.get(lang_code, "unknown")
            return lang_code, lang_name, confidence
        return None, "unknown", 0
    except Exception:
        # Fallback detection
        if any(word in text.lower() for word in ['the', 'and', 'is', 'are', 'to']):
            return 'en', 'english', 0.9
        elif any(word in text.lower() for word in ['dan', 'atau', 'yang', 'di', 'akan']):
            return 'ms', 'malay', 0.9
        else:
            return 'en', 'english', 0.5

def clean_translation(text: str):
    """Post-process translation to improve quality."""
    # Remove incorrectly added periods
    text = re.sub(r'(\w)\.(\w)', r'\1\2', text)
    
    # Common fixes
    fixes = [
        (r'\bMiz\b', 'We'),
        (r'Senses Social Science', 'Social Sciences'),
        (r'\bwe has\b', 'we have'),
        (r'\bi\b', 'I'),
        (r'\bscis\b', 'SCIS'),
        (r'\bsuss\b', 'SUSS'),
        (r'\.\.', '.'),
        (r' +', ' '),
    ]
    
    for pattern, replacement in fixes:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Fix sentence boundaries
    text = re.sub(r'([a-z])([A-Z])', r'\1. \2', text)
    
    # Capitalize sentences
    sentences = text.split('. ')
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            sentence = sentence[0].upper() + sentence[1:]
            cleaned_sentences.append(sentence)
    
    text = '. '.join(cleaned_sentences)
    
    if not text.endswith('.'):
        text += '.'
        
    return text

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")
    return text

def extract_text_from_docx(docx_path):
    """Extract text from DOCX file."""
    try:
        doc = docx.Document(docx_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        raise RuntimeError(f"DOCX extraction failed: {e}")

def extract_text_from_image(image_path):
    """Extract text from image using AWS Textract."""
    try:
        with open(image_path, 'rb') as document:
            image_bytes = bytearray(document.read())
        
        response = textract_client.detect_document_text(Document={'Bytes': image_bytes})
        
        text = ""
        for item in response["Blocks"]:
            if item["BlockType"] == "LINE":
                text += item["Text"] + "\n"
                
        return text
    except Exception as e:
        raise RuntimeError(f"Textract failed: {e}")

def extract_audio_from_video(video_path):
    """Extract audio from video file."""
    try:
        # Create a temporary file for audio
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4().hex}.wav")
        
        # Extract audio using moviepy
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path, verbose=False, logger=None)
        
        return audio_path
    except Exception as e:
        raise RuntimeError(f"Audio extraction failed: {e}")

def transcribe_audio(audio_path: str, source_lang: str):
    """Transcribe audio file."""
    job_name = f"transcribe-job-{uuid.uuid4().hex[:8]}"
    s3_key = f"audio_{job_name}.mp3"
    
    # Upload to S3
    if not upload_file_to_s3(audio_path, BUCKET_NAME, s3_key):
        raise RuntimeError("Failed to upload audio to S3")
    
    # Start transcription
    transcribe_params = {
        "TranscriptionJobName": job_name,
        "Media": {"MediaFileUri": f"s3://{BUCKET_NAME}/{s3_key}"},
        "MediaFormat": "mp3",
        "OutputBucketName": BUCKET_NAME,
    }
    
    if source_lang != "auto":
        # Convert standard language code to Transcribe language code
        transcribe_lang_code = None
        for name, code in STANDARD_LANGUAGE_CODES.items():
            if code == source_lang:
                transcribe_lang_code = TRANSCRIBE_LANGUAGE_CODES.get(name)
                break
        
        if transcribe_lang_code:
            transcribe_params["LanguageCode"] = transcribe_lang_code
        else:
            transcribe_params["LanguageCode"] = 'en-US'
    else:
        transcribe_params["IdentifyLanguage"] = True
        transcribe_params["LanguageOptions"] = list(TRANSCRIBE_LANGUAGE_CODES.values())
    
    try:
        transcribe_client.start_transcription_job(**transcribe_params)
        transcribed_text = wait_for_transcribe_and_get_transcript(BUCKET_NAME, job_name)
        return transcribed_text
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")

def translate_text(text: str, source_lang: str, target_lang: str):
    """Translate text using our translation service."""
    try:
        translated_text = translation_service.translate_text(text, source_lang, target_lang)
        return clean_translation(translated_text)
    except Exception as e:
        raise RuntimeError(f"Translation failed: {e}")

def text_to_speech(text: str, language_code: str, output_path: str):
    """Convert text to speech."""
    if language_code in POLLY_VOICES:
        # Use Amazon Polly
        voice_id = POLLY_VOICES[language_code]
        
        # Split into chunks (Polly has a 3000 character limit)
        max_chunk_size = 2500  # Conservative limit
        if len(text) > max_chunk_size:
            # Simple sentence-based splitting
            sentences = text.split('. ')
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) < max_chunk_size:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence + ". "
            
            if current_chunk:
                chunks.append(current_chunk)
        else:
            chunks = [text]
        
        # Process chunks
        audio_data = b''
        for chunk in chunks:
            response = polly_client.synthesize_speech(
                Text=chunk,
                OutputFormat="mp3",
                VoiceId=voice_id
            )
            audio_data += response["AudioStream"].read()
        
        with open(output_path, "wb") as f:
            f.write(audio_data)
    else:
        # Use gTTS as fallback
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=language_code, slow=False)
            tts.save(output_path)
        except Exception as e:
            raise RuntimeError(f"Text-to-speech failed: {e}")

# -------------------------
# Flashcard Functions
# -------------------------
def get_flashcards_by_category(category=None):
    """Get flashcards, optionally filtered by category"""
    if category and category != 'all':
        return [card for card in MALAY_ENGLISH_FLASHCARDS if card['category'] == category]
    return MALAY_ENGLISH_FLASHCARDS

def get_flashcard_categories():
    """Get unique categories from flashcards"""
    categories = set(card['category'] for card in MALAY_ENGLISH_FLASHCARDS)
    return sorted(categories)

# -------------------------
# Story Functions
# -------------------------
def get_stories_by_category(category=None):
    """Get stories, optionally filtered by category"""
    if category and category != 'all':
        return [story for story in MALAY_CULTURAL_STORIES if story['category'] == category]
    return MALAY_CULTURAL_STORIES

def get_story_categories():
    """Get unique categories from stories"""
    categories = set(story['category'] for story in MALAY_CULTURAL_STORIES)
    return sorted(categories)

# -------------------------
# Flask Routes
# -------------------------
@app.route('/')
def index():
    return render_template('index.html', languages=STANDARD_LANGUAGE_CODES)

@app.route('/audio-translation')
def audio_translation():
    return render_template('audio_translation.html', languages=STANDARD_LANGUAGE_CODES)

@app.route('/document-translation')
def document_translation():
    return render_template('document_translation.html', languages=STANDARD_LANGUAGE_CODES)

@app.route('/video-translation')
def video_translation():
    return render_template('video_translation.html', languages=STANDARD_LANGUAGE_CODES)

@app.route('/flashcards')
def flashcards():
    category = request.args.get('category', 'all')
    flashcards = get_flashcards_by_category(category)
    categories = get_flashcard_categories()
    
    return render_template('flashcards.html', 
                         flashcards=flashcards,
                         categories=categories,
                         selected_category=category)

@app.route('/cultural-stories')
def cultural_stories():
    category = request.args.get('category', 'all')
    stories = get_stories_by_category(category)
    categories = get_story_categories()
    
    return render_template('cultural_stories.html', 
                         stories=stories,
                         categories=categories,
                         selected_category=category)

@app.route('/ancient-texts')
def ancient_texts():
    flash('Ancient Texts Decoder is coming soon!')
    return redirect(url_for('index'))

@app.route('/ai-tutor')
def ai_tutor():
    flash('AI Tutor feature is coming soon!')
    return redirect(url_for('index'))

@app.route('/translate-audio', methods=['POST'])
def translate_audio():
    # Check if file was uploaded or URL was provided
    file = None
    file_url = request.form.get('file_url', '').strip()
    
    if 'audio_file' in request.files:
        file = request.files['audio_file']
        if file.filename == '':
            file = None
    
    if not file and not file_url:
        flash('Please either upload a file or provide a URL')
        return redirect(url_for('audio_translation'))
    
    # Get form data
    source_lang = request.form.get('source_lang', 'auto')
    target_lang = request.form.get('target_lang', 'en')
    
    # Generate unique ID for this session
    session_id = uuid.uuid4().hex[:8]
    
    try:
        # Handle file upload or URL download
        if file:
            if not allowed_file(file.filename, 'audio'):
                flash('Invalid file type. Please upload MP3, WAV, M4A, or FLAC.')
                return redirect(url_for('audio_translation'))
            
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{secure_filename(file.filename)}")
            file.save(upload_path)
        else:
            # Download from URL
            upload_path, filename = download_file_from_url(file_url, 'audio')
        
        # Step 1: Transcribe audio
        transcribed_text = transcribe_audio(upload_path, source_lang)
        
        # Step 2: Detect language if auto
        if source_lang == "auto":
            detected_lang, lang_name, confidence = detect_language(transcribed_text)
            source_lang = detected_lang
        else:
            detected_lang = source_lang
            lang_name = LANGUAGE_CODE_TO_NAME.get(source_lang, "unknown")
            confidence = 1.0
        
        # Step 3: Translate if needed
        if source_lang == target_lang:
            translated_text = transcribed_text
        else:
            translated_text = translate_text(transcribed_text, source_lang, target_lang)
        
        # Step 4: Convert to speech
        output_audio = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_output.mp3")
        text_to_speech(translated_text, target_lang, output_audio)
        
        # Step 5: Save text files
        transcript_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_transcript.txt")
        translation_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_translation.txt")
        
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcribed_text)
        
        with open(translation_file, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        
        # Prepare results
        results = {
            'session_id': session_id,
            'source_lang': lang_name,
            'target_lang': LANGUAGE_CODE_TO_NAME.get(target_lang, "unknown"),
            'confidence': f"{confidence:.1%}",
            'transcribed_text': transcribed_text,
            'translated_text': translated_text,
            'has_translation': source_lang != target_lang,
            'file_type': 'audio'
        }
        
        return render_template('results.html', **results)
        
    except Exception as e:
        flash(f'Error processing audio: {str(e)}')
        return redirect(url_for('audio_translation'))

@app.route('/translate-document', methods=['POST'])
def translate_document():
    # Check if file was uploaded or URL was provided
    file = None
    file_url = request.form.get('file_url', '').strip()
    
    if 'document_file' in request.files:
        file = request.files['document_file']
        if file.filename == '':
            file = None
    
    if not file and not file_url:
        flash('Please either upload a file or provide a URL')
        return redirect(url_for('document_translation'))
    
    # Get form data
    source_lang = request.form.get('source_lang', 'auto')
    target_lang = request.form.get('target_lang', 'en')
    
    # Generate unique ID for this session
    session_id = uuid.uuid4().hex[:8]
    
    try:
        # Handle file upload or URL download
        if file:
            if not allowed_file(file.filename, 'document'):
                flash('Invalid file type. Please upload PDF, DOCX, or TXT.')
                return redirect(url_for('document_translation'))
            
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{secure_filename(file.filename)}")
            file.save(upload_path)
            
            # Get file extension from uploaded file
            file_ext = file.filename.rsplit('.', 1)[1].lower()
        else:
            # Download from URL
            upload_path, filename = download_file_from_url(file_url, 'document')
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'txt'
        
        # Extract text based on file type
        if file_ext == 'pdf':
            extracted_text = extract_text_from_pdf(upload_path)
        elif file_ext == 'docx':
            extracted_text = extract_text_from_docx(upload_path)
        elif file_ext == 'txt':
            with open(upload_path, 'r', encoding='utf-8') as f:
                extracted_text = f.read()
        else:
            flash('Unsupported document format')
            return redirect(url_for('document_translation'))
        
        # Detect language if auto
        if source_lang == "auto":
            detected_lang, lang_name, confidence = detect_language(extracted_text)
            source_lang = detected_lang
        else:
            detected_lang = source_lang
            lang_name = LANGUAGE_CODE_TO_NAME.get(source_lang, "unknown")
            confidence = 1.0
        
        # Translate if needed
        if source_lang == target_lang:
            translated_text = extracted_text
        else:
            translated_text = translate_text(extracted_text, source_lang, target_lang)
        
        # Save files
        original_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_original.txt")
        translation_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_translation.txt")
        
        with open(original_file, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        with open(translation_file, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        
        # Prepare results
        results = {
            'session_id': session_id,
            'source_lang': lang_name,
            'target_lang': LANGUAGE_CODE_TO_NAME.get(target_lang, "unknown"),
            'confidence': f"{confidence:.1%}",
            'transcribed_text': extracted_text,
            'translated_text': translated_text,
            'has_translation': source_lang != target_lang,
            'file_type': 'document'
        }
        
        return render_template('results.html', **results)
        
    except Exception as e:
        flash(f'Error processing document: {str(e)}')
        return redirect(url_for('document_translation'))

@app.route('/translate-video', methods=['POST'])
def translate_video():
    # Check if file was uploaded or URL was provided
    file = None
    file_url = request.form.get('file_url', '').strip()
    
    if 'video_file' in request.files:
        file = request.files['video_file']
        if file.filename == '':
            file = None
    
    if not file and not file_url:
        flash('Please either upload a file or provide a URL')
        return redirect(url_for('video_translation'))
    
    # Get form data
    source_lang = request.form.get('source_lang', 'auto')
    target_lang = request.form.get('target_lang', 'en')
    
    # Generate unique ID for this session
    session_id = uuid.uuid4().hex[:8]
    
    try:
        # Handle file upload or URL download
        if file:
            if not allowed_file(file.filename, 'video'):
                flash('Invalid file type. Please upload MP4, MOV, AVI, or MKV.')
                return redirect(url_for('video_translation'))
            
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{secure_filename(file.filename)}")
            file.save(upload_path)
        else:
            # Download from URL
            upload_path, filename = download_file_from_url(file_url, 'video')
        
        # Step 1: Extract audio from video
        audio_path = extract_audio_from_video(upload_path)
        
        # Step 2: Transcribe audio
        transcribed_text = transcribe_audio(audio_path, source_lang)
        
        # Step 3: Detect language if auto
        if source_lang == "auto":
            detected_lang, lang_name, confidence = detect_language(transcribed_text)
            source_lang = detected_lang
        else:
            detected_lang = source_lang
            lang_name = LANGUAGE_CODE_TO_NAME.get(source_lang, "unknown")
            confidence = 1.0
        
        # Step 4: Translate if needed
        if source_lang == target_lang:
            translated_text = transcribed_text
        else:
            translated_text = translate_text(transcribed_text, source_lang, target_lang)
        
        # Step 5: Convert to speech
        output_audio = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_output.mp3")
        text_to_speech(translated_text, target_lang, output_audio)
        
        # Step 6: Save text files
        transcript_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_transcript.txt")
        translation_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_translation.txt")
        
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcribed_text)
        
        with open(translation_file, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        
        # Prepare results
        results = {
            'session_id': session_id,
            'source_lang': lang_name,
            'target_lang': LANGUAGE_CODE_TO_NAME.get(target_lang, "unknown"),
            'confidence': f"{confidence:.1%}",
            'transcribed_text': transcribed_text,
            'translated_text': translated_text,
            'has_translation': source_lang != target_lang,
            'file_type': 'video'
        }
        
        return render_template('results.html', **results)
        
    except Exception as e:
        flash(f'Error processing video: {str(e)}')
        return redirect(url_for('video_translation'))

@app.route('/download/<file_type>/<session_id>')
def download_file(file_type, session_id):
    if file_type == 'transcript':
        filename = f"{session_id}_transcript.txt"
        display_name = "transcript.txt"
    elif file_type == 'translation':
        filename = f"{session_id}_translation.txt"
        display_name = "translation.txt"
    elif file_type == 'audio':
        filename = f"{session_id}_output.mp3"
        display_name = "translated_audio.mp3"
    else:
        flash('Invalid file type')
        return redirect(url_for('index'))
    
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=display_name)
    else:
        flash('File not found')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
