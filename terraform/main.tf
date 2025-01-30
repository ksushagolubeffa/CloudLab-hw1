    terraform {
      required_providers {
        yandex = {
          source  = "yandex-cloud/yandex"
          version = "~> 0.102.0"
        }
      }
    }

    provider "yandex" {
      # Authentication will be via authorized key in ~/.yc-keys/key.json, no explicit key setup
      cloud_id  = var.yandex_cloud_id
      folder_id = var.yandex_folder_id
      zone      = var.yandex_zone
    }

    # Create a Yandex Object Storage bucket
    resource "yandex_storage_bucket" "instruction_bucket" {
      bucket = var.yandex_object_storage_bucket_name
      acl = "private" # Adjust as needed
      lifecycle_rule {
        enabled = true
        abort_incomplete_multipart_upload_days = 1
      }
    }

    resource "yandex_storage_object" "instruction_object" {
      bucket = yandex_storage_bucket.instruction_bucket.bucket
      key = "yandex_api_instruction.md"
      source = "yandex_api_instruction.md" # Local instruction file
    }

    # Create Yandex Cloud Function
    resource "yandex_function" "telegram_bot_function" {
       name            = "telegram-bot-function"
        description     = "Telegram bot cloud function"
        folder_id       = var.yandex_folder_id
        labels = {
            "managed-by" = "terraform" # Custom label
        }
        runtime         = "python311" # Select Python 3.11 or higher
        entrypoint      = "app.app"  #Assuming your main file is app.py and the function is called app()
        memory          = 128      # Customize memory
        timeout         = 60
        environment = {
              "BOT_TOKEN" = var.tg_bot_key # Telegram Bot API token
              "YANDEX_API_KEY" = var.yandex_api_key
              "YANDEX_OBJECT_STORAGE_BUCKET" = yandex_storage_bucket.instruction_bucket.bucket
              "YANDEX_OBJECT_STORAGE_KEY" = yandex_storage_object.instruction_object.key
              "YANDEX_OBJECT_STORAGE_ACCESS_KEY" = var.yandex_object_storage_access_key
              "YANDEX_OBJECT_STORAGE_SECRET_KEY" = var.yandex_object_storage_secret_key
              "PORT" = "8080"
              "YANDEX_CLOUD_ID" = var.yandex_cloud_id
              "YANDEX_FOLDER_ID" = var.yandex_folder_id
              "YANDEX_ZONE" = var.yandex_zone
              "INSTRUCTION_URL" = "https://${yandex_storage_bucket.bucket.bucket}.storage.yandexcloud.net/${yandex_storage_object.instruction.key}"
        }
        package {
          # Local zip archive with cloud function code (make sure to create this zip!)
           zip_path = "bot.zip"
        }
    }

    # Set up function access rights
    resource "yandex_function_iam_binding" "function_invoker" {
              function_id = yandex_function.telegram_bot_function.id
        role = "roles/functions.invoker" # Make function publicly invokable
        members = ["allUsersAuthenticated"]
    }
     # Extract function URL
     resource "null_resource" "print_function_url" {
         depends_on = [yandex_function.telegram_bot_function]
           provisioner "local-exec" {
               command = "echo URL: $(yc functions function get ${yandex_function.telegram_bot_function.id}  --format json | jq -r '.http_invoke_url')"
           }
       }
    # Configure the webhook (create)
    resource "null_resource" "set_webhook" {
     depends_on = [yandex_function_iam_binding.function_invoker, null_resource.print_function_url]
        provisioner "local-exec" {
          command = <<EOF
          FUNCTION_URL=$(yc functions function get ${yandex_function.telegram_bot_function.id}  --format json | jq -r '.http_invoke_url')
          curl -s -X POST "https://api.telegram.org/bot${var.tg_bot_key}/setWebhook" -H "Content-Type: application/json" -d "{\\"url\\": \\"$FUNCTION_URL\\"}"
          EOF
        }
    }

    # Configure the webhook (destroy)
    resource "null_resource" "delete_webhook" {
       provisioner "local-exec" {
          command = <<EOF
          curl -s -X POST "https://api.telegram.org/bot${var.tg_bot_key}/deleteWebhook"
          EOF
       }
      triggers = {
       always_run = timestamp() # To make sure that we always delete webhook on destroy
      }
      lifecycle {
      create_before_destroy = true # Make sure that destroy will be called before creation
      }
    }

