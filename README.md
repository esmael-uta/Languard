## **Languard**
echo "# Langaurd - AI Language Preservation Platform

## Overview
Langaurd is an AI-powered platform designed to preserve and revitalize endangered Malaysian languages, particularly Orang Asli languages. Our solution leverages Amazon Web Services combined with modern AI technologies to create a comprehensive ecosystem for language preservation, education, and digital immortality.

## Features
- 🔉 Audio Translation (MP3, WAV, M4A, FLAC)
- 📄 Document Translation (PDF, DOCX, TXT)
- 🎥 Video Translation (MP4, MOV, AVI, MKV)
- 📚 Malay-English Flashcards
- 📖 Cultural Stories Repository
- 🌐 URL Upload Support

## Technology Stack
- Backend: Python Flask
- AWS Services: S3, Transcribe, Polly, Comprehend
- Translation: Google Translate API + AWS Translate
- Frontend: HTML5, CSS3, Bootstrap 5
- File Processing: PyPDF2, python-docx, MoviePy

## Installation

1. Clone the repository:
\`\`\`bash
git clone https://github.com/esmael-uta/langaurd.git
cd langaurd
\`\`\`

2. Create a virtual environment:
\`\`\`bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
\`\`\`

3. Install dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

4. Set up environment variables (create a .env file):
\`\`\`
AWS_PROFILE=your_aws_profile
FLASK_SECRET_KEY=your_secret_key
\`\`\`

5. Run the application:
\`\`\`bash
python app.py
\`\`\`

## Project Structure
\`\`\`
langaurd/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── README.md             # Project documentation
├── static/               # Static assets (CSS, JS, images)
│   └── css/
│       └── style.css     # Custom styles
├── templates/            # HTML templates
│   ├── index.html        # Home page
│   ├── audio_translation.html
│   ├── document_translation.html
│   ├── video_translation.html
│   ├── flashcards.html   # Flashcards feature
│   ├── cultural_stories.html # Stories feature
│   └── results.html      # Results page
├── uploads/              # File uploads (not in git)
└── outputs/              # Processed outputs (not in git)
\`\`\`

## Usage
1. Open your browser and navigate to http://localhost:5000
2. Choose your desired translation feature
3. Upload a file or provide a URL
4. Select source and target languages
5. View and download results

## AWS Setup
To use AWS services, you need to:
1. Set up an AWS account
2. Configure AWS CLI with your credentials
3. Create an S3 bucket for file storage
4. Set up necessary IAM permissions for Transcribe, Polly, and Comprehend

## Contributing
We welcome contributions! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License
This project is licensed under the MIT License.

## Acknowledgments
- Amazon Web Services for AI/ML capabilities
- Google Translate API for translation services
- Bootstrap for UI components
- Flask community for web framework" > README.md