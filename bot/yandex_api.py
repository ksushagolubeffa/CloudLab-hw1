import os
import requests
import json
import logging
import boto3
import configparser
from botocore.exceptions import NoCredentialsError, ClientError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_tfvars(filename="terraform.tfvars"):
    """Reads variables from a Terraform tfvars file."""
    config = configparser.ConfigParser()
    full_path = os.path.join("terraform", filename)
    try:
        with open(full_path, "r") as f:
            config.read_string("[DEFAULT]\n" + f.read())  # tfvars не имеет секций, поэтому добавляем фиктивную
        return dict(config["DEFAULT"])
    except FileNotFoundError:
        print(f"Error: File not found: {full_path}")
        exit()
    except Exception as e:
        print(f"Error reading {full_path}: {e}")
        exit()
        
async def get_answer_from_yandex(question):
      config = read_tfvars()  
      yandex_api_key = config.get('yandex_api_key').strip('"')
      yandex_folder_id = config.get('yandex_folder_id').strip('"')
      yandex_object_storage_bucket = config.get('yandex_object_storage_bucket_name').strip('"')
      yandex_object_storage_key = config.get('yandex_object_key').strip('"')
      yandex_object_storage_access_key_id = config.get('yandex_object_storage_access_key').strip('"')
      yandex_object_storage_access_key = config.get('yandex_object_storage_secret_key').strip('"')
      if not yandex_api_key:
          raise ValueError("YANDEX_API_KEY environment variable not set")
      if not yandex_object_storage_bucket:
          raise ValueError("YANDEX_OBJECT_STORAGE_BUCKET environment variable not set")
      if not yandex_object_storage_key:
          raise ValueError("YANDEX_OBJECT_STORAGE_KEY environment variable not set")
      if not yandex_object_storage_access_key:
          raise ValueError("YANDEX_OBJECT_STORAGE_ACCESS_KEY environment variable not set")
      if not yandex_object_storage_access_key_id:
          raise ValueError("YANDEX_OBJECT_STORAGE_SECRET_KEY environment variable not set")

      try:
        # Fetch Instruction from Yandex Object Storage
        instruction = fetch_yandex_api_instruction(yandex_object_storage_bucket, yandex_object_storage_key, yandex_object_storage_access_key_id, yandex_object_storage_access_key)
        
        if not instruction:
          raise ValueError("Could not fetch Yandex API instruction from object storage.")
        # Replace with your actual API endpoint. For example, using Yandex GPT model
        url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            # "Authorization": f"Api-Key {yandex_api_key}",
            'Authorization': f'Api-Key {yandex_api_key}',
            'x-folder-id': f'{yandex_folder_id}',
            "Content-Type": "application/json"
            }
        messages = [
        {'role': 'system', 'text': instruction}, 
        {'role': 'user', 'text': question},
    ]
        payload = {
        'modelUri': f'gpt://{yandex_folder_id }/yandexgpt-lite/latest',
        'completionOptions': {
            'stream': False,
            'temperature': 0.6,
            'maxTokens': 1000
        },
        'messages': messages,
        }
 
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        try:
          response_json = response.json()
          if response_json and response_json['result'] and response_json['result']['alternatives'] and response_json['result']['alternatives'][0] and response_json['result']['alternatives'][0]['message']:
            return response_json['result']['alternatives'][0]['message']['text']
          else:
              logging.warning(f"Unexpected API response format, returning raw response: {response_json}")
              return f"Unexpected API response format: {response_json}" # Return the raw response to log it for debug
        except json.JSONDecodeError as e:
           logging.error(f"Error decoding JSON response: {e}")
           return "Error decoding JSON response from the API"
      except requests.exceptions.RequestException as e:
        logging.error(f"Error during API request: {e}")
        return f"Error communicating with the API: {e}" #Return some error message
      except Exception as e:
        logging.error(f"An unexpected error occured: {e}")
        return f"An unexpected error occurred: {e}"

def fetch_yandex_api_instruction(bucket_name, object_key, access_key_id, access_key):
       # Create an S3 client
       try:
            s3_client = boto3.client(
                's3',
                endpoint_url='https://storage.yandexcloud.net',
                aws_access_key_id=access_key_id,
                aws_secret_access_key=access_key,
            )
            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            if response and 'Body' in response:
                return response['Body'].read().decode('utf-8')
            else:
                logging.error(f"Failed to get instruction from S3 object: response = {response}")
                return None
       except NoCredentialsError:
            logging.error("Credentials not available")
            return None
       except ClientError as e:
            logging.error(f"Error fetching from S3: {e}")
            return None

