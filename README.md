# SpendWise - AI-Powered Personal Finance Analysis

SpendWise is an intelligent personal finance tool that extracts and analyzes bank statements from PDFs to provide insights into spending habits, income trends, and financial health.

## 🚀 Features

- **PDF Statement Parsing**: Automatically extracts transaction data from bank statement PDFs
- **AI-Powered Categorization**: Uses machine learning to categorize transactions into spending categories
- **Anomaly Detection**: Identifies unusual spending patterns using isolation forest algorithm
- **Financial Insights**: Provides intelligent insights about spending habits and financial health
- **Beautiful UI**: Modern, responsive web interface with drag-and-drop file upload

## 🛠️ Technology Stack

- **Backend**: Django 4.2, Python 3.8+
- **Frontend**: Bootstrap 5, JavaScript (Vanilla)
- **Machine Learning**: scikit-learn, TF-IDF, Logistic Regression, Isolation Forest
- **PDF Processing**: pdfplumber, PyPDF2
- **Database**: SQLite (for MVP)

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/spend-wise.git
cd spend-wise
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Start the Development Server
```bash
python manage.py runserver
```

### 6. Open in Browser
Navigate to `http://localhost:8000` to access the application.

## 📊 How It Works

### 1. PDF Processing
- Users upload bank statement PDFs (max 1MB)
- The system extracts text using `pdfplumber`
- Transaction data is parsed using regex patterns for dates and amounts

### 2. Machine Learning Analysis
- **Categorization**: TF-IDF + Logistic Regression classifies transactions into categories
- **Anomaly Detection**: Isolation Forest identifies unusual spending patterns
- **Insights Generation**: AI provides spending ratio analysis and recommendations

### 3. Categories Supported
- Food & Dining
- Transportation
- Shopping
- Bills & Utilities
- Entertainment
- Healthcare
- Other

## 🧠 Machine Learning Models

### Transaction Categorization
```python
# TF-IDF Vectorizer for text feature extraction
vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')

# Logistic Regression for classification
classifier = LogisticRegression(random_state=42, max_iter=1000)
```

### Anomaly Detection
```python
# Isolation Forest for detecting unusual transactions
anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
```

## 📁 Project Structure

```
spend-wise/
├── spendwise/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── analyzer/                  # Main Django app
│   ├── models.py             # Database models
│   ├── views.py              # API endpoints
│   ├── urls.py               # URL routing
│   └── services/             # Core business logic
│       ├── pdf_parser.py     # PDF extraction
│       └── ml_analyzer.py    # ML analysis
├── templates/                 # HTML templates
│   └── analyzer/
│       └── index.html        # Main upload page
├── requirements.txt           # Python dependencies
├── manage.py                 # Django management
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### File Upload Settings
- Maximum file size: 1MB
- Supported format: PDF only
- Temporary file storage with automatic cleanup

## 🚀 Deployment

### Railway (Recommended)
1. Connect your GitHub repository to Railway
2. Railway will automatically detect Django and install dependencies
3. Set environment variables in Railway dashboard
4. Deploy!

### Render
1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn spendwise.wsgi:application`
5. Deploy!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- [ ] Support for multiple bank formats
- [ ] Advanced ML models (BERT, Transformers)
- [ ] Historical trend analysis
- [ ] Budget recommendations
- [ ] Export functionality
- [ ] Mobile app
- [ ] Real-time notifications

## 🐛 Known Issues

- PDF parsing accuracy depends on statement format
- ML models need more training data for better accuracy
- Limited to English transaction descriptions

## 📞 Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/abdulahadakram/spend-wise.git) page
2. Create a new issue with detailed description
3. Include error logs and steps to reproduce

## 🙏 Acknowledgments

- Django community for the excellent web framework
- scikit-learn team for ML tools
- Bootstrap team for the beautiful UI components
- All contributors who help improve this project

---

**Made with ❤️ for the open source community** 