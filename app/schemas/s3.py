from pydantic import BaseModel

class FileUploadResponse(BaseModel):
    file_key: str
    download_url: str

class FileDeleteResponse(BaseModel):
    file_key: str
    message: str
