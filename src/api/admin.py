"""管理后台 API 路由"""
import os
from functools import wraps
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from db.repositories import checkin as checkin_repo


router = APIRouter(prefix="/api/admin")


def get_admin_key():
    """动态获取管理密钥"""
    return os.getenv("ADMIN_KEY", "")


def require_admin_key(x_admin_key: Optional[str] = Header(None)):
    """验证管理员密钥"""
    admin_key = get_admin_key()
    
    if not admin_key:
        raise HTTPException(
            status_code=500,
            detail="服务器未配置管理密钥，请设置 ADMIN_KEY 环境变量"
        )
    
    if not x_admin_key or x_admin_key != admin_key:
        raise HTTPException(
            status_code=401,
            detail="无效的管理密钥"
        )
    
    return True


@router.get("/stats")
async def get_stats(authorized: bool = Depends(require_admin_key)):
    """获取统计信息"""
    stats = checkin_repo.get_stats()
    return {
        "success": True,
        "data": stats
    }


@router.get("/pending")
async def get_pending_list(
    page: int = 1,
    limit: int = 20,
    authorized: bool = Depends(require_admin_key)
):
    """获取待审核列表"""
    checkins, total = checkin_repo.get_pending_list(page, limit)
    
    return {
        "success": True,
        "data": {
            "items": [c.to_dict() for c in checkins],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0
        }
    }


@router.post("/approve/{checkin_id}")
async def approve_checkin(
    checkin_id: int,
    authorized: bool = Depends(require_admin_key)
):
    """通过审核"""
    # 检查记录是否存在
    checkin = checkin_repo.get_by_id(checkin_id)
    if not checkin:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    success = checkin_repo.approve(checkin_id)
    
    if success:
        return {"success": True, "message": f"已通过审核 #{checkin_id}"}
    else:
        raise HTTPException(status_code=500, detail="操作失败")


@router.post("/reject/{checkin_id}")
async def reject_checkin(
    checkin_id: int,
    authorized: bool = Depends(require_admin_key)
):
    """拒绝审核（删除记录）"""
    # 检查记录是否存在
    checkin = checkin_repo.get_by_id(checkin_id)
    if not checkin:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    success = checkin_repo.reject(checkin_id)
    
    if success:
        return {"success": True, "message": f"已拒绝并删除 #{checkin_id}"}
    else:
        raise HTTPException(status_code=500, detail="操作失败")


@router.post("/ban/{checkin_id}")
async def ban_checkin(
    checkin_id: int,
    authorized: bool = Depends(require_admin_key)
):
    """封禁并加入黑名单（基于 IP）"""
    # 检查记录是否存在
    checkin = checkin_repo.get_by_id(checkin_id)
    if not checkin:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    ip_address = checkin.ip_address
    banned_ip = False
    
    # 如果有 IP 地址，加入黑名单
    if ip_address:
        blacklist_path = Path(__file__).parent.parent / "data" / "blacklist.txt"
        try:
            with open(blacklist_path, 'a') as f:
                f.write(f"{ip_address}\n")
            banned_ip = True
        except Exception:
            pass  # 写入失败不影响删除操作
    
    # 删除记录
    success = checkin_repo.reject(checkin_id)
    
    if success:
        msg = f"已封禁并删除 #{checkin_id}"
        if banned_ip:
            msg += f"，IP {ip_address} 已加入黑名单"
        return {"success": True, "message": msg}
    else:
        raise HTTPException(status_code=500, detail="操作失败")


@router.post("/batch/approve")
async def batch_approve(
    request: Request,
    authorized: bool = Depends(require_admin_key)
):
    """批量通过审核"""
    data = await request.json()
    ids = data.get("ids", [])
    
    if not ids:
        raise HTTPException(status_code=400, detail="请提供要操作的 ID 列表")
    
    success_count = 0
    for checkin_id in ids:
        if checkin_repo.approve(checkin_id):
            success_count += 1
    
    return {
        "success": True,
        "message": f"已通过 {success_count}/{len(ids)} 条记录"
    }


@router.post("/batch/reject")
async def batch_reject(
    request: Request,
    authorized: bool = Depends(require_admin_key)
):
    """批量拒绝审核"""
    data = await request.json()
    ids = data.get("ids", [])
    
    if not ids:
        raise HTTPException(status_code=400, detail="请提供要操作的 ID 列表")
    
    success_count = 0
    for checkin_id in ids:
        if checkin_repo.reject(checkin_id):
            success_count += 1
    
    return {
        "success": True,
        "message": f"已拒绝 {success_count}/{len(ids)} 条记录"
    }


@router.get("/all")
async def get_all_checkins(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,  # "pending", "approved", "all"
    authorized: bool = Depends(require_admin_key)
):
    """获取所有记录（管理员视角）"""
    if status == "pending":
        checkins, total = checkin_repo.get_pending_list(page, limit)
    elif status == "approved":
        checkins, total = checkin_repo.get_list(page, limit, approved_only=True)
    else:
        checkins, total = checkin_repo.get_list(page, limit, approved_only=False)
    
    return {
        "success": True,
        "data": {
            "items": [c.to_dict() for c in checkins],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0
        }
    }
