# import json

# class SwaggerExtractor:
#     def __init__(self, swagger_file):
#         self.swagger_file = swagger_file
#         self.swagger_data = self.load_swagger_file()
#         self.endpoints_info = []

#     def load_swagger_file(self):
#         with open(self.swagger_file, 'r') as file:
#             return json.load(file)

#     def extract_endpoints(self):
#         paths = self.swagger_data.get('paths', {})
#         for path, methods in paths.items():
#             for method, details in methods.items():
#                 self.endpoints_info.append({
#                     'url': f"{self.swagger_data['host']}{self.swagger_data['basePath']}{path}",
#                     'method': method.upper(),
#                     'request': self.extract_request_details(details),
#                     'response': self.extract_response_details(details)
#                 })

#     def extract_request_details(self, details):
#         parameters = details.get('parameters', [])
#         request_info = {
#             'description': details.get('summary', ''),
#             'parameters': []
#         }
        
#         for param in parameters:
#             request_info['parameters'].append({
#                 'name': param.get('name'),
#                 'in': param.get('in'),
#                 'required': param.get('required', False),
#                 'type': param.get('type'),
#                 'description': param.get('description', '')
#             })

#         return request_info

#     def extract_response_details(self, details):
#         responses = details.get('responses', {})
#         response_info = {}
        
#         for status_code, response in responses.items():
#             response_info[status_code] = {
#                 'description': response.get('description', ''),
#                 'schema': response.get('schema', {})
#             }

#         return response_info

#     def generate_output(self):
#         output = {
#             'endpoints': self.endpoints_info
#         }
#         return output

#     def transform_to_json(self):
#         transformed_data = {
#             "endpoints": []
#         }
    
#         for endpoint in self.endpoints_info:
#             transformed_data["endpoints"].append({
#                 "url": endpoint['url'],
#                 "method": endpoint['method'],
#                 "request": {
#                     "description": endpoint['request']['description'],
#                     "parameters": endpoint['request']['parameters']
#                 },
#                 "response": endpoint['response']
#             })
        
#         return transformed_data
    

# import json
# import google.generativeai as genai
# # from swagger_helper import SwaggerExtractor 
# import time
# import random
# from google.api_core.exceptions import ResourceExhausted


# class TestCasePromptBuilder:
#     def __init__(self, transformed_data):
#         self.transformed_data = transformed_data
#         self.genai_key = "AIzaSyBhRLbc8Lil9vNNgFS28ao3SZyCrpmKTs0"  # Replace with your actual API key

#         if not self.genai_key:
#             raise ValueError("genai_key must be set in the environment variables")

#         genai.configure(api_key=self.genai_key)

#     def build_prompts(self, limit=None):
#         prompts = []
        
#         # Shuffle the endpoints for random selection
#         endpoints = self.transformed_data["endpoints"]
#         random.shuffle(endpoints)

#         for endpoint in endpoints:
#             if limit is not None and len(prompts) >= limit:
#                 break  # Stop if the limit is reached

#             url = endpoint["url"]
#             method = endpoint["method"]
#             request = endpoint["request"]

#             # Ensure URL has the correct scheme
#             if not url.startswith("http://") and not url.startswith("https://"):
#                 url = "https://" + url  # Add HTTPS if missing

#             # Generate test case for the happy path
#             happy_case, expected_status_code = self.__genai_suggest(
#                 f"Generate a test case for the happy path of {method} {url}.",
#                 request["parameters"]
#             )
#             prompts.append({
#                 "description": happy_case,
#                 "functional_type": "happy_path",
#                 "request_method": method,
#                 "request": {
#                     "url": url,
#                     "parameters": request["parameters"]
#                 },
#                 "expected_response": {
#                     "status_code": expected_status_code,
#                     "description": "successful operation"
#                 }
#             })

#             # Generate test case for the error path
#             error_case, expected_status_code = self.__genai_suggest(
#                 f"Generate a test case for the error path of {method} {url}.",
#                 request["parameters"]
#             )
#             prompts.append({
#                 "description": error_case,
#                 "functional_type": "error_path",
#                 "request_method": method,
#                 "request": {
#                     "url": url,
#                     "parameters": request["parameters"]
#                 },
#                 "expected_response": {
#                     "status_code": expected_status_code,  # Dynamic based on generated content
#                     "description": "Invalid input"
#                 }
#             })

#         return prompts

#     def __genai_suggest(self, prompt, parameters):
#         model = genai.GenerativeModel('gemini-2.0-flash-exp')
#         # Construct a prompt for generating a specific test case
#         prompt_content = f"""
#         {prompt}
        
#         Please include the following mandatory parameters: {parameters}.
#         Provide a detailed test case including request payload and expected response.
#         """
#         retry_attempts = 3  # Set the number of retry attempts
#         for attempt in range(retry_attempts):
#             try:
#                 suggestions = model.generate_content(prompt_content)
#                 generated_text = suggestions.text

#                 # Determine expected status code based on content (you can refine this logic)
#                 if "success" in generated_text.lower():
#                     expected_status_code = 200 if "GET" in prompt else 201  # Assume 200 for GET, 201 for POST
#                 else:
#                     expected_status_code = 400  # Default to 400 for error cases

#                 return generated_text, expected_status_code
#             except genai.exceptions.ResourceExhausted as e:
#                 if attempt < retry_attempts - 1:  # Don't wait on the last attempt
#                     print("Quota exceeded. Retrying...")
#                     time.sleep(10)  # Wait for a while before retrying
#                 else:
#                     raise e  # Re-raise the exception after all attempts
                

# import json
# import google.generativeai as genai
# import requests
# # from swagger_helper import SwaggerExtractor
# # from prompt_helper import TestCasePromptBuilder  
# import time
# import matplotlib.pyplot as plt

# class TestRunner:
#     def __init__(self):
#         self.passed_count = 0
#         self.failed_count = 0
#         self.results = []  # Store results for the Markdown file

#     def run_test_cases(self, test_cases, limit=None):
#         if limit is not None:
#             test_cases = test_cases[:limit]
        
#         for test_case in test_cases:
#             print(f"Running test case: {test_case['description']}")
#             try:
#                 # Make the request
#                 response = requests.request(
#                     method=test_case["request_method"],
#                     url=test_case["request"]["url"],
#                     headers={"Content-Type": "application/json"},
#                     json=test_case.get("request", {}).get("payload", {})
#                 )

#                 actual_status_code = response.status_code
#                 actual_output = response.text

#                 # Validate the response
#                 expected_status_code = test_case["expected_response"]["status_code"]

#                 # Check if the actual status code falls within success or failure ranges
#                 if (expected_status_code in range(200, 300) and actual_status_code in range(200, 300)) or \
#                    (expected_status_code in range(400, 600) and actual_status_code in range(400, 600)):
#                     self.passed_count += 1
#                     status = "PASSED"
#                 else:
#                     self.failed_count += 1
#                     status = "FAILED"

#                 # Collect results
#                 self.results.append({
#                     "description": test_case['description'],
#                     "status": status,
#                     "expected": test_case["expected_response"],
#                     "actual": {
#                         "status_code": actual_status_code,
#                         "output": actual_output
#                     }
#                 })

#                 print(f"Test case '{test_case['description']}' executed with status: {status}")

#             except requests.exceptions.RequestException as e:
#                 self.failed_count += 1
#                 self.results.append({
#                     "description": test_case['description'],
#                     "status": "FAILED",
#                     "error": str(e)
#                 })
#                 print(f"Test case '{test_case['description']}' encountered an error: {e}")

#     def generate_results_markdown(self, store_name="Pet Store", author="Your Name", file_name="api-testing-agent-results.md"):
#         with open(file_name, 'w', encoding='utf-8') as f:  # Specify utf-8 encoding
#             f.write("# Test Results\n\n")
#             f.write(f"**Store Name:** {store_name}\n")
#             f.write(f"**Author:** {author}\n")
#             f.write(f"**Total Passed:** {self.passed_count}\n")
#             f.write(f"**Total Failed:** {self.failed_count}\n\n")

#             # Add some humor
#             f.write("## Summary\n")
#             f.write(f"- **Total Test Cases Executed:** {self.passed_count + self.failed_count}\n")
#             f.write(f"- **Passed:** {self.passed_count}\n")
#             f.write(f"- **Failed:** {self.failed_count}\n")
#             f.write("\n### Don't worry, it's just testing!\n")
#             f.write("It's not about how many times you fail, but how many times you get up! 🎉\n\n")

#             f.write("## Detailed Results\n")
#             for result in self.results:
#                 f.write(f"### Test Case: {result['description']}\n")
#                 f.write(f"- **Status:** {result['status']}\n")
#                 if result['status'] == "FAILED":
#                     f.write(f"- **Error:** {result.get('error', 'No error details available')}\n")
#                 else:
#                     f.write(f"- **Expected Response:**\n")
#                     f.write(f"  ```json\n{json.dumps(result['expected'], indent=4)}\n```\n")
#                     f.write(f"- **Actual Response:**\n")
#                     f.write(f"  ```json\n{json.dumps(result['actual'], indent=4)}\n```\n")
#                 f.write("\n")

#             # Embed the pie chart image
#             f.write("## Test Case Results Pie Chart\n")
#             f.write("![Test Case Results](test_case_results_pie_chart.png)\n")  # Adjust the path if needed

#             # Optionally, you can add a footer
#             f.write("---\n")
#             f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

#     def generate_pie_chart(self):
#             labels = 'Passed', 'Failed'
#             sizes = [self.passed_count, self.failed_count]
#             colors = ['lightgreen', 'salmon']
#             explode = (0.1, 0)  # explode the 1st slice (i.e., 'Passed')

#             plt.figure(figsize=(8, 5))
#             plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
#             plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
#             plt.title('Test Case Results')
#             plt.savefig('test_case_results_pie_chart.png')  # Save as image
#             plt.close()

# # Load the Swagger file and extract endpoints
# extractor = SwaggerExtractor('petstore_swagger.json')
# extractor.extract_endpoints()
# transformed_json = extractor.transform_to_json()

# # Build prompts for generating test cases
# prompt_builder = TestCasePromptBuilder(transformed_json)
# prompts = prompt_builder.build_prompts(limit=5)

# # Create TestRunner instance and execute the generated test cases
# test_runner = TestRunner()

# # Execute the test cases
# test_runner.run_test_cases(prompts, limit=None)

# # Generate pie chart for test case results
# test_runner.generate_pie_chart()

# # Generate results Markdown file
# test_runner.generate_results_markdown(store_name="Pet Store", author="Ibrahim Nasr")

#======================================
#======================================
#======================================


import requests
import json
import logging
import asyncio
import aiohttp
from playwright.async_api import async_playwright
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import re
from concurrent.futures import ThreadPoolExecutor
import time
from bs4 import BeautifulSoup
import google.generativeai as genai
import matplotlib.pyplot as plt
from collections import defaultdict

@dataclass
class APIEndpoint:
    url: str
    method: str
    content_type: Optional[str] = None
    request_payload: Optional[Dict] = None
    response_payload: Optional[Dict] = None
    status_code: Optional[int] = None
    headers: Optional[Dict] = None
    source_page: Optional[str] = None
    triggered_by: Optional[str] = None  # UI element that triggered the request

class WebAPIDiscoveryAgent:
    def __init__(self, domain: str, max_pages: int = 100):
        self.domain = self.normalize_domain(domain)
        self.max_pages = max_pages
        self.discovered_endpoints: Set[APIEndpoint] = set()
        self.visited_pages: Set[str] = set()
        self.setup_logging()
        self.api_patterns = self.compile_api_patterns()
        self.setup_request_interception()

    @staticmethod
    def normalize_domain(domain: str) -> str:
        if not domain.startswith(('http://', 'https://')):
            domain = f'https://{domain}'
        return domain.rstrip('/')

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('api_discovery.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('WebAPIDiscoveryAgent')

    @staticmethod
    def compile_api_patterns():
        """Compile regex patterns for identifying API endpoints"""
        return [
            re.compile(r'/api/[\w/\-{}]+'),
            re.compile(r'/v\d+/[\w/\-{}]+'),
            re.compile(r'/_api/[\w/\-{}]+'),
            re.compile(r'/rest/[\w/\-{}]+'),
            re.compile(r'/graphql'),
            re.compile(r'/gateway/[\w/\-{}]+'),
            re.compile(r'/service/[\w/\-{}]+')
        ]

    def setup_request_interception(self):
        """Setup network request interception configuration"""
        self.intercept_patterns = [
            "**/api/*",
            "**/v1/*",
            "**/v2/*",
            "**/graphql",
            "**/rest/*",
            "**/gateway/*",
            "**/service/*"
        ]

    async def discover_api_endpoints(self):
        """Main method to discover API endpoints"""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )

            # Enable request interception
            await context.route("**/*", self.route_handler)
            
            page = await context.new_page()
            await self.crawl_website(page)
            await browser.close()

    async def route_handler(self, route, request):
        """Handle intercepted network requests"""
        if any(request.url.startswith(self.domain + pattern) for pattern in self.intercept_patterns):
            try:
                response = await route.fetch()
                endpoint = APIEndpoint(
                    url=request.url,
                    method=request.method,
                    content_type=request.headers.get('content-type'),
                    request_payload=await self.parse_request_payload(request),
                    response_payload=await self.parse_response_payload(response),
                    status_code=response.status,
                    headers=dict(response.headers),
                    source_page=request.frame.url,
                    triggered_by=await self.identify_trigger_element(request)
                )
                self.discovered_endpoints.add(endpoint)
                self.logger.info(f"Discovered API endpoint: {endpoint.url}")
            except Exception as e:
                self.logger.error(f"Error handling request {request.url}: {str(e)}")
        await route.continue_()

    async def crawl_website(self, page):
        """Crawl website and interact with UI elements"""
        try:
            # Navigate to the main page
            await page.goto(self.domain)
            await self.process_page(page)

            # Get all links on the page
            links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a')).map(a => a.href)
            """)

            # Process each link
            for link in links[:self.max_pages]:
                if link.startswith(self.domain) and link not in self.visited_pages:
                    self.visited_pages.add(link)
                    await page.goto(link)
                    await self.process_page(page)

        except Exception as e:
            self.logger.error(f"Error crawling website: {str(e)}")

    async def process_page(self, page):
        """Process a single page and interact with UI elements"""
        await page.wait_for_load_state('networkidle')

        # Interact with common UI elements
        await self.interact_with_elements(page)

        # Handle infinite scroll
        await self.handle_infinite_scroll(page)

        # Handle dynamic content loading
        await self.handle_dynamic_content(page)

    async def interact_with_elements(self, page):
        """Interact with various UI elements to trigger API calls"""
        # Click buttons
        buttons = await page.query_selector_all('button, [role="button"]')
        for button in buttons:
            try:
                await button.click()
                await page.wait_for_timeout(500)  # Wait for potential API calls
            except Exception:
                continue

        # Fill forms
        forms = await page.query_selector_all('form')
        for form in forms:
            try:
                # Fill input fields
                inputs = await form.query_selector_all('input[type="text"]')
                for input_field in inputs:
                    await input_field.fill('test')

                # Submit form
                submit_button = await form.query_selector('button[type="submit"]')
                if submit_button:
                    await submit_button.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                continue

    async def handle_infinite_scroll(self, page):
        """Handle infinite scroll pagination"""
        last_height = await page.evaluate('document.body.scrollHeight')
        while True:
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)  # Wait for content to load
            new_height = await page.evaluate('document.body.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height

    async def handle_dynamic_content(self, page):
        """Handle dynamically loaded content"""
        # Wait for AJAX requests to complete
        await page.wait_for_load_state('networkidle')

        # Click "Load More" buttons
        load_more_buttons = await page.query_selector_all(
            'button:has-text("Load More"), button:has-text("Show More")'
        )
        for button in load_more_buttons:
            try:
                await button.click()
                await page.wait_for_timeout(1000)
            except Exception:
                continue

    @staticmethod
    async def parse_request_payload(request):
        """Parse request payload"""
        try:
            if request.post_data:
                return json.loads(request.post_data)
            return None
        except Exception:
            return None

    @staticmethod
    async def parse_response_payload(response):
        """Parse response payload"""
        try:
            body = await response.body()
            return json.loads(body)
        except Exception:
            return None

    @staticmethod
    async def identify_trigger_element(request):
        """Identify UI element that triggered the request"""
        try:
            # Get the stack trace if available
            stack = request.frame.evaluate("""
                Error.stack
            """)
            return stack
        except Exception:
            return None

class EnhancedTestRunner:
    def __init__(self, discovered_endpoints: Set[APIEndpoint]):
        self.discovered_endpoints = discovered_endpoints
        self.test_results = []
        self.setup_genai()
        self.logger = logging.getLogger('EnhancedTestRunner')

    def setup_genai(self):
        """Setup Google's Generative AI"""
        try:
            genai.configure(api_key="AIzaSyBhRLbc8Lil9vNNgFS28ao3SZyCrpmKTs0")
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception as e:
            self.logger.error(f"Failed to setup GenAI: {str(e)}")

    async def run_tests(self):
        """Run tests for all discovered endpoints"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for endpoint in self.discovered_endpoints:
                tasks.append(self.test_endpoint(session, endpoint))
            await asyncio.gather(*tasks)

    async def test_endpoint(self, session, endpoint: APIEndpoint):
        """Test a single endpoint"""
        # Generate test cases
        test_cases = await self.generate_test_cases(endpoint)
        
        for test_case in test_cases:
            try:
                async with session.request(
                    method=endpoint.method,
                    url=endpoint.url,
                    json=test_case.get('request_payload'),
                    headers=endpoint.headers
                ) as response:
                    result = {
                        'endpoint': endpoint,
                        'test_case': test_case,
                        'status_code': response.status,
                        'response': await response.json(),
                        'success': response.status == test_case.get('expected_status_code')
                    }
                    self.test_results.append(result)
            except Exception as e:
                self.logger.error(f"Error testing endpoint {endpoint.url}: {str(e)}")

    async def generate_test_cases(self, endpoint: APIEndpoint):
        """Generate test cases using AI"""
        prompt = f"""
        Generate test cases for API endpoint:
        URL: {endpoint.url}
        Method: {endpoint.method}
        Sample Request: {endpoint.request_payload}
        Sample Response: {endpoint.response_payload}
        
        Include:
        1. Happy path test
        2. Error cases
        3. Edge cases
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Parse and structure the generated test cases
            return self.parse_generated_test_cases(response.text)
        except Exception:
            # Return default test cases if AI generation fails
            return self.get_default_test_cases(endpoint)

    def get_default_test_cases(self, endpoint: APIEndpoint):
        """Generate default test cases when AI generation fails"""
        return [
            {
                'name': 'Happy Path Test',
                'request_payload': endpoint.request_payload,
                'expected_status_code': 200,
                'description': 'Verify successful response'
            },
            {
                'name': 'Error Path Test',
                'request_payload': {},
                'expected_status_code': 400,
                'description': 'Verify error handling with empty payload'
            }
        ]

    def parse_generated_test_cases(self, generated_text: str):
        """Parse AI-generated test cases into structured format"""
        # Basic parsing implementation
        test_cases = []
        try:
            # Split by numbered items
            cases = re.split(r'\d+\.', generated_text)
            for case in cases[1:]:  # Skip first empty split
                test_cases.append({
                    'name': case.strip().split('\n')[0],
                    'request_payload': {},  # Default empty payload
                    'expected_status_code': 200,  # Default success code
                    'description': case.strip()
                })
        except Exception as e:
            self.logger.error(f"Error parsing generated test cases: {str(e)}")
            return self.get_default_test_cases(None)
        
        return test_cases

    def generate_html_report(self, total_tests: int, passed_tests: int) -> str:
        """Generate HTML test report"""
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>API Test Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    line-height: 1.6;
                }}
                .header {{
                    background-color: #f4f4f4;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .summary {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 30px;
                }}
                .stat-box {{
                    background-color: #fff;
                    border: 1px solid #ddd;
                    padding: 15px;
                    border-radius: 5px;
                    text-align: center;
                    flex: 1;
                    margin: 0 10px;
                }}
                .test-details {{
                    margin-top: 30px;
                }}
                .test-case {{
                    border: 1px solid #ddd;
                    padding: 15px;
                    margin-bottom: 15px;
                    border-radius: 5px;
                }}
                .success {{
                    border-left: 5px solid #4CAF50;
                }}
                .failure {{
                    border-left: 5px solid #f44336;
                }}
                .endpoint-url {{
                    color: #666;
                    font-family: monospace;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>API Test Report</h1>
                <p>Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="summary">
                <div class="stat-box">
                    <h3>Total Tests</h3>
                    <p>{total_tests}</p>
                </div>
                <div class="stat-box">
                    <h3>Passed</h3>
                    <p style="color: #4CAF50">{passed_tests}</p>
                </div>
                <div class="stat-box">
                    <h3>Failed</h3>
                    <p style="color: #f44336">{failed_tests}</p>
                </div>
                <div class="stat-box">
                    <h3>Pass Rate</h3>
                    <p>{pass_rate:.1f}%</p>
                </div>
            </div>

            <div class="test-details">
                <h2>Test Details</h2>
        """

        # Add test case details
        for result in self.test_results:
            endpoint = result['endpoint']
            test_case = result['test_case']
            success = result['success']
            
            html += f"""
                <div class="test-case {'success' if success else 'failure'}">
                    <h3>{test_case['name']}</h3>
                    <p class="endpoint-url">{endpoint.method} {endpoint.url}</p>
                    <p><strong>Status:</strong> {'Passed' if success else 'Failed'}</p>
                    <p><strong>Status Code:</strong> {result['status_code']}</p>
                    <p><strong>Description:</strong> {test_case['description']}</p>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html

    def generate_visualizations(self):
        """Generate visualizations for the test results"""
        # Create a pie chart
        passed = sum(1 for result in self.test_results if result['success'])
        failed = len(self.test_results) - passed

        plt.figure(figsize=(8, 8))
        plt.pie([passed, failed], 
                labels=['Passed', 'Failed'],
                colors=['#4CAF50', '#f44336'],
                autopct='%1.1f%%',
                startangle=90)
        plt.title('Test Results Distribution')
        plt.axis('equal')
        plt.savefig('test_results_pie_chart.png')
        plt.close()

    def generate_report(self):
        """Generate comprehensive test report"""
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        # Generate HTML report
        report = self.generate_html_report(total_tests, passed_tests)
        
        # Save report
        with open('api_test_report.html', 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Generate visualization
        self.generate_visualizations()

def main():
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Web API Discovery and Testing Tool')
    parser.add_argument('domain', help='Domain to scan (e.g., www.example.com)')
    parser.add_argument('--max-pages', type=int, default=100, help='Maximum pages to scan')
    args = parser.parse_args()

    # Create and run the discovery agent
    discovery_agent = WebAPIDiscoveryAgent(args.domain, args.max_pages)
    asyncio.run(discovery_agent.discover_api_endpoints())

    # Run tests
    test_runner = EnhancedTestRunner(discovery_agent.discovered_endpoints)
    asyncio.run(test_runner.run_tests())
    test_runner.generate_report()

if __name__ == "__main__":
    main()





#======================================
#======================================
#======================================
# import asyncio
# import playwright.async_api as pw
# import aiohttp
# import json
# import logging
# from dataclasses import dataclass, asdict
# from typing import List, Dict, Set, Optional
# from urllib.parse import urljoin, urlparse
# import re
# from bs4 import BeautifulSoup
# from datetime import datetime
# import sqlite3
# import hashlib
# from concurrent.futures import ThreadPoolExecutor
# import pandas as pd
# from tqdm import tqdm

# @dataclass
# class APIEndpoint:
#     url: str
#     method: str
#     request_headers: Optional[Dict] = None
#     request_payload: Optional[Dict] = None
#     response_status: Optional[int] = None
#     response_headers: Optional[Dict] = None
#     response_type: Optional[str] = None
#     source_page: Optional[str] = None
#     timestamp: str = datetime.now().isoformat()

# class DatabaseManager:
#     def __init__(self, db_name: str = "api_discovery.db"):
#         self.conn = sqlite3.connect(db_name)
#         self.create_tables()

#     def create_tables(self):
#         self.conn.execute('''
#             CREATE TABLE IF NOT EXISTS endpoints (
#                 id TEXT PRIMARY KEY,
#                 url TEXT,
#                 method TEXT,
#                 request_headers TEXT,
#                 request_payload TEXT,
#                 response_status INTEGER,
#                 response_headers TEXT,
#                 response_type TEXT,
#                 source_page TEXT,
#                 timestamp TEXT
#             )
#         ''')
#         self.conn.commit()

#     def save_endpoint(self, endpoint: APIEndpoint):
#         endpoint_id = hashlib.md5(
#             f"{endpoint.url}:{endpoint.method}:{endpoint.source_page}".encode()
#         ).hexdigest()
        
#         self.conn.execute('''
#             INSERT OR REPLACE INTO endpoints 
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (
#             endpoint_id,
#             endpoint.url,
#             endpoint.method,
#             json.dumps(endpoint.request_headers),
#             json.dumps(endpoint.request_payload),
#             endpoint.response_status,
#             json.dumps(endpoint.response_headers),
#             endpoint.response_type,
#             endpoint.source_page,
#             endpoint.timestamp
#         ))
#         self.conn.commit()

# class NetworkTrafficInterceptor:
#     def __init__(self, base_url: str):
#         self.base_url = base_url
#         self.api_endpoints: Set[APIEndpoint] = set()
#         self.base_domain = urlparse(base_url).netloc

#     async def handle_request(self, route: pw.Route, request: pw.Request):
#         """Intercept and analyze network requests"""
#         url = request.url
        
#         # Filter out non-API requests
#         if self.is_api_request(url, request.resource_type):
#             endpoint = APIEndpoint(
#                 url=url,
#                 method=request.method,
#                 request_headers=dict(request.headers),
#                 request_payload=request.post_data,
#                 source_page=request.frame.url
#             )
#             self.api_endpoints.add(endpoint)
        
#         await route.continue_()

#     def is_api_request(self, url: str, resource_type: str) -> bool:
#         """Determine if a request is an API call"""
#         # Check if the URL belongs to the same domain or subdomains
#         url_domain = urlparse(url).netloc
#         if not (url_domain == self.base_domain or url_domain.endswith('.' + self.base_domain)):
#             return False

#         # API indicators in URL
#         api_patterns = [
#             r'/api/v?\d*/',
#             r'/rest/',
#             r'/graphql',
#             r'/service/',
#             r'/_api/',
#             r'/gateway/',
#             r'/endpoint/'
#         ]

#         # Check resource type and patterns
#         is_api = (
#             resource_type in ['fetch', 'xhr', 'websocket'] or
#             any(re.search(pattern, url) for pattern in api_patterns) or
#             'json' in url.lower() or
#             'api' in url.lower()
#         )

#         return is_api

# class WebCrawler:
#     def __init__(self, base_url: str, db_manager: DatabaseManager):
#         self.base_url = base_url
#         self.db_manager = db_manager
#         self.visited_urls: Set[str] = set()
#         self.pending_urls: Set[str] = {base_url}
#         self.interceptor = NetworkTrafficInterceptor(base_url)
#         self.setup_logging()

#     def setup_logging(self):
#         logging.basicConfig(
#             level=logging.INFO,
#             format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#             handlers=[
#                 logging.FileHandler('crawler.log'),
#                 logging.StreamHandler()
#             ]
#         )
#         self.logger = logging.getLogger('WebCrawler')

#     async def crawl(self):
#         """Main crawling logic"""
#         async with pw.async_playwright() as playwright:
#             browser = await playwright.chromium.launch(headless=True)
#             context = await browser.new_context(
#                 viewport={'width': 1920, 'height': 1080},
#                 user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
#             )

#             # Set up network interception
#             await context.route('**/*', self.interceptor.handle_request)

#             while self.pending_urls:
#                 url = self.pending_urls.pop()
#                 if url in self.visited_urls:
#                     continue

#                 try:
#                     page = await context.new_page()
#                     await self.process_page(page, url)
#                     self.visited_urls.add(url)
#                 except Exception as e:
#                     self.logger.error(f"Error processing {url}: {str(e)}")
#                 finally:
#                     await page.close()

#             await context.close()
#             await browser.close()

#     async def process_page(self, page: pw.Page, url: str):
#         """Process a single page"""
#         self.logger.info(f"Processing page: {url}")

#         try:
#             # Navigate to the page
#             response = await page.goto(url, wait_until='networkidle')
#             if not response:
#                 return

#             # Wait for dynamic content
#             await page.wait_for_load_state('networkidle')

#             # Interact with the page to trigger potential API calls
#             await self.interact_with_page(page)

#             # Extract new URLs
#             new_urls = await self.extract_urls(page)
#             self.pending_urls.update(new_urls - self.visited_urls)

#             # Save discovered endpoints
#             for endpoint in self.interceptor.api_endpoints:
#                 self.db_manager.save_endpoint(endpoint)

#         except Exception as e:
#             self.logger.error(f"Error on page {url}: {str(e)}")

#     async def interact_with_page(self, page: pw.Page):
#         """Interact with page elements to trigger API calls"""
#         try:
#             # Scroll page
#             await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
#             await page.wait_for_timeout(1000)

#             # Click buttons
#             buttons = await page.query_selector_all('button:visible, [role="button"]:visible')
#             for button in buttons[:5]:  # Limit to first 5 buttons to avoid infinite loops
#                 try:
#                     await button.click()
#                     await page.wait_for_timeout(500)
#                 except:
#                     continue

#             # Interact with forms
#             forms = await page.query_selector_all('form')
#             for form in forms:
#                 await self.interact_with_form(form)

#         except Exception as e:
#             self.logger.error(f"Error during page interaction: {str(e)}")

#     async def interact_with_form(self, form: pw.ElementHandle):
#         """Fill and submit forms to trigger API calls"""
#         try:
#             # Find input fields
#             inputs = await form.query_selector_all('input:visible')
            
#             # Fill inputs with test data
#             for input_field in inputs:
#                 input_type = await input_field.get_attribute('type') or 'text'
#                 if input_type in ['text', 'email', 'password']:
#                     await input_field.fill('test')

#             # Submit form
#             submit_button = await form.query_selector('[type="submit"]')
#             if submit_button:
#                 await submit_button.click()
#                 await form.page.wait_for_timeout(1000)

#         except Exception as e:
#             self.logger.error(f"Error interacting with form: {str(e)}")

#     async def extract_urls(self, page: pw.Page) -> Set[str]:
#         """Extract relevant URLs from the page"""
#         urls = set()
#         base_domain = urlparse(self.base_url).netloc

#         # Get all links
#         links = await page.evaluate('''() => {
#             return Array.from(document.querySelectorAll('a[href]')).map(a => a.href);
#         }''')

#         # Filter and clean URLs
#         for url in links:
#             parsed_url = urlparse(url)
#             if parsed_url.netloc == base_domain and not url.startswith(('#', 'javascript:')):
#                 urls.add(url)

#         return urls

# class APITester:
#     def __init__(self, db_manager: DatabaseManager):
#         self.db_manager = db_manager

#     async def test_endpoints(self):
#         """Test all discovered API endpoints"""
#         async with aiohttp.ClientSession() as session:
#             cursor = self.db_manager.conn.execute('SELECT * FROM endpoints')
#             endpoints = cursor.fetchall()

#             for endpoint_data in tqdm(endpoints, desc="Testing endpoints"):
#                 endpoint = self.create_endpoint_from_db_row(endpoint_data)
#                 await self.test_endpoint(session, endpoint)

#     async def test_endpoint(self, session: aiohttp.ClientSession, endpoint: APIEndpoint):
#         """Test a single API endpoint"""
#         try:
#             async with session.request(
#                 method=endpoint.method,
#                 url=endpoint.url,
#                 headers=endpoint.request_headers or {},
#                 json=endpoint.request_payload,
#                 ssl=False
#             ) as response:
#                 endpoint.response_status = response.status
#                 endpoint.response_headers = dict(response.headers)
#                 self.db_manager.save_endpoint(endpoint)

#         except Exception as e:
#             logging.error(f"Error testing endpoint {endpoint.url}: {str(e)}")

#     @staticmethod
#     def create_endpoint_from_db_row(row: tuple) -> APIEndpoint:
#         """Create APIEndpoint object from database row"""
#         return APIEndpoint(
#             url=row[1],
#             method=row[2],
#             request_headers=json.loads(row[3]) if row[3] else None,
#             request_payload=json.loads(row[4]) if row[4] else None,
#             response_status=row[5],
#             response_headers=json.loads(row[6]) if row[6] else None,
#             response_type=row[7],
#             source_page=row[8],
#             timestamp=row[9]
#         )

# class ReportGenerator:
#     def __init__(self, db_manager: DatabaseManager):
#         self.db_manager = db_manager

#     def generate_report(self, output_file: str = "api_discovery_report.html"):
#         """Generate comprehensive HTML report"""
#         # Get all endpoints
#         cursor = self.db_manager.conn.execute('SELECT * FROM endpoints')
#         endpoints = cursor.fetchall()
        
#         # Convert to DataFrame for analysis
#         df = pd.DataFrame(endpoints, columns=[
#             'id', 'url', 'method', 'request_headers', 'request_payload',
#             'response_status', 'response_headers', 'response_type', 'source_page', 'timestamp'
#         ])

#         # Generate HTML report
#         with open(output_file, 'w') as f:
#             f.write('''
#             <html>
#             <head>
#                 <title>API Discovery Report</title>
#                 <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
#                 <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
#             </head>
#             <body>
#             ''')

#             # Write summary statistics
#             f.write(f'''
#             <div class="container mt-5">
#                 <h1>API Discovery Report</h1>
#                 <div class="row">
#                     <div class="col-md-4">
#                         <div class="card">
#                             <div class="card-body">
#                                 <h5 class="card-title">Total Endpoints</h5>
#                                 <p class="card-text">{len(df)}</p>
#                             </div>
#                         </div>
#                     </div>
#                     <div class="col-md-4">
#                         <div class="card">
#                             <div class="card-body">
#                                 <h5 class="card-title">HTTP Methods</h5>
#                                 <p class="card-text">{df['method'].value_counts().to_dict()}</p>
#                             </div>
#                         </div>
#                     </div>
#                     <div class="col-md-4">
#                         <div class="card">
#                             <div class="card-body">
#                                 <h5 class="card-title">Response Status Codes</h5>
#                                 <p class="card-text">{df['response_status'].value_counts().to_dict()}</p>
#                             </div>
#                         </div>
#                     </div>
#                 </div>
#             ''')

#             # Write detailed endpoint table
#             f.write('''
#             <div class="mt-5">
#                 <h2>Endpoint Details</h2>
#                 <table class="table table-striped">
#                     <thead>
#                         <tr>
#                             <th>URL</th>
#                             <th>Method</th>
#                             <th>Status</th>
#                             <th>Source Page</th>
#                         </tr>
#                     </thead>
#                     <tbody>
#             ''')

#             for _, row in df.iterrows():
#                 f.write(f'''
#                     <tr>
#                         <td>{row['url']}</td>
#                         <td>{row['method']}</td>
#                         <td>{row['response_status']}</td>
#                         <td>{row['source_page']}</td>
#                     </tr>
#                 ''')

#             f.write('''
#                     </tbody>
#                 </table>
#             </div>
#             ''')

#             f.write('''
#             </div>
#             </body>
#             </html>
#             ''')

# async def main():
#     # Initialize database
#     db_manager = DatabaseManager()

#     # Initialize crawler
#     crawler = WebCrawler("https://www.saucedemo.com/v1/", db_manager)
    
#     # Crawl website
#     await crawler.crawl()

#     # Test discovered endpoints
#     tester = APITester(db_manager)
#     await tester.test_endpoints()

#     # Generate report
#     report_generator = ReportGenerator(db_manager)
#     report_generator.generate_report()

# if __name__ == "__main__":
#     asyncio.run(main())
