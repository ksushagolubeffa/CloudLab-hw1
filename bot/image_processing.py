import os
import requests
import json
import logging
import configparser

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
        # yandex_api_key = os.environ.get("YANDEX_API_KEY")
        if not yandex_api_key:
           raise ValueError("YANDEX_API_KEY environment variable not set")
        try:
          url = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"
          headers = {
              "Authorization": f"Api-Key {yandex_api_key}",
              'x-folder-id': f'{yandex_folder_id}',
              "Content-Type": "application/json"
          }

        #   image_content = image_bytes.decode('latin-1') # Encode bytes to content
          payload = {
            'mimeType': 'JPEG',
            'languageCodes': ['ru'],
            'model': 'page',
            'content': image_content,
          }
        #   payload = {
        #       "analyze_specs": [{
        #           "content": image_content,
        #           "features": [{
        #               "type": "TEXT_DETECTION",
        #           }]
        #       }]
        #   }
          response = requests.post(url, headers=headers, json=payload)
          response.raise_for_status()
          response_json = response.json()

          if response_json and response_json["results"] and response_json["results"][0]["results"] and response_json["results"][0]["results"][0]["textDetection"] and response_json["results"][0]["results"][0]["textDetection"]["pages"]:
              full_text = ""
              for page in response_json["results"][0]["results"][0]["textDetection"]["pages"]:
                  for block in page["blocks"]:
                      for line in block["lines"]:
                          full_text += " ".join([word["text"] for word in line["words"]]) + " "
                  full_text+="\n" #Add new line
              return full_text.strip()
          else:
                logging.warning(f"Unexpected Yandex Vision OCR response format: {response_json}")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Error during Yandex Vision API request: {e}")
            return None
        except json.JSONDecodeError as e:
          logging.error(f"Error decoding Yandex Vision API JSON response: {e}")
          return None
        except Exception as e:
            logging.error(f"An unexpected error occurred in image processing: {e}")
            return None

