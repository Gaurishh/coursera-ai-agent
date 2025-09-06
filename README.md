# Coursera AI Agent

An AI agent that analyzes websites to recommend either a "Programming Course" or "Sales Course" based on the website content.

## Features

- **Website Analysis**: Crawls websites and extracts text content
- **URL Discovery**: Finds all internal links on a website
- **AI-Powered Recommendations**: Uses Gemini AI to analyze content and make course recommendations
- **Smart Crawling**: Visits multiple pages (up to 15 steps) to gather comprehensive data
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
from coursera_agent import run_agent

# Analyze a website
result = run_agent("example.com")

print(f"Recommended Course: {result['recommended_course']}")
print(f"Reasoning: {result['recommendation_reasoning']}")
print(f"Confidence Score: {result['recommendation_score']}")
```

### Command Line Usage

```bash
python coursera_agent.py
```

## How It Works

1. **URL Normalization**: Handles URLs in any format (with/without www, http/https)
2. **Content Extraction**: Extracts clean text from web pages
3. **Link Discovery**: Finds all internal links on the website
4. **Iterative Analysis**: Visits multiple pages to gather comprehensive data
5. **AI Analysis**: Uses Gemini AI to analyze content and determine course recommendation
6. **Smart Termination**: Stops early when confident recommendation is made
7. **Forced Recommendation**: If insufficient data after 15 steps, forces a recommendation with lower confidence (20-50 score)

## API Response Format

The agent returns a dictionary with:

- `recommended_course`: "Programming Course" or "Sales Course"
- `recommendation_reasoning`: Detailed explanation of the recommendation
- `recommendation_score`: Confidence score (0-100)

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
