import os
import requests
import json
import logging
import configparser
import base64

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
        
async def recognize_text_from_image(image_content):
    config = read_tfvars()
    yandex_api_key = config.get('yandex_api_key').strip('"')
    yandex_folder_id = config.get('yandex_folder_id').strip('"')

    if not yandex_api_key:
        raise ValueError("YANDEX_API_KEY environment variable not set")

    try:
        
        url = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"
        headers = {
            "Authorization": f"Api-Key {yandex_api_key}",
            'x-folder-id': f'{yandex_folder_id}',
            "Content-Type": "application/json",
        }

        data = {
            'mimeType': 'jpeg',
            'languageCodes': ['ru'],
            'model': 'page',
            'content': image_content
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            result = response.json().get('result', {})
            text_annotation = result.get('textAnnotation', {})
            if text_annotation:
                ocr_text = text_annotation.get('fullText', '')
                if ocr_text:
                    return 'Ответь на билет:\n\n' + ocr_text
                else:
                    return None
            else:
                logging.error(f"No text: {text_annotation}")
                return None
        else:
            logging.error(f"Status code: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Error during Yandex OCR API request: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding Yandex OCR API JSON response: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred in image processing: {e}")
        return None