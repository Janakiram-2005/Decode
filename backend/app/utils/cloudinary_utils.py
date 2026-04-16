import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Cloudinary
cloudinary.config( 
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.getenv("CLOUDINARY_API_KEY"), 
  api_secret = os.getenv("CLOUDINARY_API_SECRET"),
  secure = True
)

def upload_to_cloudinary(file_obj, folder="media_verification"):
    """
    Uploads a file-like object to Cloudinary.
    Returns the secure_url and public_id.
    """
    try:
        response = cloudinary.uploader.upload(
            file_obj,
            folder=folder,
            resource_type="auto" # Auto-detect image/video/raw
        )
        return {
            "url": response.get("secure_url"),
            "public_id": response.get("public_id"),
            "format": response.get("format"),
            "width": response.get("width"),
            "height": response.get("height")
        }
    except Exception as e:
        print(f"Cloudinary Upload Error: {str(e)}")
        raise e
