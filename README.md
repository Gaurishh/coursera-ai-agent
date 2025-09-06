# Coursera AI Agent - Website Analysis for Course Recommendations

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()
[![AI](https://img.shields.io/badge/AI-Gemini%20LLM-purple.svg)](https://ai.google.dev/)

An intelligent AI agent powered by **Google Gemini LLM** that analyzes websites to determine whether to recommend **Programming** or **Sales** courses based on the website's content, context, and purpose.

## 🚀 Features

- **AI-Powered Analysis**: Uses Google Gemini LLM for intelligent content analysis
- **Contextual Understanding**: Goes beyond keyword matching to understand website purpose and audience
- **URL Discovery**: Automatically finds and analyzes subpages for comprehensive insights
- **Confidence Scoring**: Provides confidence levels for each recommendation
- **Batch Processing**: Analyze multiple websites at once
- **Detailed Reasoning**: AI explains why a particular course is recommended
- **Respectful Crawling**: Includes delays and proper headers to be respectful to servers

## 📋 Requirements

- Python 3.7 or higher
- Internet connection for website analysis
- Google Gemini API key (get one at [Google AI Studio](https://aistudio.google.com/))

## 🛠️ Installation

1. **Clone or download this repository**

   ```bash
   git clone <repository-url>
   cd coursera-ai-agent
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Gemini API key**

   ```bash
   # Option 1: Set environment variable
   export GEMINI_API_KEY="your_api_key_here"

   # Option 2: Set in your shell profile (.bashrc, .zshrc, etc.)
   echo 'export GEMINI_API_KEY="your_api_key_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

4. **Run the agent**
   ```bash
   python coursera_agent.py
   ```

## 🎯 Usage

### Interactive Mode

Run the script and follow the interactive prompts:

```bash
python coursera_agent.py
```

You'll see options to:

1. Analyze a single website
2. Analyze multiple websites
3. Use example URLs (GitHub, Stack Overflow, Salesforce, HubSpot)
4. Exit

### Programmatic Usage

```python
from coursera_agent import CourseraAgent

# Initialize the agent
agent = CourseraAgent()

# Analyze a single website
analysis = agent.analyze_website("https://github.com")
print(f"Recommendation: {analysis.recommendation}")
print(f"Confidence: {analysis.confidence}")

# Analyze with subpages for better accuracy
analysis = agent.analyze_website_with_subpages("https://example.com")

# Process multiple URLs
urls = ["https://github.com", "https://salesforce.com"]
results = agent.process_urls(urls)
```

## 📊 How It Works

### AI-Powered Analysis

The agent uses **Google Gemini LLM** for intelligent content analysis:

**Contextual Understanding**:

- Analyzes website purpose, target audience, and main themes
- Considers content context beyond simple keyword matching
- Understands business models, industry focus, and user intent
- Provides nuanced recommendations based on overall website analysis

**Programming Course Indicators**:

- Software development, coding, technology companies
- Programming languages, frameworks, development tools
- Tech startups, developer communities, open source projects
- Data science, AI/ML, DevOps, cloud computing

**Sales Course Indicators**:

- Sales, marketing, business development companies
- E-commerce, retail, customer acquisition
- Lead generation, advertising, brand management
- Consulting, business services, relationship management

### Analysis Process

1. **Content Extraction**: Scrapes website content and extracts text
2. **AI Analysis**: Sends content to Gemini LLM for intelligent analysis
3. **Contextual Understanding**: AI considers website purpose, audience, and themes
4. **Recommendation**: AI suggests the most relevant course type
5. **Detailed Reasoning**: AI provides explanation with key indicators

### Example Output

```
============================================================
URL: https://github.com
Title: GitHub: Let's build from here
Recommendation: Programming Course
Confidence: 0.92
Reasoning: This is a software development platform focused on code hosting, version control, and collaboration tools. The website clearly targets developers, programmers, and software engineers. Key indicators: code repositories, programming languages, development tools, open source projects
============================================================
```

## 🔧 Configuration

### API Key Setup

Set your Gemini API key as an environment variable:

```bash
# Linux/Mac
export GEMINI_API_KEY="your_api_key_here"

# Windows
set GEMINI_API_KEY=your_api_key_here
```

Or modify the code directly in `coursera_agent.py`:

```python
self.gemini_api_key = "your_api_key_here"
```

### Analysis Settings

- **Max URLs per site**: Control how many subpages to analyze (default: 50)
- **Max subpages**: Limit subpage analysis (default: 5)
- **Content length limit**: Truncate content for API calls (default: 8000 chars)
- **Request delays**: Built-in delays to be respectful to servers
- **API timeout**: Gemini API request timeout (default: 30 seconds)

## 📈 API Reference

### CourseraAgent Class

#### Methods

- `find_urls(url, max_urls=50)`: Find all URLs on a website
- `browse_website(url)`: Extract content from a website
- `call_gemini_api(content, url, title)`: Call Gemini LLM for analysis
- `analyze_website(url)`: Complete analysis of a single website
- `analyze_website_with_subpages(url, max_subpages=5)`: Analyze website + subpages
- `process_urls(urls, use_subpages=True)`: Process multiple URLs

#### WebsiteAnalysis Dataclass

- `url`: Website URL
- `title`: Page title
- `content`: Extracted content (truncated)
- `recommendation`: Course recommendation ("Programming Course", "Sales Course", etc.)
- `confidence`: Confidence score (0.0 to 1.0)
- `reasoning`: Detailed explanation of the recommendation
- `gemini_response`: Raw response from Gemini LLM

## 🧪 Testing

Test the agent with various websites:

```python
# Test programming-focused sites
agent.analyze_website("https://stackoverflow.com")
agent.analyze_website("https://github.com")

# Test sales-focused sites
agent.analyze_website("https://salesforce.com")
agent.analyze_website("https://hubspot.com")

# Test mixed content
agent.analyze_website("https://medium.com")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**"Connection Error"**

- Check your internet connection
- Some websites may block automated requests
- Try with different websites

**"No keywords found"**

- The website might not contain relevant content
- Try analyzing subpages for better results
- Check if the website is accessible

**"SSL Certificate Error"**

- Some websites have SSL issues
- The agent will skip problematic URLs and continue

### Getting Help

If you encounter issues:

1. Check the logs for detailed error messages
2. Try with different websites
3. Ensure all dependencies are installed
4. Open an issue with details about the problem

## 🎯 Use Cases

- **Course Recommendation Systems**: Automatically suggest relevant courses
- **Lead Qualification**: Identify potential customers for programming vs sales courses
- **Market Research**: Analyze competitor websites
- **Content Strategy**: Understand what type of content resonates with different audiences
- **Educational Technology**: Build intelligent tutoring systems

## 🔮 Future Enhancements

- [ ] Machine learning model for more accurate predictions
- [ ] Support for more course categories
- [ ] Integration with course databases
- [ ] Real-time website monitoring
- [ ] API endpoint for web integration
- [ ] Advanced text analysis (sentiment, topics)
- [ ] Multi-language support

---

**Made with ❤️ for the Coursera community**
