"""
Keywords History API Routes
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.api.dependencies import get_db
from app.api.schemas import MessageResponse
from app.repositories.stored_keyword_repository import StoredKeywordRepository
from app.models.task import Task
from sqlalchemy import distinct
from app.utils.cache import get_cache

router = APIRouter(prefix="/api/keywords", tags=["Keywords"])
cache = get_cache()


@router.get("/history")
async def get_keywords_history(
    country: str = Query(..., description="國家代碼"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    獲取某個國家的歷史關鍵字列表（包含任務中的和用戶自定義的）
    
    Get historical keywords for a specific country from both tasks and stored keywords.
    Uses caching to improve performance.
    """
    # Try to get from cache first
    cache_key = f"keywords:history:{country}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    stored_repo = StoredKeywordRepository(db)
    
    # 從 stored_keywords 表獲取用戶自定義的關鍵字
    stored_keywords = stored_repo.get_keywords_by_country(country)
    
    # 從 tasks 表獲取使用過的關鍵字（去重）
    task_keywords = (
        db.query(distinct(Task.keyword))
        .filter(Task.country == country)
        .order_by(Task.keyword)
        .all()
    )
    task_keyword_list = [kw[0] for kw in task_keywords if kw[0] and kw[0].strip()]
    
    # 合併並去重
    all_keywords = list(set(stored_keywords + task_keyword_list))
    all_keywords.sort()
    
    result = {
        "country": country,
        "keywords": all_keywords,
        "count": len(all_keywords)
    }
    
    # Cache for 5 minutes
    cache.set(cache_key, result, ttl=300)
    
    return result


@router.get("/cities/history")
async def get_cities_history(
    country: str = Query(..., description="國家代碼"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    獲取某個國家的歷史城市列表（包含任務中的和用戶自定義的）
    
    Get historical cities for a specific country from both tasks and stored keywords.
    Uses caching to improve performance.
    """
    # Try to get from cache first
    cache_key = f"cities:history:{country}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    stored_repo = StoredKeywordRepository(db)
    
    # 從 stored_keywords 表獲取用戶自定義的城市
    stored_cities = stored_repo.get_cities_by_country(country)
    
    # 從 tasks 表獲取使用過的城市（去重）
    task_cities = (
        db.query(distinct(Task.city))
        .filter(Task.country == country)
        .order_by(Task.city)
        .all()
    )
    task_city_list = [city[0] for city in task_cities if city[0] and city[0].strip()]
    
    # 合併並去重
    all_cities = list(set(stored_cities + task_city_list))
    all_cities.sort()
    
    result = {
        "country": country,
        "cities": all_cities,
        "count": len(all_cities)
    }
    
    # Cache for 5 minutes
    cache.set(cache_key, result, ttl=300)
    
    return result


@router.post("/add")
async def add_keyword(
    country: str = Query(..., description="國家代碼"),
    keyword: str = Query(..., description="關鍵字"),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    新增關鍵字到歷史記錄（如果已刪除則恢復）
    
    Add a keyword to stored keywords. If deleted, restore it.
    """
    if not keyword or not keyword.strip():
        raise HTTPException(status_code=400, detail="關鍵字不能為空")
    
    stored_repo = StoredKeywordRepository(db)
    
    # Check if exists and not deleted
    if stored_repo.keyword_exists(country, keyword):
        return MessageResponse(
            message="關鍵字已存在",
            detail=f"關鍵字 '{keyword}' 已經存在於 {country} 的歷史記錄中"
        )
    
    # Try to add (will restore if deleted)
    result = stored_repo.add_keyword(country, keyword)
    
    if result:
        # Clear cache for this country's keywords
        cache.delete(f"keywords:history:{country}")
        # Check if it was restored or newly created by checking if it was previously deleted
        # This is a simple check - if result exists, it was either restored or newly created
        # For better UX, we could add a flag, but for now we'll just say it was added
        return MessageResponse(
            message="關鍵字已新增",
            detail=f"關鍵字 '{keyword}' 已成功新增到 {country} 的歷史記錄"
        )
    else:
        # This shouldn't happen, but handle it just in case
        raise HTTPException(status_code=500, detail="新增關鍵字失敗，請稍後再試")


@router.post("/cities/add")
async def add_city(
    country: str = Query(..., description="國家代碼"),
    city: str = Query(..., description="城市"),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    新增城市到歷史記錄（如果已刪除則恢復）
    
    Add a city to stored keywords. If deleted, restore it.
    """
    if not city or not city.strip():
        raise HTTPException(status_code=400, detail="城市不能為空")
    
    stored_repo = StoredKeywordRepository(db)
    
    # Check if exists and not deleted
    if stored_repo.city_exists(country, city):
        return MessageResponse(
            message="城市已存在",
            detail=f"城市 '{city}' 已經存在於 {country} 的歷史記錄中"
        )
    
    # Try to add (will restore if deleted)
    result = stored_repo.add_city(country, city)
    
    if result:
        # Clear cache for this country's cities
        cache.delete(f"cities:history:{country}")
        return MessageResponse(
            message="城市已新增",
            detail=f"城市 '{city}' 已成功新增到 {country} 的歷史記錄"
        )
    else:
        # This shouldn't happen, but handle it just in case
        raise HTTPException(status_code=500, detail="新增城市失敗，請稍後再試")


@router.delete("/delete")
async def delete_keyword(
    country: str = Query(..., description="國家代碼"),
    keyword: str = Query(..., description="關鍵字"),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    刪除關鍵字（軟刪除，標記為已刪除）
    
    Delete a keyword (soft delete).
    """
    if not keyword or not keyword.strip():
        raise HTTPException(status_code=400, detail="關鍵字不能為空")
    
    stored_repo = StoredKeywordRepository(db)
    result = stored_repo.delete_keyword(country, keyword)
    
    if result:
        # Clear cache for this country's keywords
        cache.delete(f"keywords:history:{country}")
        return MessageResponse(
            message="關鍵字已刪除",
            detail=f"關鍵字 '{keyword}' 已從 {country} 的歷史記錄中刪除"
        )
    else:
        return MessageResponse(
            message="關鍵字不存在",
            detail=f"關鍵字 '{keyword}' 不存在於 {country} 的歷史記錄中"
        )


@router.delete("/cities/delete")
async def delete_city(
    country: str = Query(..., description="國家代碼"),
    city: str = Query(..., description="城市"),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    刪除城市（軟刪除，標記為已刪除）
    
    Delete a city (soft delete).
    """
    if not city or not city.strip():
        raise HTTPException(status_code=400, detail="城市不能為空")
    
    stored_repo = StoredKeywordRepository(db)
    result = stored_repo.delete_city(country, city)
    
    if result:
        # Clear cache for this country's cities
        cache.delete(f"cities:history:{country}")
        return MessageResponse(
            message="城市已刪除",
            detail=f"城市 '{city}' 已從 {country} 的歷史記錄中刪除"
        )
    else:
        return MessageResponse(
            message="城市不存在",
            detail=f"城市 '{city}' 不存在於 {country} 的歷史記錄中"
        )

