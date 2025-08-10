"""
Dynamic Action Handler for RAG System
- Automatically detects when documents require API calls or actions
- Executes actions dynamically based on document content
- Supports various action types: API calls, form submissions, calculations
- Maintains security and error handling
"""

import re
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Union, Tuple
from urllib.parse import urlparse, parse_qs
import time
from config import config

logger = logging.getLogger(__name__)

class ActionDetector:
    """Detects actions required by documents."""
    
    def __init__(self):
        self.action_patterns = {
            'api_call': [
                r'https?://[^\s]+',  # URLs
                r'api[_-]?endpoint',  # API endpoint mentions
                r'call\s+[a-z]+\s+api',  # API call instructions
                r'fetch\s+from\s+[^\s]+',  # Fetch instructions
                r'get\s+data\s+from',  # Data retrieval
                r'execute\s+mission',  # Mission execution
                r'step\s+\d+:',  # Step-by-step instructions
                r'follow\s+steps'  # Step following
            ],
            'form_submission': [
                r'submit\s+form',  # Form submission
                r'fill\s+out',  # Form filling
                r'provide\s+information',  # Information provision
                r'enter\s+details'  # Detail entry
            ],
            'calculation': [
                r'calculate',  # Calculation requests
                r'compute',  # Computation
                r'formula',  # Mathematical formulas
                r'equation',  # Equations
                r'math',  # Mathematical content
                r'solve'  # Problem solving
            ],
            'mission_execution': [
                r'mission\s+brief',  # Mission brief
                r'execute\s+challenge',  # Challenge execution
                r'follow\s+mission',  # Mission following
                r'complete\s+steps',  # Step completion
                r'get\s+flight\s+number',  # Flight number retrieval
                r'retrieve\s+city',  # City retrieval
                r'map\s+to\s+landmark'  # Landmark mapping
            ]
        }
        
        self.url_patterns = {
            'hackrx': r'register\.hackrx\.in',
            'api_endpoint': r'https?://[^\s]+',
            'data_retrieval': r'get.*data|fetch.*data|retrieve.*data'
        }
    
    def detect_actions(self, content: str, query: str = None) -> List[Dict[str, Any]]:
        """
        Detect actions required by document content and query.
        
        Args:
            content: Document content
            query: User query
            
        Returns:
            List of detected actions
        """
        actions = []
        content_lower = content.lower()
        query_lower = query.lower() if query else ""
        
        # Detect action types
        for action_type, patterns in self.action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    actions.append({
                        'type': action_type,
                        'pattern': pattern,
                        'context': self._extract_context(content, pattern)
                    })
                    break
        
        # Detect URLs and endpoints
        urls = self._extract_urls(content)
        for url in urls:
            actions.append({
                'type': 'api_call',
                'url': url,
                'domain': self._extract_domain(url),
                'context': self._extract_url_context(content, url)
            })
        
        # Detect mission-specific actions
        if self._is_mission_document(content, query):
            mission_actions = self._detect_mission_actions(content, query)
            actions.extend(mission_actions)
        
        return actions
    
    def _extract_context(self, content: str, pattern: str) -> str:
        """Extract context around a pattern match."""
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            start = max(0, match.start() - 100)
            end = min(len(content), match.end() + 100)
            return content[start:end].strip()
        return ""
    
    def _extract_urls(self, content: str) -> List[str]:
        """Extract URLs from content."""
        url_pattern = r'https?://[^\s]+'
        return re.findall(url_pattern, content)
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""
    
    def _extract_url_context(self, content: str, url: str) -> str:
        """Extract context around a URL."""
        return self._extract_context(content, re.escape(url))
    
    def _is_mission_document(self, content: str, query: str) -> bool:
        """Check if document is a mission document."""
        mission_indicators = [
            'mission', 'challenge', 'execute', 'steps', 'flight number',
            'city', 'landmark', 'endpoint', 'solve'
        ]
        
        content_lower = content.lower()
        query_lower = query.lower() if query else ""
        
        return any(indicator in content_lower or indicator in query_lower 
                  for indicator in mission_indicators)
    
    def _detect_mission_actions(self, content: str, query: str) -> List[Dict[str, Any]]:
        """Detect mission-specific actions."""
        actions = []
        
        # Detect city retrieval
        if 'city' in query.lower() or 'favorite city' in query.lower():
            actions.append({
                'type': 'mission_execution',
                'action': 'get_favorite_city',
                'endpoint': 'https://register.hackrx.in/submissions/myFavouriteCity',
                'method': 'GET',
                'description': 'Retrieve favorite city from API'
            })
        
        # Detect flight number retrieval
        if 'flight number' in query.lower() or 'flight' in query.lower():
            actions.append({
                'type': 'mission_execution',
                'action': 'get_flight_number',
                'endpoint': 'dynamic',  # Will be determined based on city/landmark
                'method': 'GET',
                'description': 'Retrieve flight number based on city and landmark mapping'
            })
        
        # Detect landmark mapping
        if 'landmark' in query.lower() or 'map' in query.lower():
            actions.append({
                'type': 'mission_execution',
                'action': 'map_city_to_landmark',
                'endpoint': 'local',  # Local mapping operation
                'method': 'MAPPING',
                'description': 'Map city to corresponding landmark using document data'
            })
        
        return actions

class DynamicActionExecutor:
    """Executes actions detected in documents."""
    
    def __init__(self):
        self.detector = ActionDetector()
        self.session = requests.Session()
        self.default_timeout = config.REQUEST_TIMEOUT
        
        # Common HTTP headers
        self.default_headers = {
            'User-Agent': 'RAG-System/1.0',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json'
        }
        
        # Domain-specific configurations
        self.domain_configs = {
            'register.hackrx.in': {
                'timeout': config.REQUEST_TIMEOUT,
                'retries': 3,
                'headers': {
                    'User-Agent': 'HackRx-Mission/1.0'
                }
            }
        }
    
    def execute_actions(self, content: str, query: str, document_url: str = None) -> Dict[str, Any]:
        """
        Execute all required actions for a document and query.
        
        Args:
            content: Document content
            query: User query
            document_url: Document URL
            
        Returns:
            Results of executed actions
        """
        try:
            # Detect required actions
            actions = self.detector.detect_actions(content, query)
            
            if not actions:
                return {'actions_executed': [], 'results': {}, 'status': 'no_actions_required'}
            
            results = {}
            executed_actions = []
            
            # Execute each action
            for action in actions:
                try:
                    if action['type'] == 'mission_execution':
                        result = self._execute_mission_action(action, content, query)
                    elif action['type'] == 'api_call':
                        result = self._execute_api_call(action)
                    else:
                        result = {'status': 'not_implemented', 'action': action}
                    
                    results[action.get('action', action['type'])] = result
                    executed_actions.append({
                        'action': action,
                        'result': result,
                        'status': 'success'
                    })
                    
                except Exception as e:
                    logger.error(f"Error executing action {action}: {e}")
                    results[action.get('action', action['type'])] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    executed_actions.append({
                        'action': action,
                        'result': {'status': 'error', 'error': str(e)},
                        'status': 'failed'
                    })
            
            return {
                'actions_executed': executed_actions,
                'results': results,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error in execute_actions: {e}")
            return {
                'actions_executed': [],
                'results': {},
                'status': 'error',
                'error': str(e)
            }
    
    def _execute_mission_action(self, action: Dict[str, Any], content: str, query: str) -> Dict[str, Any]:
        """Execute mission-specific actions."""
        action_name = action.get('action', '')
        
        if action_name == 'get_favorite_city':
            return self._get_favorite_city()
        elif action_name == 'map_city_to_landmark':
            return self._map_city_to_landmark(content)
        elif action_name == 'get_flight_number':
            return self._get_flight_number_dynamic(content)
        else:
            return {'status': 'unknown_action', 'action': action_name}
    
    def _get_favorite_city(self) -> Dict[str, Any]:
        """Get favorite city from API."""
        try:
            url = "https://register.hackrx.in/submissions/myFavouriteCity"
            response = self._make_request('GET', url)
            
            if response['status'] == 'success':
                city_data = response['data']
                city = self._extract_city_from_response(city_data)
                return {
                    'status': 'success',
                    'city': city,
                    'raw_response': city_data
                }
            else:
                return {'status': 'error', 'error': response.get('error', 'Unknown error')}
                
        except Exception as e:
            logger.error(f"Error getting favorite city: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _map_city_to_landmark(self, content: str) -> Dict[str, Any]:
        """Map city to landmark using document content."""
        try:
            # Extract city-landmark mappings from document
            mappings = self._extract_city_landmark_mappings(content)
            
            if not mappings:
                return {'status': 'error', 'error': 'No city-landmark mappings found in document'}
            
            return {
                'status': 'success',
                'mappings': mappings,
                'count': len(mappings)
            }
            
        except Exception as e:
            logger.error(f"Error mapping city to landmark: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_flight_number_dynamic(self, content: str) -> Dict[str, Any]:
        """Get flight number dynamically based on document content."""
        try:
            # First get the favorite city
            city_result = self._get_favorite_city()
            if city_result['status'] != 'success':
                return city_result
            
            city = city_result['city']
            
            # Map city to landmark
            landmark_result = self._map_city_to_landmark(content)
            if landmark_result['status'] != 'success':
                return landmark_result
            
            # Find the specific mapping for this city
            city_mappings = landmark_result['mappings']
            landmark = None
            
            for mapping in city_mappings:
                if mapping['city'].lower() == city.lower():
                    landmark = mapping['landmark']
                    break
            
            if not landmark:
                return {'status': 'error', 'error': f'No landmark found for city: {city}'}
            
            # Get the appropriate endpoint based on landmark
            endpoint = self._get_flight_endpoint_by_landmark(landmark, content)
            if not endpoint:
                return {'status': 'error', 'error': f'No endpoint found for landmark: {landmark}'}
            
            # Get flight number from endpoint
            flight_result = self._make_request('GET', endpoint)
            if flight_result['status'] == 'success':
                flight_data = flight_result['data']
                flight_number = self._extract_flight_number_from_response(flight_data)
                
                return {
                    'status': 'success',
                    'city': city,
                    'landmark': landmark,
                    'endpoint': endpoint,
                    'flight_number': flight_number,
                    'trace_info': {
                        'city': city,
                        'landmark': landmark,
                        'endpoint': endpoint,
                        'flight_number': flight_number,
                        'steps_completed': [
                            'Retrieved favorite city from API',
                            'Mapped city to landmark using document data',
                            'Selected flight endpoint based on landmark rules',
                            'Retrieved flight number from endpoint'
                        ]
                    }
                }
            else:
                return {'status': 'error', 'error': flight_result.get('error', 'Unknown error')}
                
        except Exception as e:
            logger.error(f"Error getting flight number: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _extract_city_landmark_mappings(self, content: str) -> List[Dict[str, str]]:
        """Extract city-landmark mappings from document content."""
        mappings = []
        
        # Debug: Log content length and first part
        logger.info(f"Extracting city-landmark mappings from content length: {len(content)}")
        logger.info(f"Content preview: {content[:500]}...")
        
        # First, try to find structured mappings in code-like format
        if 'CITY_TO_LANDMARK' in content:
            logger.info("Found CITY_TO_LANDMARK in content")
            # Extract from code-like structures
            code_pattern = r'CITY_TO_LANDMARK\s*=\s*\{([^}]+)\}'
            code_match = re.search(code_pattern, content, re.DOTALL)
            if code_match:
                code_content = code_match.group(1)
                logger.info(f"Code content: {code_content}")
                # Parse the code structure
                code_mappings = self._parse_code_mappings(code_content)
                mappings.extend(code_mappings)
                if mappings:
                    logger.info(f"Found {len(mappings)} structured mappings")
                    return mappings  # Return early if we found structured mappings
        
        # Look for table-like structures
        table_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\|\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # City | Landmark
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # City Landmark (space separated)
        ]
        
        for pattern in table_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                city = match[0].strip()
                landmark = match[1].strip()
                
                # Filter out obvious non-mappings
                if (len(city) > 2 and len(landmark) > 2 and 
                    city.lower() not in ['the', 'and', 'or', 'for', 'with', 'city', 'landmark'] and
                    landmark.lower() not in ['the', 'and', 'or', 'for', 'with', 'city', 'landmark']):
                    mappings.append({
                        'city': city,
                        'landmark': landmark
                    })
        
        # Look for more specific mapping patterns
        specific_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # City: Landmark
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*-\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # City - Landmark
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*→\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # City → Landmark
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*=\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # City = Landmark
        ]
        
        for pattern in specific_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                city = match[0].strip()
                landmark = match[1].strip()
                
                # Filter out obvious non-mappings
                if (len(city) > 2 and len(landmark) > 2 and 
                    city.lower() not in ['the', 'and', 'or', 'for', 'with', 'city', 'landmark'] and
                    landmark.lower() not in ['the', 'and', 'or', 'for', 'with', 'city', 'landmark']):
                    mappings.append({
                        'city': city,
                        'landmark': landmark
                    })
        
        # If still no mappings, try to find any city-like and landmark-like words
        if not mappings:
            logger.info("No structured mappings found, trying fallback keyword search")
            # Look for common city names and landmarks
            city_keywords = ['delhi', 'mumbai', 'chennai', 'hyderabad', 'new york', 'london', 'tokyo', 'paris', 'berlin']
            landmark_keywords = ['gateway', 'taj mahal', 'eiffel tower', 'big ben', 'statue of liberty', 'temple', 'fort', 'palace']
            
            logger.info(f"Searching for cities: {city_keywords}")
            logger.info(f"Searching for landmarks: {landmark_keywords}")
            
            for city in city_keywords:
                if city in content.lower():
                    logger.info(f"Found city '{city}' in content")
                    # Try to find a nearby landmark
                    city_pos = content.lower().find(city)
                    nearby_text = content[max(0, city_pos-100):city_pos+100]
                    logger.info(f"Nearby text for '{city}': {nearby_text}")
                    
                    for landmark in landmark_keywords:
                        if landmark in nearby_text.lower():
                            logger.info(f"Found landmark '{landmark}' near city '{city}'")
                            mappings.append({
                                'city': city.title(),
                                'landmark': landmark.title()
                            })
                            break
        
        return mappings
    
    def _parse_code_mappings(self, code_content: str) -> List[Dict[str, str]]:
        """Parse code-like mapping structures."""
        mappings = []
        
        # Look for "City": "Landmark" patterns
        pattern = r'"([^"]+)":\s*"([^"]+)"'
        matches = re.findall(pattern, code_content)
        
        for match in matches:
            city = match[0].strip()
            landmark = match[1].strip()
            mappings.append({
                'city': city,
                'landmark': landmark
            })
        
        return mappings
    
    def _get_flight_endpoint_by_landmark(self, landmark: str, content: str) -> Optional[str]:
        """Get flight endpoint based on landmark using document content."""
        # Look for endpoint mappings in the document
        endpoint_patterns = [
            r'([^"]+):\s*(https?://[^\s]+)',  # Landmark: URL
            r'([^"]+)\s*→\s*(https?://[^\s]+)',  # Landmark → URL
            r'([^"]+)\s*=\s*(https?://[^\s]+)',  # Landmark = URL
        ]
        
        for pattern in endpoint_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                doc_landmark = match[0].strip()
                endpoint = match[1].strip()
                
                if doc_landmark.lower() == landmark.lower():
                    return endpoint
        
        # If no specific mapping found, look for default patterns
        if 'getFirstCityFlightNumber' in content:
            return "https://register.hackrx.in/teams/public/flights/getFirstCityFlightNumber"
        elif 'getSecondCityFlightNumber' in content:
            return "https://register.hackrx.in/teams/public/flights/getSecondCityFlightNumber"
        elif 'getThirdCityFlightNumber' in content:
            return "https://register.hackrx.in/teams/public/flights/getThirdCityFlightNumber"
        elif 'getFourthCityFlightNumber' in content:
            return "https://register.hackrx.in/teams/public/flights/getFourthCityFlightNumber"
        elif 'getFifthCityFlightNumber' in content:
            return "https://register.hackrx.in/teams/public/flights/getFifthCityFlightNumber"
        
        return None
    
    def _extract_city_from_response(self, response_data: Any) -> str:
        """Extract city from API response."""
        if isinstance(response_data, dict):
            # Check for nested data structure
            if 'data' in response_data and isinstance(response_data['data'], dict):
                data = response_data['data']
                for key in ['city', 'name', 'location', 'result']:
                    if key in data:
                        return str(data[key]).strip()
            
            # Check for direct keys
            for key in ['city', 'name', 'location', 'result']:
                if key in response_data:
                    return str(response_data[key]).strip()
            
            # If no common key found, convert the whole dict to string
            return str(response_data).strip()
        else:
            # If it's already a string
            return str(response_data).strip()
    
    def _extract_flight_number_from_response(self, response_data: Any) -> str:
        """Extract flight number from API response."""
        if isinstance(response_data, dict):
            # Check for nested data structure
            if 'data' in response_data and isinstance(response_data['data'], dict):
                data = response_data['data']
                for key in ['flightNumber', 'flight_number', 'number', 'result']:
                    if key in data:
                        return str(data[key]).strip()
            
            # Check for direct keys
            for key in ['flightNumber', 'flight_number', 'number', 'result']:
                if key in response_data:
                    return str(response_data[key]).strip()
            
            # If no common key found, convert the whole dict to string
            return str(response_data).strip()
        else:
            # If it's already a string
            return str(response_data).strip()
    
    def _execute_api_call(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a generic API call."""
        try:
            url = action.get('url', '')
            method = action.get('method', 'GET')
            
            if not url:
                return {'status': 'error', 'error': 'No URL provided'}
            
            response = self._make_request(method, url)
            return response
            
        except Exception as e:
            logger.error(f"Error executing API call: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _make_request(self, method: str, url: str, data: Any = None, headers: Dict = None) -> Dict[str, Any]:
        """Make HTTP request with proper error handling."""
        try:
            # Get domain-specific configuration
            domain = self._extract_domain(url)
            config = self.domain_configs.get(domain, {})
            
            # Prepare headers
            request_headers = self.default_headers.copy()
            if headers:
                request_headers.update(headers)
            if config.get('headers'):
                request_headers.update(config['headers'])
            
            # Prepare timeout
            timeout = config.get('timeout', self.default_timeout)
            
            # Make request
            if method.upper() == 'GET':
                response = self.session.get(url, headers=request_headers, timeout=timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=request_headers, timeout=timeout)
            else:
                return {'status': 'error', 'error': f'Unsupported method: {method}'}
            
            # Handle response
            response.raise_for_status()
            
            # Parse response
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                response_data = response.json()
            else:
                response_data = response.text.strip()
            
            return {
                'status': 'success',
                'data': response_data,
                'status_code': response.status_code,
                'headers': dict(response.headers)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed for {url}: {e}")
            return {'status': 'error', 'error': f'HTTP request failed: {str(e)}'}
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return {'status': 'error', 'error': f'Unexpected error: {str(e)}'}
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""

# Global instances
action_detector = ActionDetector()
dynamic_action_executor = DynamicActionExecutor()

def execute_document_actions(content: str, query: str, document_url: str = None) -> Dict[str, Any]:
    """
    Execute actions required by a document.
    
    Args:
        content: Document content
        query: User query
        document_url: Document URL
        
    Returns:
        Results of executed actions
    """
    return dynamic_action_executor.execute_actions(content, query, document_url)

def detect_document_actions(content: str, query: str = None) -> List[Dict[str, Any]]:
    """
    Detect actions required by a document.
    
    Args:
        content: Document content
        query: User query
        
    Returns:
        List of detected actions
    """
    return action_detector.detect_actions(content, query)
