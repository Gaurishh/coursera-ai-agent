import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os

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

# Debug: Print API key status (remove in production)
# print(f"API Key loaded: {'Yes' if GEMINI_API_KEY != 'YOUR_API_KEY_HERE' else 'No'}")
# print(f"API Key length: {len(GEMINI_API_KEY)}")

def normalize_url(url):
    """Normalize URL to handle different input formats"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def find_urls(url):
    """Find all URLs present as hyperlinks in the website"""
    try:
        normalized_url = normalize_url(url)
        response = requests.get(normalized_url, timeout=10)
        response.raise_for_status()
        
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
        
        return list(set(urls))  # Remove duplicates
    except Exception as e:
        print(f"Error finding URLs from {url}: {e}")
        return []

def browse_website(url):
    """Extract text content from a website"""
    try:
        normalized_url = normalize_url(url)
        response = requests.get(normalized_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        print(f"Error browsing website {url}: {e}")
        return ""

def analyze_with_llm(text_content):
    """Analyze accumulated text content with Gemini LLM"""
    prompt = f"""
    You are an AI agent analyzing website content to recommend either a "Programming Course" or "Sales Course" to a course-selling company.
    
    Based on the following website content, determine if the website owner would benefit more from a Programming Course or a Sales Course.
    
    Website Content:
    {text_content}
    
    Analyze the content and return a JSON response with the following structure:
    - ready: boolean (true if you have enough information to make a recommendation, false if you need more data)
    - recommended_course: string ("Programming Course" or "Sales Course" or null if ready=false)
    - recommendation_reasoning: string (explanation of your recommendation or "Need more data" if ready=false)
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
    - recommendation_reasoning: explanation based on available data
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

def run_agent(url):
    """Main agent function that runs the analysis loop"""
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
        if step == 1:
            new_urls = find_urls(current_url)
            # Add new URLs to visit (limit to avoid too many)
            for new_url in new_urls[:5]:  # Limit to first 5 new URLs
                if new_url not in visited_urls:
                    urls_to_visit.append(new_url)
                    visited_urls.add(new_url)
        
        # Analyze with LLM
        analysis = analyze_with_llm(accumulated_text)
        
        print(f"LLM Analysis: {analysis}")
        
        if analysis.get("ready", False):
            print("LLM has enough data to make a recommendation!")
            break
    
    # Final analysis if not ready yet
    if not analysis.get("ready", False):
        print("Running final analysis with all collected data...")
        analysis = analyze_with_llm(accumulated_text)
    
    # If still not ready after final analysis, force a recommendation with low confidence
    if not analysis.get("ready", False):
        print("Forcing recommendation based on limited data available...")
        forced_analysis = force_recommendation(accumulated_text)
        return {
            "recommended_course": forced_analysis.get("recommended_course", "Unable to determine"),
            "recommendation_reasoning": forced_analysis.get("recommendation_reasoning", "Limited data available"),
            "recommendation_score": forced_analysis.get("recommendation_score", 30)
        }
    
    return {
        "recommended_course": analysis.get("recommended_course", "Unable to determine"),
        "recommendation_reasoning": analysis.get("recommendation_reasoning", "Insufficient data"),
        "recommendation_score": analysis.get("recommendation_score", 0)
    }

# Example usage
if __name__ == "__main__":
    # Example: Analyze a single website
    url = "nitdelhi.ac.in"  # You can change this to any website URL
    
    print(f"Analyzing website: {url}")
    print("="*50)
    
    result = run_agent(url)
    
    print(f"\nFinal Recommendation:")
    print(f"Course: {result['recommended_course']}")
    print(f"Reasoning: {result['recommendation_reasoning']}")
    print(f"Score: {result['recommendation_score']}")

