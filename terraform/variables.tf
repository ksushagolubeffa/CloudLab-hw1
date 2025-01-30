    variable "yandex_cloud_id" {
      description = "Yandex Cloud ID"
      type        = string
    }

    variable "yandex_folder_id" {
      description = "Yandex Folder ID"
      type        = string
    }

    variable "tg_bot_key" {
      description = "Telegram Bot API token"
      type        = string
       sensitive = true # Prevent value showing in output
    }

     variable "yandex_api_key" {
       description = "Yandex API Key (Vision, LLM or other)"
      type        = string
       sensitive = true # Prevent value showing in output
    }

    variable "yandex_object_storage_bucket_name" {
        description = "Name for Yandex Object Storage bucket"
        type = string
      default = "telegram-bot-bucket-instruction"
    }
    variable "yandex_zone" {
       description = "Yandex Zone"
        type      = string
       default     = "ru-central1-a"
    }
     variable "yandex_object_storage_access_key" {
       description = "Yandex Object Storage Access Key"
       type = string
       sensitive = true # Prevent value showing in output
    }
    variable "yandex_object_storage_secret_key" {
       description = "Yandex Object Storage Secret Key"
       type = string
       sensitive = true # Prevent value showing in output
    }
