#!/usr/bin/env python3
"""
Coursera AI Agent - Website Analysis for Course Recommendations

This agent analyzes websites to determine whether to recommend
Programming or Sales courses based on the website's content and context.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
import os
import json
from typing import List, Dict, Tuple
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class WebsiteAnalysis:
    """Data class to store website analysis results"""
    url: str
    title: str
    content: str
    recommendation: str
    confidence: float
    reasoning: str
    gemini_response: str

class CourseraAgent:
    """AI Agent for analyzing websites and recommending courses using Gemini LLM"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # API Configuration
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
        self.google_places_api_key = os.environ.get("GOOGLE_PLACES_API_KEY", "YOUR_API_KEY_HERE")
        self.gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}"
        
        if self.gemini_api_key == "YOUR_API_KEY_HERE":
            logger.warning("GEMINI_API_KEY not set. Please set it as an environment variable or update the code.")
    
    def find_urls(self, url: str, max_urls: int = 50) -> List[str]:
        """
        Find all URLs on a given website
        
        Args:
            url: The base URL to analyze
            max_urls: Maximum number of URLs to return
            
        Returns:
            List of URLs found on the website
        """
        try:
            logger.info(f"Finding URLs on: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            urls = set()
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                
                # Only include URLs from the same domain
                if self._is_same_domain(url, full_url):
                    urls.add(full_url)
            
            # Convert to list and limit results
            url_list = list(urls)[:max_urls]
            logger.info(f"Found {len(url_list)} URLs on {url}")
            return url_list
            
        except Exception as e:
            logger.error(f"Error finding URLs on {url}: {str(e)}")
            return []
    
    def browse_website(self, url: str) -> Dict[str, str]:
        """
        Browse a website and extract textual content
        
        Args:
            url: The URL to browse
            
        Returns:
            Dictionary containing title and content
        """
        try:
            logger.info(f"Browsing website: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title found"
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text_content = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            logger.info(f"Successfully extracted content from {url}")
            return {
                'title': title_text,
                'content': text
            }
            
        except Exception as e:
            logger.error(f"Error browsing {url}: {str(e)}")
            return {
                'title': "Error loading page",
                'content': ""
            }
    
    def _is_same_domain(self, base_url: str, url: str) -> bool:
        """Check if two URLs are from the same domain"""
        try:
            base_domain = urlparse(base_url).netloc
            url_domain = urlparse(url).netloc
            return base_domain == url_domain
        except:
            return False
    
    def call_gemini_api(self, content: str, url: str, title: str) -> Dict:
        """
        Call Gemini API to analyze website content and get course recommendation
        
        Args:
            content: Website content to analyze
            url: Website URL
            title: Website title
            
        Returns:
            Dictionary containing Gemini's analysis
        """
        if self.gemini_api_key == "YOUR_API_KEY_HERE":
            return {
                "recommendation": "API Key not configured",
                "confidence": 0.0,
                "reasoning": "Please set GEMINI_API_KEY environment variable",
                "raw_response": "API Key not configured"
            }
        
        # Truncate content if too long (Gemini has token limits)
        max_content_length = 8000  # Conservative limit
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        prompt = f"""
You are an AI assistant that analyzes websites to determine whether to recommend Programming or Sales courses to visitors.

Website URL: {url}
Website Title: {title}
Website Content: {content}

Based on the website's content, title, and context, determine which type of course would be most relevant to recommend:

1. "Programming Course" - if the website is related to software development, coding, technology, programming languages, web development, mobile apps, data science, AI/ML, DevOps, etc.

2. "Sales Course" - if the website is related to sales, marketing, business development, customer acquisition, lead generation, advertising, e-commerce, retail, consulting, etc.

3. "Both courses could be relevant" - if the website has mixed content or could benefit from both types of courses.

Please respond with a JSON object in this exact format:
{{
    "recommendation": "Programming Course" | "Sales Course" | "Both courses could be relevant",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this recommendation was made",
    "key_indicators": ["list", "of", "key", "indicators", "found"]
}}

Be specific about what content elements led to your decision. Consider the website's purpose, target audience, and main themes.
"""

        try:
            headers = {
                'Content-Type': 'application/json',
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            response = requests.post(self.gemini_api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                content_text = result['candidates'][0]['content']['parts'][0]['text']
                
                # Try to parse JSON response
                try:
                    # Extract JSON from response (in case there's extra text)
                    json_start = content_text.find('{')
                    json_end = content_text.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        json_str = content_text[json_start:json_end]
                        parsed_response = json.loads(json_str)
                        parsed_response['raw_response'] = content_text
                        return parsed_response
                except json.JSONDecodeError:
                    pass
                
                # Fallback if JSON parsing fails
                return {
                    "recommendation": "Analysis completed",
                    "confidence": 0.7,
                    "reasoning": "Gemini analysis completed but response format was unexpected",
                    "raw_response": content_text
                }
            else:
                return {
                    "recommendation": "Error in analysis",
                    "confidence": 0.0,
                    "reasoning": "No valid response from Gemini API",
                    "raw_response": str(result)
                }
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            return {
                "recommendation": "Error in analysis",
                "confidence": 0.0,
                "reasoning": f"API call failed: {str(e)}",
                "raw_response": f"Error: {str(e)}"
            }
    
    def recommend_course(self, url: str, title: str, content: str) -> WebsiteAnalysis:
        """
        Analyze website and recommend a course type using Gemini LLM
        
        Args:
            url: The website URL
            title: Website title
            content: Website content
            
        Returns:
            WebsiteAnalysis object with recommendation
        """
        # Call Gemini API for analysis
        gemini_result = self.call_gemini_api(content, url, title)
        
        # Extract results from Gemini response
        recommendation = gemini_result.get("recommendation", "Error in analysis")
        confidence = gemini_result.get("confidence", 0.0)
        reasoning = gemini_result.get("reasoning", "No reasoning provided")
        raw_response = gemini_result.get("raw_response", "")
        
        # Add key indicators if available
        if "key_indicators" in gemini_result:
            indicators = gemini_result["key_indicators"]
            if isinstance(indicators, list) and indicators:
                reasoning += f" Key indicators: {', '.join(indicators[:5])}"  # Limit to first 5 indicators
        
        return WebsiteAnalysis(
            url=url,
            title=title,
            content=content[:500] + "..." if len(content) > 500 else content,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning,
            gemini_response=raw_response
        )
    
    def analyze_website(self, url: str) -> WebsiteAnalysis:
        """
        Complete analysis of a single website
        
        Args:
            url: The website URL to analyze
            
        Returns:
            WebsiteAnalysis object
        """
        logger.info(f"Starting analysis of: {url}")
        
        # Get website content
        website_data = self.browse_website(url)
        
        # Analyze and recommend
        analysis = self.recommend_course(
            url, 
            website_data['title'], 
            website_data['content']
        )
        
        return analysis
    
    def analyze_website_with_subpages(self, url: str, max_subpages: int = 5) -> WebsiteAnalysis:
        """
        Analyze a website including its subpages for better accuracy
        
        Args:
            url: The main website URL
            max_subpages: Maximum number of subpages to analyze
            
        Returns:
            WebsiteAnalysis object with combined analysis
        """
        logger.info(f"Starting comprehensive analysis of: {url}")
        
        # Get main page content
        main_data = self.browse_website(url)
        combined_content = main_data['content']
        combined_title = main_data['title']
        
        # Find and analyze subpages
        subpage_urls = self.find_urls(url, max_subpages)
        
        for subpage_url in subpage_urls[:max_subpages]:
            try:
                subpage_data = self.browse_website(subpage_url)
                combined_content += " " + subpage_data['content']
                time.sleep(1)  # Be respectful to the server
            except Exception as e:
                logger.warning(f"Could not analyze subpage {subpage_url}: {str(e)}")
        
        # Analyze combined content
        analysis = self.recommend_course(url, combined_title, combined_content)
        analysis.reasoning += f" (Analyzed main page + {min(len(subpage_urls), max_subpages)} subpages)"
        
        return analysis
    
    def process_urls(self, urls: List[str], use_subpages: bool = True) -> List[WebsiteAnalysis]:
        """
        Process multiple URLs and return analysis results
        
        Args:
            urls: List of URLs to analyze
            use_subpages: Whether to analyze subpages for better accuracy
            
        Returns:
            List of WebsiteAnalysis objects
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing URL {i}/{len(urls)}: {url}")
            
            try:
                if use_subpages:
                    analysis = self.analyze_website_with_subpages(url)
                else:
                    analysis = self.analyze_website(url)
                
                results.append(analysis)
                
                # Print immediate results
                print(f"\n{'='*60}")
                print(f"URL: {analysis.url}")
                print(f"Title: {analysis.title}")
                print(f"Recommendation: {analysis.recommendation}")
                print(f"Confidence: {analysis.confidence:.2f}")
                print(f"Reasoning: {analysis.reasoning}")
                print(f"{'='*60}\n")
                
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
                error_analysis = WebsiteAnalysis(
                    url=url,
                    title="Error",
                    content="",
                    recommendation="Error analyzing website",
                    confidence=0.0,
                    reasoning=f"Error: {str(e)}",
                    gemini_response=""
                )
                results.append(error_analysis)
            
            # Be respectful to servers
            time.sleep(2)
        
        return results

def main():
    """Main function to run the Coursera Agent"""
    print("🤖 Coursera AI Agent - Website Analysis for Course Recommendations")
    print("=" * 70)
    
    agent = CourseraAgent()
    
    # Example URLs for testing
    example_urls = [
        "https://github.com",
        "https://stackoverflow.com",
        "https://salesforce.com",
        "https://hubspot.com"
    ]
    
    while True:
        print("\nOptions:")
        print("1. Analyze a single website")
        print("2. Analyze multiple websites")
        print("3. Use example URLs")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            url = input("Enter the website URL: ").strip()
            if url:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                use_subpages = input("Analyze subpages for better accuracy? (y/n): ").lower() == 'y'
                
                if use_subpages:
                    analysis = agent.analyze_website_with_subpages(url)
                else:
                    analysis = agent.analyze_website(url)
                
                print(f"\n{'='*60}")
                print(f"ANALYSIS RESULTS")
                print(f"{'='*60}")
                print(f"URL: {analysis.url}")
                print(f"Title: {analysis.title}")
                print(f"Recommendation: {analysis.recommendation}")
                print(f"Confidence: {analysis.confidence:.2f}")
                print(f"Reasoning: {analysis.reasoning}")
                print(f"{'='*60}")
        
        elif choice == "2":
            urls_input = input("Enter URLs separated by commas: ").strip()
            urls = [url.strip() for url in urls_input.split(',') if url.strip()]
            
            if urls:
                # Add https:// if not present
                urls = [url if url.startswith(('http://', 'https://')) else 'https://' + url for url in urls]
                
                use_subpages = input("Analyze subpages for better accuracy? (y/n): ").lower() == 'y'
                
                results = agent.process_urls(urls, use_subpages)
                
                # Summary
                print(f"\n{'='*60}")
                print(f"SUMMARY OF ALL ANALYSES")
                print(f"{'='*60}")
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result.url} -> {result.recommendation} (Confidence: {result.confidence:.2f})")
                print(f"{'='*60}")
        
        elif choice == "3":
            use_subpages = input("Analyze subpages for better accuracy? (y/n): ").lower() == 'y'
            results = agent.process_urls(example_urls, use_subpages)
            
            # Summary
            print(f"\n{'='*60}")
            print(f"SUMMARY OF EXAMPLE ANALYSES")
            print(f"{'='*60}")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.url} -> {result.recommendation} (Confidence: {result.confidence:.2f})")
            print(f"{'='*60}")
        
        elif choice == "4":
            print("Goodbye! 👋")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
