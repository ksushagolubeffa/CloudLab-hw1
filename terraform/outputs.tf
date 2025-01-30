    output "bucket_name" {
       description = "Name of created object storage bucket"
      value = yandex_storage_bucket.instruction_bucket.bucket
    }

    output "instruction_object_key" {
      description = "Key for instruction object"
      value = yandex_storage_object.instruction_object.key
    }
