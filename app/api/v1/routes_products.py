# app/api/v1/routes_products.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.pg import get_db
from app.core.auth import get_current_active_user, get_current_superuser
from app.repos import product_repo
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.core.s3 import upload_file, generate_presigned_url

router = APIRouter()

# Create product - admin or seller (we treat superuser only for now)
@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db), current_admin = Depends(get_current_superuser)):
    product = await product_repo.create_product(db, owner_id=current_admin.id, name=data.name, price=data.price, stock=data.stock, description=data.description)
    return product

# List products - public
@router.get("/", response_model=List[ProductOut])
async def list_products(limit: int = Query(50, le=200), offset: int = 0, db: AsyncSession = Depends(get_db)):
    return await product_repo.list_products(db, limit=limit, offset=offset)

# Get product
@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await product_repo.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Update product - only owner or admin
@router.put("/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    product = await product_repo.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # allow if current_user is owner or superuser
    if product.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    updated = await product_repo.update_product(db, product, **data.dict(exclude_unset=True))
    return updated

# Delete product - only owner or admin
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    product = await product_repo.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    await product_repo.delete_product(db, product)
    return

# Upload product image (owner/admin)
@router.post("/{product_id}/image", response_model=ProductOut)
async def upload_image(product_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    product = await product_repo.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    content = await file.read()
    file_key = upload_file(content, file.filename, file.content_type, user_id=current_user.id)
    updated = await product_repo.update_product(db, product, image_key=file_key)
    return updated

# Get product image presigned URL
@router.get("/{product_id}/image-url")
async def product_image_url(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await product_repo.get_product(db, product_id)
    if not product or not product.image_key:
        raise HTTPException(status_code=404, detail="Image not found")
    url = generate_presigned_url(product.image_key)
    return {"url": url}
