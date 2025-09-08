# Coursera AI Agent - Lead Generation & Course Recommendation System

A comprehensive AI-powered lead generation system that discovers institutions, analyzes their websites, recommends appropriate courses, and extracts contact information for sales outreach.

## 🎯 Project Overview

This system automates the entire lead generation pipeline for a course-selling company, from discovering potential customers to providing actionable contact information. It uses Google Places API for lead discovery, AI models (Gemini & Perplexity) for content analysis, and intelligent web scraping for data extraction.

## 🏗️ System Architecture

The system consists of 3 main Python scripts that work sequentially:

```
1_institutions_list_fetcher.py → 2_coursera_agent.py → 3_output_cleaner.py
```

## 📋 Prerequisites

### Required API Keys

- **Google Places API Key**: For discovering institutions
- **Gemini API Key**: For AI-powered content analysis
- **Perplexity API Key**: For deep web research and contact extraction

### Python Dependencies

```bash
pip install requests beautifulsoup4 pandas python-dotenv
```

### Environment Setup

Create a `.env` file in the project root:

```env
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

## 🚀 Sequential Workflow

### Step 1: Institution Discovery (`1_institutions_list_fetcher.py`)

**Purpose**: Discovers potential customer institutions using Google Places API

**What it does**:

- Searches for institutions in specified cities (Bangalore, Delhi)
- Targets two types: "Corporates" and "Schools"
- Uses intelligent search queries:
  - **Corporates**: "Software companies", "Sales and marketing companies"
  - **Schools**: "Engineering colleges", "Business schools"
- Fetches detailed information including websites, phone numbers, and addresses
- Filters institutions to only include those with valid websites
- Categorizes locations (Bangalore vs Delhi) based on keywords

**Output**: `1_discovered_leads.csv`

- Institution Name
- Institution Type (Corporates/Schools)
- Website URL
- Location (Bangalore/Delhi)
- Phone Number

**Key Features**:

- Rate limiting to respect Google Places API limits
- Pagination handling for comprehensive results
- Duplicate prevention using place IDs
- Robust error handling and retry logic

### Step 2: AI-Powered Analysis (`2_coursera_agent.py`)

**Purpose**: Analyzes each institution's website to recommend courses and extract contact information

**What it does**:

#### 2.1 Course Recommendation Analysis

- **Website Crawling**: Intelligently crawls institution websites with anti-bot protection bypass
- **Content Analysis**: Uses Gemini AI to analyze website content
- **Course Classification**: Determines whether to recommend:
  - **Programming Course**: For technical institutions, engineering colleges, software companies
  - **Sales Course**: For business schools, marketing companies, sales organizations
- **Confidence Scoring**: Provides 0-100 confidence scores for recommendations

#### 2.2 Contact Information Extraction

- **Targeted Research**: Uses Perplexity API for deep web research
- **Course-Specific Targeting**:
  - **Programming Course**: Targets CTOs, technical directors, IT managers, faculty heads
  - **Sales Course**: Targets sales managers, business development directors, marketing managers
- **Contact Parsing**: Extracts names, titles, emails, and phone numbers
- **Quality Filtering**: Only includes contacts with valid email or phone information

**Output**: Individual JSON files in `outputs/` directory

```json
{
  "course_recommendation": {
    "recommended_course": "Programming Course",
    "recommendation_reasoning": "Technical content and engineering focus",
    "recommendation_score": 95
  },
  "contact_info": {
    "contacts": [
      {
        "name": "Dr. John Smith",
        "title": "Head of Computer Science",
        "email": "john.smith@university.edu",
        "phone": "+91-9876543210"
      }
    ]
  },
  "metadata": {
    "institution_name": "Example University",
    "website_url": "https://example.edu",
    "location": "Delhi",
    "phone": "+91-11-12345678",
    "institution_type": "Schools",
    "processed_at": "2025-09-08T10:30:00"
  }
}
```

**Key Features**:

- Advanced web scraping with multiple fallback strategies
- AI-powered URL filtering for relevant content
- Intelligent content analysis with confidence scoring
- Comprehensive contact extraction with role-based targeting
- Robust error handling and retry mechanisms

### Step 3: Data Cleaning (`3_output_cleaner.py`)

**Purpose**: Filters and cleans the analysis results to include only high-quality leads

**What it does**:

- Processes all JSON files from the `outputs/` directory
- Filters files that contain at least one valid contact entry
- Creates cleaned versions in `cleaned_outputs/` directory
- Provides detailed processing statistics

**Output**: `cleaned_outputs/` directory with filtered JSON files

**Key Features**:

- Quality filtering based on contact availability
- Comprehensive error handling for malformed files
- Detailed progress reporting with success/failure indicators
- UTF-8 encoding support for international characters

## 📊 Usage Instructions

### 1. Run Institution Discovery

```bash
python 1_institutions_list_fetcher.py
```

This will create `1_discovered_leads.csv` with discovered institutions.

### 2. Run AI Analysis

```bash
python 2_coursera_agent.py
```

This will process all institutions from the CSV file and create individual JSON files in `outputs/`.

### 3. Clean and Filter Results

```bash
python 3_output_cleaner.py
```

This will create filtered results in `cleaned_outputs/` directory.

## 📈 Performance Metrics

Based on the latest run:

- **Total Institutions Discovered**: 299
- **Successfully Processed**: 151 (50.5% success rate)
- **Files with Valid Contacts**: 151
- **Average Processing Time**: ~2-3 minutes per institution

## 🔧 Configuration

### Search Parameters (in `constants.py`)

- **Cities**: Bangalore, Delhi
- **Institution Types**: Corporates, Schools
- **Max Pages per Query**: 3
- **Rate Limiting**: 100ms between API calls

### AI Model Settings

- **Gemini Model**: gemini-2.5-flash
- **Perplexity Model**: sonar-pro
- **Max Tokens**: 4000
- **Temperature**: 0.2 (for consistent results)

## 📁 Output Structure

```
project/
├── 1_discovered_leads.csv          # Initial institution list
├── outputs/                         # Raw analysis results
│   ├── institution1.com.json
│   ├── institution2.edu.json
│   └── ...
├── cleaned_outputs/                 # Filtered results
│   ├── institution1.com.json
│   ├── institution2.edu.json
│   └── ...
└── constants.py                     # Configuration file
```

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure all API keys are properly set in `.env` file
2. **Rate Limiting**: The system includes built-in rate limiting, but monitor API usage
3. **Website Access**: Some websites may block automated access; the system includes fallback strategies
4. **Memory Usage**: For large datasets, consider processing in batches

### Error Handling

- All scripts include comprehensive error handling
- Failed requests are logged with detailed error messages
- The system continues processing even if individual institutions fail

## 🔒 Security & Compliance

- **Rate Limiting**: Respects API rate limits to avoid service disruption
- **User Agent Rotation**: Uses realistic browser headers to avoid detection
- **Data Privacy**: Only extracts publicly available information
- **Error Logging**: Comprehensive logging for debugging without exposing sensitive data

## 📝 License

This project is for educational and research purposes. Ensure compliance with:

- Google Places API Terms of Service
- Website Terms of Service for scraped content
- Data protection regulations in your jurisdiction

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Review error logs in the console output
3. Ensure all API keys are valid and have sufficient quotas
4. Verify network connectivity for web scraping operations

---

**Note**: This system is designed for legitimate business lead generation. Always respect website terms of service and applicable laws when using web scraping capabilities.
