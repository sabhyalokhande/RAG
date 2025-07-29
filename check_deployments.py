import requests
import json

# Azure OpenAI configuration
api_key = "DT7N5LlmoXALRGppU1Jgcyrm1tt69ZOhnduXguB7Xkhte4wOTy2lJQQJ99AKACYeBjFXJ3w3AAABACOGPMfj"
endpoint = "https://botwot-opanai.openai.azure.com"
api_version = "2023-06-01-preview"

# Get deployments
url = f"{endpoint}/openai/deployments?api-version={api_version}"
headers = {"api-key": api_key}

try:
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}") 