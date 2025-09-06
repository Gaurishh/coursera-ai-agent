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

# Course-specific contact extraction prompt templates
PROGRAMMING_CONTACT_EXTRACTION_PROMPT = """
Persona:
You are an expert data extraction specialist specializing in identifying key decision-makers and influencers for programming course sales.

Context:
Your goal is to analyze the provided text from an institution's website and extract contact information ONLY for personnel who would be relevant for selling programming courses. Focus on individuals who make decisions about technical training, curriculum development, or have influence over educational technology purchases.

Target Contacts for Programming Course Sales:
- CTO, Chief Technology Officer, Technical Directors
- IT Managers, IT Directors, Systems Administrators
- Engineering Department Heads, Engineering Managers
- Computer Science Department Heads, CS Faculty
- Technical Training Coordinators, Professional Development Managers
- Academic Deans with technical focus
- Research Directors in technical fields
- Technology Integration Specialists
- Software Development Managers
- Technical Curriculum Coordinators

Exclusion Criteria:
- General administrative staff (unless they handle training decisions)
- Non-technical department heads
- Support staff without decision-making authority
- Faculty in non-technical fields
- General contact information without specific names

Inclusion Criteria: A contact must only be included if it contains at least one phone number OR at least one email address AND appears to be relevant for programming course sales.

Website Content:
{website_content}

Your Task:
Respond ONLY with a valid JSON object containing an array of contact objects. Each contact object should have the following structure (include only the fields that are available):
{{
"contacts": [
{{
"name": "Full Name",
"title": "Job Title/Position",
"phone": "Phone Number",
"email": "Email Address"
}},
{{
"name": "Another Person",
"title": "Another Title",
"phone": "Another Phone"
}},
...
]
}}

Note: Only include the fields that are available in the source text. If a field is not available, simply omit it from the contact object.
If no relevant contacts for programming course sales are found, return: {{"contacts": []}}
"""

SALES_CONTACT_EXTRACTION_PROMPT = """
Persona:
You are an expert data extraction specialist specializing in identifying key decision-makers and influencers for sales course sales.

Context:
Your goal is to analyze the provided text from an institution's website and extract contact information ONLY for personnel who would be relevant for selling sales courses. Focus on individuals who make decisions about business training, sales development, or have influence over professional development purchases.

Target Contacts for Sales Course Sales:
- Sales Managers, Sales Directors, VP of Sales
- Business Development Managers, BD Directors
- Marketing Managers, Marketing Directors
- HR Directors, Training Managers, Professional Development Managers
- Business School Deans, Management Department Heads
- Executive Directors, General Managers
- Partnership Managers, Business Relations Managers
- Customer Success Managers
- Revenue Managers, Growth Managers
- Business Training Coordinators

Exclusion Criteria:
- Technical staff (unless they also handle business development)
- General administrative staff (unless they handle training decisions)
- Support staff without decision-making authority
- Faculty in non-business fields
- General contact information without specific names

Inclusion Criteria: A contact must only be included if it contains at least one phone number OR at least one email address AND appears to be relevant for sales course sales.

Website Content:
{website_content}

Your Task:
Respond ONLY with a valid JSON object containing an array of contact objects. Each contact object should have the following structure (include only the fields that are available):
{{
"contacts": [
{{
"name": "Full Name",
"title": "Job Title/Position",
"phone": "Phone Number",
"email": "Email Address"
}},
{{
"name": "Another Person",
"title": "Another Title",
"phone": "Another Phone"
}},
...
]
}}

Note: Only include the fields that are available in the source text. If a field is not available, simply omit it from the contact object.
If no relevant contacts for sales course sales are found, return: {{"contacts": []}}
"""

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
- URLs containing: "faculty", "staff", "team", "leadership", "director", "head", "dean"
- URLs containing: "computer-science", "engineering", "technology", "research", "development"
- URLs containing: "academic", "training", "professional-development"
- URLs containing: "contact", "about", "administration"
- Department pages (e.g., "computer-science-engineering", "electrical-engineering", "applied-sciences")
- Faculty directory pages and staff listing pages
- ANY URL with "computer-science" in the path (these contain faculty contacts)
- ANY URL with "engineering" in the path (these contain faculty contacts)

AVOID these types of URLs:
- Student-focused pages (admissions, applications, student life, student-*, how-to-apply)
- General information pages (policies, procedures, guidelines, IT-policy, how-to-reach)
- Partnership/collaboration pages (mou-collaboration, partnerships)
- Location/directions pages (how-to-reach, location, directions)
- News/events pages (unless about technical training)
- PDF files and documents
- Administrative pages without personnel information
- Course catalog or curriculum pages (unless they also contain faculty information)

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
    """Extract contact information from website using similar structure to get_course_recommendation"""
    print(f"Starting contact extraction for: {url}")
    
    # Normalize the input URL
    base_url = normalize_url(url)
    visited_urls = {base_url}
    visited_urls_list = [base_url]  # Track order of visited URLs
    extracted_contacts = {"contacts": []}
    
    # Start with the base URL
    urls_to_visit = [base_url]
    
    for step in range(1, 16):  # Max 15 steps
        print(f"\n--- Contact Extraction Step {step} ---")
        
        if not urls_to_visit:
            print("No more URLs to visit for contact extraction")
            break
        
        # Get next URL to visit
        current_url = urls_to_visit.pop(0)
        
        if current_url in visited_urls and step > 1:
            continue
            
        print(f"Extracting contacts from: {current_url}")
        
        # Mark as visited
        visited_urls.add(current_url)
        visited_urls_list.append(current_url)
        
        # Extract text content from current URL only (not accumulated)
        text_content = browse_website(current_url)
        if text_content:
            # Extract contacts from current URL content
            try:
                contacts = extract_contacts_from_text(text_content, recommended_course)
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print(f"API rate limit hit, waiting 5 seconds...")
                    import time
                    time.sleep(5)
                    contacts = extract_contacts_from_text(text_content, recommended_course)
                else:
                    print(f"Error extracting contacts: {e}")
                    contacts = []
            
            if contacts and len(contacts) > 0:
                # Add new contacts to extracted_contacts, avoiding duplicates
                for contact in contacts:
                    if len(extracted_contacts["contacts"]) < 10:  # Limit to 10 contacts max
                        # Check for duplicates based on name and email
                        is_duplicate = False
                        for existing_contact in extracted_contacts["contacts"]:
                            if (contact.get("name") == existing_contact.get("name") and 
                                contact.get("email") == existing_contact.get("email")):
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            extracted_contacts["contacts"].append(contact)
                            print(f"Added contact: {contact.get('name', 'Unknown')} - {contact.get('title', 'No title')}")
        

        # Find new URLs from current page (recursive traversal)
        all_new_urls = find_urls(current_url)
        print(f"Found {len(all_new_urls)} total URLs for contact extraction")
        
        # Filter out non-HTML files and invalid URLs before LLM processing
        filtered_urls = []
        for url in all_new_urls:
            # Skip PDFs, images, documents, and other non-HTML files
            if not any(ext in url.lower() for ext in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.xlsx', '.doc', '.docx', '.ppt', '.pptx']):
                filtered_urls.append(url)
        
        print(f"After filtering non-HTML files: {len(filtered_urls)} URLs")
        
        # Use LLM to filter URLs that are most relevant for contact information
        base_domain = urlparse(current_url).netloc
        good_urls = detect_good_urls_for_contact_info_extraction(filtered_urls, base_domain, recommended_course)
        
        # Add filtered URLs to visit (check both visited_urls and urls_to_visit for duplicates)
        for new_url in good_urls:
            if new_url not in visited_urls and new_url not in urls_to_visit:
                urls_to_visit.append(new_url)
        
        # Add small delay to avoid API rate limiting
        import time
        time.sleep(1)
        
        # Stop if we have enough contacts
        if len(extracted_contacts["contacts"]) >= 10:
            print("Reached maximum contact limit (10)")
            break
    
    print(f"Contact extraction completed. Found {len(extracted_contacts['contacts'])} contacts")
    
    # Print all visited URLs
    print(f"\nVisited URLs for contact extraction ({len(visited_urls_list)} total):")
    print("-" * 60)
    for i, visited_url in enumerate(visited_urls_list, 1):
        print(f"{i}. {visited_url}")
    
    return extracted_contacts

def extract_contacts_from_text(text_content, recommended_course):
    """Extract contacts from text content using course-specific LLM prompts"""
    # Choose the appropriate prompt based on recommended course
    if "Programming" in recommended_course:
        prompt = PROGRAMMING_CONTACT_EXTRACTION_PROMPT.format(website_content=text_content)
    else:  # Sales Course or any other type
        prompt = SALES_CONTACT_EXTRACTION_PROMPT.format(website_content=text_content)
    
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
            return analysis.get('contacts', [])
            
    except Exception as e:
        print(f"Error extracting contacts: {e}")
    
    return []

def run_agent(url):
    """Main agent function that gets course recommendation and contact info, then returns both"""
    course_recommendation = get_course_recommendation(url)
    contact_info = get_contact_info(url, course_recommendation.get("recommended_course", "Unknown"))
    
    return {
        "course_recommendation": course_recommendation,
        "contact_info": contact_info
    }

# Example usage
if __name__ == "__main__":
    # Example: Analyze a single website
    url = "nitdelhi.ac.in"  # You can change this to any website URL
    
    print(f"Analyzing website: {url}")
    print("="*50)
    
    result = run_agent(url)
    
    # Print course recommendation
    course_rec = result['course_recommendation']
    print(f"\nFinal Recommendation:")
    print(f"Course: {course_rec['recommended_course']}")
    print(f"Reasoning: {course_rec['recommendation_reasoning']}")
    print(f"Score: {course_rec['recommendation_score']}")
    
    # Print contact information
    contact_info = result['contact_info']
    print(f"\nExtracted Contacts ({len(contact_info['contacts'])} found):")
    print("-" * 50)
    
    if contact_info['contacts']:
        for i, contact in enumerate(contact_info['contacts'], 1):
            print(f"{i}. {contact.get('name', 'Unknown Name')}")
            if contact.get('title'):
                print(f"   Title: {contact['title']}")
            if contact.get('email'):
                print(f"   Email: {contact['email']}")
            if contact.get('phone'):
                print(f"   Phone: {contact['phone']}")
            print()
    else:
        print("No contacts found.")

