import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os
import time
import random

# Try to load from .env file first, then environment variable
def load_api_key():
    # Check for .env file first
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    return line.split('=', 1)[1].strip()
    
    # Fallback to environment variable
    return os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")

# Environment variables
GEMINI_API_KEY = load_api_key()
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

# Perplexity API Configuration
def load_perplexity_api_key():
    # Check for .env file first
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('PERPLEXITY_API_KEY='):
                    return line.split('=', 1)[1].strip()
    
    # Fallback to environment variable
    return os.environ.get("PERPLEXITY_API_KEY", "YOUR_PERPLEXITY_API_KEY_HERE")

PERPLEXITY_API_KEY = load_perplexity_api_key()
PERPLEXITY_BASE_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_HEADERS = {
    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
    "Content-Type": "application/json"
}

# Debug: Print API key status (remove in production)
print(f"Perplexity API Key loaded: {'Yes' if PERPLEXITY_API_KEY != 'YOUR_PERPLEXITY_API_KEY_HERE' else 'No'}")
print(f"Perplexity API Key length: {len(PERPLEXITY_API_KEY)}")


# Master prompts for URL filtering based on course type
PROGRAMMING_MASTER_PROMPT_TEMPLATE = """
Persona:
You are an expert data analyst specializing in website structure and contact information discovery for technology companies. Your task is to identify the most informative URLs from a given list that will help a sales team find contact information, key personnel, and communication channels for programming course sales.

Primary Goal:
Select the most informative URLs from the list below that are most likely to contain contact information for programming course sales. Choose up to 5 URLs (or all available URLs if there are fewer than 5) that are most likely to contain:
- Technical leadership (CTO, technical directors, IT managers, engineering heads)
- Computer Science/Engineering department heads and faculty
- Technical training coordinators and professional development managers
- Research directors and technical project managers
- Technology integration specialists and curriculum developers
- Academic deans with technical focus
- Software development managers and technical leads

PRIORITY URLs (select these if available):
- URLs containing: "faculty", "staff", "team", "leadership"
- URLs containing: "computer-science", "technology"
- URLs containing: "professional-development"
- URLs containing: "contact", "administration"
- Programming-related department pages: "computer-science-engineering", "applied-sciences", "mathematics", "statistics"
- Faculty directory pages and staff listing pages
- ANY URL with "computer-science" in the path (these contain programming faculty contacts)
- URLs with "software", "programming", "computing", "informatics", "data-science", "artificial-intelligence"

AVOID these types of URLs:
- Student-focused pages (admissions, applications, student life, student-*, how-to-apply)
- General information pages (policies, procedures, guidelines, IT-policy, how-to-reach)
- Partnership/collaboration pages (mou-collaboration, partnerships)
- Location/directions pages (how-to-reach, location, directions)
- News/events pages (unless about technical training)
- PDF files and documents
- Administrative pages without personnel information
- Course catalog or curriculum pages (unless they also contain faculty information)
- Non-programming engineering departments: "civil-engineering", "electrical-engineering", "mechanical-engineering", "aerospace-engineering", "chemical-engineering"
- Physical sciences departments: "physics", "chemistry", "biology" (unless they have computing focus)
- Non-technical departments: "humanities", "social-sciences", "arts", "sports"

This information will be used for programming course sales outreach and lead generation. Use your own expert judgment to determine the most relevant URLs from the list.

List of URLs to Analyze:
{url_list_json}

Required Output Format:
Your response MUST be a valid JSON object and nothing else. The JSON object should contain a single key, 'selected_urls', with a list of the most relevant URLs you have chosen (up to 5, or all available if fewer than 5).
Example: {{"selected_urls": ["url_1", "url_2", "url_3"]}}
"""

SALES_MASTER_PROMPT_TEMPLATE = """
Persona:
You are an expert data analyst specializing in website structure and contact information discovery for business organizations. Your task is to identify the most informative URLs from a given list that will help a sales team find contact information, key personnel, and communication channels for sales course sales.

Primary Goal:
Select the most informative URLs from the list below that are most likely to contain contact information for sales course sales. Choose up to 5 URLs (or all available URLs if there are fewer than 5) that are most likely to contain:
- Business leadership (sales managers, business development directors, marketing managers)
- HR and training managers responsible for professional development
- Executive directors and general managers
- Business school deans and management department heads
- Partnership managers and business relations managers
- Customer success managers and revenue managers
- Business training coordinators and professional development staff

PRIORITY URLs (select these if available):
- URLs containing: "leadership", "management", "director", "manager", "head", "dean"
- URLs containing: "business", "sales", "marketing", "hr", "training", "development"
- URLs containing: "executive", "administration", "partnership", "relations"
- URLs containing: "contact", "about", "team", "staff"

AVOID these types of URLs:
- Student-focused pages (admissions, applications, student life)
- General information pages (policies, procedures, guidelines)
- Technical/engineering pages (unless they mention business development)
- Location/directions pages
- News/events pages (unless about business training)

This information will be used for sales course sales outreach and lead generation. Use your own expert judgment to determine the most relevant URLs from the list.

List of URLs to Analyze:
{url_list_json}

Required Output Format:
Your response MUST be a valid JSON object and nothing else. The JSON object should contain a single key, 'selected_urls', with a list of the most relevant URLs you have chosen (up to 5, or all available if fewer than 5).
Example: {{"selected_urls": ["url_1", "url_2", "url_3"]}}
"""

# Debug: Print API key status (remove in production)
# print(f"API Key loaded: {'Yes' if GEMINI_API_KEY != 'YOUR_API_KEY_HERE' else 'No'}")

def perplexity_deep_research(query: str, max_searches: int = 10) -> dict:
    """
    Perform a deep research query using Perplexity API.

    Args:
      query: The research question or topic.
      max_searches: Maximum number of web searches allowed.

    Returns:
      JSON response with:
        - 'answer': synthesized summary,
        - 'citations': list of source URLs,
        - 'breakdown': token usage and cost details.
    """
    if not PERPLEXITY_API_KEY:
        raise RuntimeError("PERPLEXITY_API_KEY environment variable not set")
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ],
        "max_tokens": 4000,
        "temperature": 0.2
    }
    
    try:
        print(f"\n🔍 Sending query to Perplexity API...")
        print(f"Query length: {len(query)} characters")
        
        resp = requests.post(PERPLEXITY_BASE_URL, json=payload, headers=PERPLEXITY_HEADERS, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        
        print(f"✅ Perplexity API response received")
        print(f"Response status: {resp.status_code}")
        
        # Extract the response content
        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            
            # Print the full response from Perplexity
            print(f"\n📋 PERPLEXITY RESPONSE:")
            print("="*80)
            print(content)
            print("="*80)
            
            return {
                "answer": content,
                "citations": [],  # Perplexity doesn't provide citations in this format
                "breakdown": result.get('usage', {})
            }
        else:
            print(f"❌ No choices found in Perplexity response")
            print(f"Full response: {result}")
            return {"answer": "", "citations": [], "breakdown": {}}
            
    except Exception as e:
        print(f"❌ Error in Perplexity API call: {e}")
        return {"answer": "", "citations": [], "breakdown": {}}
# print(f"API Key length: {len(GEMINI_API_KEY)}")

def normalize_url(url):
    """Normalize URL to handle different input formats"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def get_enhanced_headers():
    """Get enhanced headers that mimic a real browser"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"'
    }

def make_robust_request(url, max_retries=3):
    """Make a robust HTTP request with multiple fallback strategies"""
    session = requests.Session()
    
    for attempt in range(max_retries):
        try:
            # Get fresh headers for each attempt
            headers = get_enhanced_headers()
            
            # Add random delay
            time.sleep(random.uniform(1, 3))
            
            if attempt == 0:
                # First attempt: Standard request
                response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
            elif attempt == 1:
                # Second attempt: Add referer
                headers['Referer'] = 'https://www.google.com/'
                response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
            else:
                # Third attempt: Different approach with more realistic headers
                headers.update({
                    'Referer': 'https://www.google.com/',
                    'Origin': 'https://www.google.com',
                    'Sec-Fetch-Site': 'cross-site'
                })
                response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code == 200:
                print(f"✅ Successfully accessed {url} on attempt {attempt + 1}")
                return response
            elif response.status_code == 406:
                print(f"⚠️  Attempt {attempt + 1}: Got 406 error, trying different approach...")
                time.sleep(random.uniform(3, 7))  # Wait longer between attempts
                continue
            else:
                print(f"⚠️  Attempt {attempt + 1}: Got status {response.status_code}, retrying...")
                time.sleep(random.uniform(2, 5))
                continue
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(3, 7))
            continue
    
    print(f"❌ All attempts failed for {url}")
    return None

def find_urls(url):
    """Find all URLs present as hyperlinks in the website with anti-bot protection"""
    try:
        normalized_url = normalize_url(url)
        
        # Use the robust request function
        response = make_robust_request(normalized_url)
        
        if response is None:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        base_domain = urlparse(normalized_url).netloc
        
        urls = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(normalized_url, href)
            parsed_url = urlparse(full_url)
            
            # Only include URLs from the same domain
            if parsed_url.netloc == base_domain:
                urls.append(full_url)
        
        print(f"Found {len(set(urls))} unique URLs from {normalized_url}")
        return list(set(urls))  # Remove duplicates
    except Exception as e:
        print(f"Error finding URLs from {url}: {e}")
        return []

def browse_website(url):
    """Extract text content from a website with anti-bot protection bypass"""
    try:
        normalized_url = normalize_url(url)
        
        # Use the robust request function
        response = make_robust_request(normalized_url)
        
        if response is None:
            return ""
        
        # Parse HTML and extract text
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        print(f"Successfully extracted {len(text)} characters from {normalized_url}")
        return text
        
    except Exception as e:
        print(f"Error browsing {url}: {e}")
        return ""

def course_recommendation(text_content):
    """Analyze accumulated text content with Gemini LLM"""
    prompt = f"""
    You are an AI agent analyzing website content to recommend either a "Programming Course" or "Sales Course" to a course-selling company.
    
    Based on the following website content, determine if the website owner would benefit more from a Programming Course or a Sales Course.
    
    Website Content:
    {text_content}
    
    Analyze the content and return a JSON response with the following structure:
    - ready: boolean (true if you have enough information to make a recommendation, false if you need more data)
    - recommended_course: string ("Programming Course" or "Sales Course" or null if ready=false)
    - recommendation_reasoning: string (ONE LINE explanation of your recommendation or "Need more data" if ready=false)
    - recommendation_score: number (confidence score 0-100, or null if ready=false)
    
    Consider these factors:
    - Technical content, programming languages, software development, engineering, etc. → Programming Course
    - Business content, marketing, sales, customer acquisition → Sales Course
    - E-commerce, retail, service business → Sales Course
    
    Return only valid JSON, no additional text.
    """
    
    try:
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(GEMINI_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        # print(f"Gemini API Response: {result}")  # Debug output
        
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text'].strip()
            # print(f"Gemini Content: {content}")  # Debug output
            
            # Extract JSON from markdown code blocks if present
            if content.startswith('```json'):
                # Find the JSON content between ```json and ```
                start = content.find('```json') + 7
                end = content.rfind('```')
                if end > start:
                    content = content[start:end].strip()
            elif content.startswith('```'):
                # Handle case where it's just ``` without json
                start = content.find('```') + 3
                end = content.rfind('```')
                if end > start:
                    content = content[start:end].strip()
            
            return json.loads(content)
        else:
            print("No candidates in Gemini response")
            return {"ready": False, "recommended_course": None, "recommendation_reasoning": "No response from Gemini", "recommendation_score": None}
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
        return {"ready": False, "recommended_course": None, "recommendation_reasoning": "Invalid JSON response", "recommendation_score": None}
    except Exception as e:
        print(f"Error analyzing with LLM: {e}")
        return {"ready": False, "recommended_course": None, "recommendation_reasoning": "Error in analysis", "recommendation_score": None}

def detect_good_urls_for_course_recommendation(urls, base_domain):
    """Use LLM to filter URLs that are most likely to contain relevant information for course recommendations"""
    if not urls:
        return []
    
    # Create a list of URL paths for analysis
    url_paths = []
    for url in urls:
        try:
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            if path:  # Only include URLs with actual paths
                url_paths.append(path)
        except:
            continue
    
    if not url_paths:
        return urls[:3]  # Return first 3 if no paths to analyze
    
    prompt = f"""
    You are analyzing website URLs to determine which ones are most likely to contain information relevant for recommending either a "Programming Course" or "Sales Course".
    
    Base domain: {base_domain}
    URL paths to analyze: {url_paths[:20]}  # Limit to first 20 for analysis
    
    For each URL path, determine if it's likely to contain information about:
    - Technical content, programming, engineering, academics, courses, departments
    - Business content, marketing, sales, services, about the company
    
    URLs that are LIKELY to be relevant:
    - /about, /about-us, /company, /services, /products
    - /departments, /academics, /courses, /programs, /research
    - /computer-science, /engineering, /technology, /science
    - /business, /marketing, /sales, /commerce
    - /faculty, /staff, /team, /leadership
    - /news, /blog, /articles, /updates
    
    URLs that are UNLIKELY to be relevant:
    - /sports, /athletics, /recreation, /entertainment
    - /events, /calendar, /gallery, /photos
    - /contact, /location, /directions, /map
    - /login, /register, /account, /profile
    - /privacy, /terms, /legal, /disclaimer
    - /sitemap, /search, /help, /faq
    - /admissions, /application, /forms (unless clearly academic)
    
    Return a JSON response with:
    - relevant_urls: array of URL paths that are likely to contain relevant information (max 8)
    - reasoning: brief explanation of your selection criteria
    
    Return only valid JSON, no additional text.
    """
    
    try:
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(GEMINI_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # Extract JSON from markdown code blocks if present
            if content.startswith('```json'):
                start = content.find('```json') + 7
                end = content.rfind('```')
                if end > start:
                    content = content[start:end].strip()
            elif content.startswith('```'):
                start = content.find('```') + 3
                end = content.rfind('```')
                if end > start:
                    content = content[start:end].strip()
            
            analysis = json.loads(content)
            relevant_paths = analysis.get('relevant_urls', [])
            
            # Convert paths back to full URLs
            good_urls = []
            for url in urls:
                try:
                    parsed = urlparse(url)
                    path = parsed.path.strip('/')
                    if path in relevant_paths:
                        good_urls.append(url)
                except:
                    continue
            
            print(f"LLM selected {len(good_urls)} relevant URLs from {len(urls)} total URLs")
            return good_urls[:8]  # Limit to 8 URLs max
            
    except Exception as e:
        print(f"Error in URL filtering: {e}")
    
    # Fallback: return first 5 URLs if LLM fails
    return urls[:5]

def detect_good_urls_for_contact_info_extraction(urls, base_domain, recommended_course):
    """Use LLM to filter URLs that are most likely to contain contact information"""
    if not urls:
        return []
    
    # Limit to first 20 URLs for analysis
    urls_to_analyze = urls[:20]
    
    # Create JSON list of URLs for the prompt
    url_list_json = json.dumps(urls_to_analyze)
    
    # Choose the appropriate master prompt based on recommended course
    if "Programming" in recommended_course:
        prompt = PROGRAMMING_MASTER_PROMPT_TEMPLATE.format(url_list_json=url_list_json)
    else:  # Sales Course or any other type
        prompt = SALES_MASTER_PROMPT_TEMPLATE.format(url_list_json=url_list_json)
    
    try:
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(GEMINI_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # Extract JSON from markdown code blocks if present
            if content.startswith('```json'):
                start = content.find('```json') + 7
                end = content.rfind('```')
                if end > start:
                    content = content[start:end].strip()
            elif content.startswith('```'):
                start = content.find('```') + 3
                end = content.rfind('```')
                if end > start:
                    content = content[start:end].strip()
            
            analysis = json.loads(content)
            selected_urls = analysis.get('selected_urls', [])
            
            print(f"LLM selected {len(selected_urls)} contact-relevant URLs from {len(urls)} total URLs")
            return selected_urls[:8]  # Limit to 8 URLs max
            
    except Exception as e:
        print(f"Error in contact URL filtering: {e}")
    
    # Fallback: return first 5 URLs if LLM fails
    return urls[:5]

def force_recommendation(text_content):
    """Force a recommendation even with limited data"""
    prompt = f"""
    You are an AI agent that MUST make a recommendation between "Programming Course" or "Sales Course" based on the limited website content provided.
    
    Website Content:
    {text_content}
    
    Even with limited data, analyze what you can and make a recommendation. Consider:
    - Any technical terms, programming languages, engineering content → Programming Course
    - Any business, marketing, sales, e-commerce content → Sales Course
    - Educational institutions → Programming Course (likely for students)
    - Company websites → Sales Course (likely for business growth)
    - If unclear, default to Programming Course
    
    Return a JSON response with:
    - ready: true
    - recommended_course: "Programming Course" or "Sales Course"
    - recommendation_reasoning: ONE LINE explanation based on available data
    - recommendation_score: low score (20-50) due to limited data
    
    Return only valid JSON, no additional text.
    """
    
    try:
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(GEMINI_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # Extract JSON from markdown code blocks if present
            if content.startswith('```json'):
                start = content.find('```json') + 7
                end = content.rfind('```')
                if end > start:
                    content = content[start:end].strip()
            elif content.startswith('```'):
                start = content.find('```') + 3
                end = content.rfind('```')
                if end > start:
                    content = content[start:end].strip()
            
            return json.loads(content)
        else:
            # Fallback recommendation if API fails
            return {
                "ready": True,
                "recommended_course": "Programming Course",
                "recommendation_reasoning": "Default recommendation due to limited data and API error",
                "recommendation_score": 25
            }
    except Exception as e:
        print(f"Error in forced recommendation: {e}")
        # Fallback recommendation
        return {
            "ready": True,
            "recommended_course": "Programming Course",
            "recommendation_reasoning": "Default recommendation due to limited data and technical error",
            "recommendation_score": 20
        }

def get_course_recommendation(url):
    """Main function that runs the analysis loop and returns course recommendation"""
    print(f"Starting analysis of: {url}")
    
    # Normalize the input URL
    base_url = normalize_url(url)
    visited_urls = {base_url}
    accumulated_text = ""
    
    # Start with the base URL
    urls_to_visit = [base_url]
    
    for step in range(1, 16):  # Max 15 steps
        print(f"\n--- Step {step} ---")
        
        if not urls_to_visit:
            print("No more URLs to visit")
            break
        
        # Get next URL to visit
        current_url = urls_to_visit.pop(0)
        
        if current_url in visited_urls and step > 1:
            continue
            
        print(f"Analyzing: {current_url}")
        
        # Extract text content
        text_content = browse_website(current_url)
        if text_content:
            accumulated_text += f"\n\n--- Content from {current_url} ---\n{text_content}"
        
        # Find new URLs (only from the first URL to avoid going too deep)
        all_new_urls = find_urls(current_url)
        print(f"Found {len(all_new_urls)} total URLs from {current_url}")
        
        # Use LLM to filter URLs that are most relevant for course recommendations
        base_domain = urlparse(current_url).netloc
        good_urls = detect_good_urls_for_course_recommendation(all_new_urls, base_domain)
        
        # Add filtered URLs to visit
        for new_url in good_urls:
            if new_url not in visited_urls:
                urls_to_visit.append(new_url)
                visited_urls.add(new_url)
        
        # Analyze with LLM
        analysis = course_recommendation(accumulated_text)
        
        print(f"LLM Analysis: {analysis}")
        
        if analysis.get("ready", False):
            print("LLM has enough data to make a recommendation!")
            break
    
    # Final analysis if not ready yet
    if not analysis.get("ready", False):
        print("Running final analysis with all collected data...")
        analysis = course_recommendation(accumulated_text)
    
    # If still not ready after final analysis, force a recommendation with low confidence
    if not analysis.get("ready", False):
        print("Forcing recommendation based on limited data available...")
        forced_analysis = force_recommendation(accumulated_text)
        result = {
            "recommended_course": forced_analysis.get("recommended_course", "Unable to determine"),
            "recommendation_reasoning": forced_analysis.get("recommendation_reasoning", "Limited data available"),
            "recommendation_score": forced_analysis.get("recommendation_score", 30)
        }
    else:
        result = {
            "recommended_course": analysis.get("recommended_course", "Unable to determine"),
            "recommendation_reasoning": analysis.get("recommendation_reasoning", "Insufficient data"),
            "recommendation_score": analysis.get("recommendation_score", 0)
        }

    return result

def get_contact_info(url, recommended_course):
    """
    Extract contact information from a website using Perplexity API
    """
    print(f"Starting contact extraction for: {url}")
    
    # Normalize the input URL
    base_url = normalize_url(url)
    
    # Create course-specific query for Perplexity
    if "Programming" in recommended_course:
        query = f"""Act as a lead generation specialist. Your task is to thoroughly analyze the website provided below and extract contact information for key individuals who are potential buyers or key influencers for a programming course.

Website to Analyze:
{base_url}

---

**Scenario A: If the website is an Educational Institution (e.g., an engineering college)**

**Target Roles:**
* Head of Department (HOD) for Computer Science (CS), Information Technology (IT), or other software-related branches.
* Training and Placement Officer (TPO) or Head of Career Services.
* Dean of Academics or Dean of Student Affairs.
* Faculty coordinators for technical student clubs (e.g., Coding Club, AI/ML Club).
* Contact Pages

**Search Locations on Website:** Look for pages titled "Departments," "Faculty," "Placement Cell," "Contact Us," "Administration," or "Student Clubs."

---

**Scenario B: If the website is a Tech Company**

**Target Roles:**
* Head of Learning & Development (L&D).
* HR Manager or Director (specifically those involved in employee training and upskilling).
* Chief Technology Officer (CTO) or VP of Engineering.
* Head of University Relations or Campus Recruitment.
* Contact Pages

**Search Locations on Website:** Look for pages titled "About Us," "Leadership," "Careers," "HR," "L&D," or "University Programs."

---

**Required Information for each Contact:**
For each relevant contact found, please extract as many of the following details as possible. If a field is not found, please write "Not Found".
* Email
* Phone
* Name
* Job Title

**Output Format:**
Present the findings as a simple text list. Separate each contact with a line of dashes (---). Do not use a table.

Example:

Email: jane.doe@example.edu
Phone: Not Found
Name: Jane Doe
Job Title: Head of Department, Computer Science
---
Email: j.smith@example.edu
Phone: +1-123-456-7890
Name: John Smith
Job Title: Training & Placement Officer"""
    else:  # Sales Course
        query = f"""Act as a lead generation specialist. Your task is to thoroughly analyze the website provided below and extract contact information for key individuals who are potential buyers or key influencers for a sales training course.

Website to Analyze:
{base_url}

---

**Scenario A: If the website is an Educational Institution (e.g., a business school)**

**Target Roles:**
* Head of Department (HOD) for Marketing, Sales, or Business Management.
* Dean of the Business School or Director of MBA Programs.
* Training and Placement Officer (TPO) or Head of Career Services.
* Faculty coordinators or professors specializing in sales and marketing.
* Director of Executive Education programs.
* Contact Pages

**Search Locations on Website:** Look for pages titled "Departments," "Faculty," "Placement Cell," "Executive Education," "Contact Us," or "Administration."

---

**Scenario B: If the website is a Sales and Marketing Company**

**Target Roles:**
* VP of Sales / Head of Sales / Chief Revenue Officer (CRO).
* Sales Training Manager or Head of Sales Enablement.
* Head of Learning & Development (L&D).
* HR Manager responsible for sales team training.
* Regional or National Sales Directors.
* Contact Pages

**Search Locations on Website:** Look for pages titled "About Us," "Leadership," "Our Team," "Sales," "Careers," or "Contact Us."

---

**Required Information for each Contact:**
For each relevant contact found, please extract as many of the following details as possible. If a field is not found, please write "Not Found".
* Email
* Phone
* Name
* Job Title

**Output Format:**
Present the findings as a simple text list. Separate each contact with a line of dashes (---). Do not use a table.

Example:

Email: jane.doe@example.com
Phone: Not Found
Name: Jane Doe
Job Title: VP of Sales
---
Email: j.smith@example.edu
Phone: +1-123-456-7890
Name: John Smith
Job Title: Head of Career Services"""
    
    print(f"Querying Perplexity for contact information...")
    print(f"Course type: {recommended_course}")
    print(f"Target website: {base_url}")
    
    try:
        # Use Perplexity to find contact information
        result = perplexity_deep_research(query, max_searches=15)
        
        # Extract contacts from the answer using LLM
        contacts = extract_contacts_from_perplexity_result(result, recommended_course)
        
        print(f"Contact extraction completed. Found {len(contacts)} contacts")
        
        # Print extracted contacts for debugging
        if contacts:
            print(f"\n📞 EXTRACTED CONTACTS:")
            print("-" * 60)
            for i, contact in enumerate(contacts, 1):
                print(f"{i}. {contact.get('name', 'Unknown Name')}")
                if contact.get('title'):
                    print(f"   Title: {contact['title']}")
                if contact.get('email'):
                    print(f"   Email: {contact['email']}")
                if contact.get('phone'):
                    print(f"   Phone: {contact['phone']}")
                print()
        else:
            print("No contacts extracted from Perplexity response")
        
        # Print citations for transparency
        if result.get('citations'):
            print(f"\nSources consulted ({len(result['citations'])} total):")
            print("-" * 60)
            for i, cite in enumerate(result['citations'][:15], 1):  # Show first 15 sources
                title = cite.get('title', 'No title')
                url = cite.get('url', 'No URL')
                print(f"{i}. {title}")
                print(f"   {url}")
            if len(result['citations']) > 5:
                print(f"   ... and {len(result['citations']) - 5} more sources")
        
        return {"contacts": contacts}
        
    except Exception as e:
        print(f"Error in contact extraction: {e}")
        return {"contacts": []}

def extract_contacts_from_perplexity_result(perplexity_result, recommended_course):
    """Extract all contacts from Perplexity API result using LLM"""
    answer = perplexity_result.get('answer', '')
    if not answer:
        return []
    
    # Create a prompt to extract ALL contact information from the Perplexity answer
    prompt = f"""
    Extract ALL contact information from the following text.. 
    Include any person mentioned with their name, title, email address, or phone number.

    Text: {answer}

    Return ONLY a valid JSON object with this structure:
    {{
        "contacts": [
            {{
                "name": "Full Name",
                "title": "Job Title/Position", 
                "email": "Email Address",
                "phone": "Phone Number"
            }}
        ]
    }}

    Include ALL contacts found in the text, regardless of their role or department.
    Only include contacts that have at least an email address or phone number.
    If no contacts are found, return: {{"contacts": []}}
    """
    
    try:
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(GEMINI_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # Extract JSON from markdown code blocks if present
            if content.startswith('```json'):
                start = content.find('```json') + 7
                end = content.rfind('```')
                if end > start:
                    content = content[start:end].strip()
            elif content.startswith('```'):
                start = content.find('```') + 3
                end = content.rfind('```')
                if end > start:
                    content = content[start:end].strip()
            
            analysis = json.loads(content)
            contacts = analysis.get('contacts', [])
            
            # Print found contacts
            for contact in contacts:
                print(f"Added contact: {contact.get('name', 'Unknown')} - {contact.get('title', 'No title')}")
            
            return contacts
            
    except Exception as e:
        print(f"Error extracting contacts from Perplexity result: {e}")
    
    return []


def run_agent(url):
    """Main agent function that gets course recommendation and contact info, then returns both"""
    course_recommendation = get_course_recommendation(url)
    contact_info = get_contact_info(url, course_recommendation.get("recommended_course", "Unknown"))
    
    return {
        "course_recommendation": course_recommendation,
        "contact_info": contact_info
    }

def process_all_websites(csv_file_path, max_websites=None):
    """Process all websites from CSV file and save results to individual JSON files"""
    import pandas as pd
    import json
    import os
    from urllib.parse import urlparse
    
    # Start timing for batch processing
    batch_start_time = time.time()
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_file_path)
        print(f"Loaded {len(df)} websites from {csv_file_path}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Limit websites if specified
    if max_websites:
        df = df.head(max_websites)
        print(f"Processing first {len(df)} websites")
    
    # Process each website
    successful = 0
    failed = 0
    
    for index, row in df.iterrows():
        institution_name = row['Institution Name']
        website_url = row['Website']
        
        # Extract domain name for filename
        try:
            parsed_url = urlparse(website_url)
            domain = parsed_url.netloc or parsed_url.path
            domain = domain.replace('www.', '').replace('https://', '').replace('http://', '')
            if domain.endswith('/'):
                domain = domain[:-1]
        except:
            domain = f"website_{index}"
        
        print(f"\n{'='*60}")
        print(f"Processing {index + 1}/{len(df)}: {institution_name}")
        print(f"Website: {website_url}")
        print(f"Domain: {domain}")
        print(f"{'='*60}")
        
        try:
            # Run the agent
            result = run_agent(website_url)
            
            # Add metadata
            result['metadata'] = {
                'institution_name': institution_name,
                'website_url': website_url,
                'location': row.get('Location', 'N/A'),
                'phone': row.get('Phone', 'N/A'),
                'institution_type': row.get('Institution Type', 'N/A'),
                'processed_at': pd.Timestamp.now().isoformat()
            }
            
            # Save to JSON file
            output_file = f"outputs/{domain}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Successfully processed and saved to {output_file}")
            successful += 1
            
            # Print summary
            print(f"Course: {result['course_recommendation']['recommended_course']}")
            print(f"Score: {result['course_recommendation']['recommendation_score']}")
            print(f"Contacts: {len(result['contact_info']['contacts'])} found")
            
        except Exception as e:
            print(f"❌ Error processing {institution_name}: {e}")
            failed += 1
            
            # Save error info
            error_result = {
                'error': str(e),
                'metadata': {
                    'institution_name': institution_name,
                    'website_url': website_url,
                    'location': row.get('Location', 'N/A'),
                    'phone': row.get('Phone', 'N/A'),
                    'institution_type': row.get('Institution Type', 'N/A'),
                    'processed_at': pd.Timestamp.now().isoformat(),
                    'status': 'failed'
                }
            }
            
            output_file = f"outputs/{domain}_ERROR.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(error_result, f, indent=2, ensure_ascii=False)
    
    # Calculate and print batch processing time
    batch_end_time = time.time()
    batch_execution_time = batch_end_time - batch_start_time
    
    print(f"\n{'='*60}")
    print(f"BATCH PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total websites processed: {len(df)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(successful/len(df)*100):.1f}%")
    print(f"Results saved in 'outputs/' directory")
    print(f"\nBATCH EXECUTION TIME: {batch_execution_time:.2f} seconds ({batch_execution_time/60:.2f} minutes)")
    print(f"Average time per website: {batch_execution_time/len(df):.2f} seconds")
    print("="*60)

# Example usage
if __name__ == "__main__":
    # Process all websites from CSV file
    csv_file = "1_discovered_leads.csv"
    
    print("🚀 Starting batch processing of all websites...")
    print(f"CSV file: {csv_file}")
    print("="*60)
    
    # Process all websites (remove max_websites limit to process all)
    process_all_websites(csv_file)
