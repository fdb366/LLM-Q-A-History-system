# backend/app/api/endpoints/cloud_files.py
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.core.sync_database import get_db, SessionLocal
from app.models.sql.user import User
from app.models.sql.cloud_file import CloudFile
from app.api.dependencies.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(tags=["云盘"])

UPLOAD_DIR = "./uploads/cloud"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class CloudFileOut(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: Optional[str]
    conversation_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[CloudFileOut])
def get_cloud_files(
    conversation_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的云盘文件"""
    query = db.query(CloudFile).filter(CloudFile.uploader_id == current_user.id)
    
    if conversation_id is not None:
        query = query.filter(CloudFile.conversation_id == conversation_id)
    
    files = query.order_by(CloudFile.created_at.desc()).all()
    return files

@router.post("/upload")
async def upload_cloud_file(
    file: UploadFile = File(...),
    conversation_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """上传文件到云盘"""
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 保存到数据库
    db = SessionLocal()
    cloud_file = CloudFile(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        file_type=file.content_type,
        uploader_id=current_user.id,
        conversation_id=conversation_id
    )
    db.add(cloud_file)
    db.commit()
    db.refresh(cloud_file)
    db.close()
    
    return {
        "id": cloud_file.id,
        "filename": file.filename,
        "size": len(content),
        "path": file_path
    }

@router.get("/download/{file_id}")
def download_cloud_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载云盘文件"""
    from fastapi.responses import FileResponse
    
    cloud_file = db.query(CloudFile).filter(
        CloudFile.id == file_id,
        CloudFile.uploader_id == current_user.id
    ).first()
    
    if not cloud_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if not os.path.exists(cloud_file.file_path):
        raise HTTPException(status_code=404, detail="文件已删除")
    
    return FileResponse(
        path=cloud_file.file_path,
        filename=cloud_file.original_filename,
        media_type=cloud_file.file_type or "application/octet-stream"
    )

@router.delete("/{file_id}")
def delete_cloud_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除云盘文件"""
    cloud_file = db.query(CloudFile).filter(
        CloudFile.id == file_id,
        CloudFile.uploader_id == current_user.id
    ).first()
    
    if not cloud_file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 删除磁盘文件
    if os.path.exists(cloud_file.file_path):
        os.remove(cloud_file.file_path)
    
    # 删除数据库记录
    db.delete(cloud_file)
    db.commit()
    
    return {"msg": "删除成功"}
