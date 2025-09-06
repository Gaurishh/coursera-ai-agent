# Coursera AI Agent

An AI agent that analyzes websites to recommend either a "Programming Course" or "Sales Course" based on the website content.

## Features

- **Website Analysis**: Crawls websites and extracts text content
- **URL Discovery**: Finds all internal links on a website
- **AI-Powered Recommendations**: Uses Gemini AI to analyze content and make course recommendations
- **Smart Crawling**: Visits multiple pages (up to 15 steps) to gather comprehensive data
- **Intelligent URL Filtering**: Uses AI to select only the most relevant URLs for analysis
- **Contact Information Extraction**: Extracts contact details (names, titles, emails, phones) from websites
- **Early Termination**: Stops when enough data is gathered for a confident recommendation
- **Forced Recommendations**: Makes recommendations even with limited data, assigning lower confidence scores

## Setup

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Set API Key**:
   Set your Gemini API key as an environment variable:

   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="your_actual_api_key_here"

   # Or create a .env file
   echo "GEMINI_API_KEY=your_actual_api_key_here" > .env
   ```

## Usage

### Basic Usage

```python
from coursera_agent import run_agent, get_course_recommendation, get_contact_info

# Analyze a website using the main agent function (returns both course recommendation and contacts)
result = run_agent("example.com")

# Access course recommendation
course_rec = result['course_recommendation']
print(f"Recommended Course: {course_rec['recommended_course']}")
print(f"Reasoning: {course_rec['recommendation_reasoning']}")
print(f"Confidence Score: {course_rec['recommendation_score']}")

# Access contact information
contact_info = result['contact_info']
print(f"Found {len(contact_info['contacts'])} contacts")
for contact in contact_info['contacts']:
    print(f"- {contact.get('name', 'Unknown')}: {contact.get('title', 'No title')}")

# Or use functions directly
recommendation = get_course_recommendation("example.com")
contacts = get_contact_info("example.com", recommendation['recommended_course'])
```

### Command Line Usage

```bash
python coursera_agent.py
```

## How It Works

1. **URL Normalization**: Handles URLs in any format (with/without www, http/https)
2. **Content Extraction**: Extracts clean text from web pages
3. **Link Discovery**: Finds all internal links on the website
4. **Intelligent URL Filtering**: Uses AI to select only the most relevant URLs (e.g., /about, /departments, /courses) while filtering out irrelevant ones (e.g., /sports, /gallery)
5. **Iterative Analysis**: Visits multiple pages to gather comprehensive data
6. **AI Analysis**: Uses Gemini AI to analyze content and determine course recommendation
7. **Smart Termination**: Stops early when confident recommendation is made
8. **Forced Recommendation**: If insufficient data after 15 steps, forces a recommendation with lower confidence (20-50 score)

## API Response Format

The agent returns a dictionary with two main sections:

### Course Recommendation

- `recommended_course`: "Programming Course" or "Sales Course"
- `recommendation_reasoning`: One-line explanation of the recommendation
- `recommendation_score`: Confidence score (0-100)

### Contact Information

- `contacts`: Array of contact objects, each containing:
  - `name`: Full name (if available)
  - `title`: Job title/position (if available)
  - `phone`: Phone number (if available)
  - `email`: Email address (if available)

Maximum 10 contacts are extracted per website.

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- Gemini API key

## Example Output

```
Analyzing website: nitdelhi.ac.in
==================================================
Starting analysis of: nitdelhi.ac.in

--- Step 1 ---
Analyzing: https://nitdelhi.ac.in
LLM Analysis: {'ready': True, 'recommended_course': 'Programming Course', ...}

LLM has enough data to make a recommendation!

Final Recommendation:
Course: Programming Course
Reasoning: The website clearly belongs to the National Institute of Technology Delhi...
Score: 98
```
