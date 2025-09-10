from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_current_user
from app.core.s3 import upload_file, generate_presigned_url, delete_file
from app.schemas.s3 import FileUploadResponse, FileDeleteResponse
from app.db.pg import get_db
from app.db.models import User

router = APIRouter()

# -------- Upload File --------
@router.post("/upload", response_model=FileUploadResponse)
async def upload(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    try:
        content = await file.read()
        file_key = upload_file(content, file.filename, file.content_type, user_id=current_user.id)
        download_url = generate_presigned_url(file_key)
        return {"file_key": file_key, "download_url": download_url}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# -------- Get Presigned URL --------
@router.get("/file/{file_key:path}", response_model=FileUploadResponse)
async def get_file(file_key: str, current_user: User = Depends(get_current_user)):
    try:
        url = generate_presigned_url(file_key)
        return {"file_key": file_key, "download_url": url}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# -------- Delete File --------
@router.delete("/file/{file_key:path}", response_model=FileDeleteResponse)
async def remove_file(file_key: str, current_user: User = Depends(get_current_user)):
    try:
        delete_file(file_key)
        return {"file_key": file_key, "message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
