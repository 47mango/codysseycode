# todo.py
from typing import Dict, Any, List

from fastapi import FastAPI, APIRouter, HTTPException

app = FastAPI()
router = APIRouter()

# 리스트 객체
todo_list: List[Dict[str, Any]] = []


@router.post("/todo", response_model=Dict[str, Any])
async def add_todo(item: Dict[str, Any]):
    """
    todo_list에 새로운 항목을 추가하는 POST 메소드
    입력/출력 모두 Dict 타입
    """
    # 입력 Dict가 비어 있으면 경고(에러) 반환
    if not item:
        # FastAPI에서 HTTPException을 쓰면 JSON 형태(dict)로 응답됨
        raise HTTPException(
            status_code=400,
            detail="입력된 Dict가 비어 있습니다. 값을 넣어 주세요."
        )

    todo_list.append(item)
    return {
        "message": "TODO가 추가되었습니다.",
        "todo": item,
        "count": len(todo_list),
    }


@router.get("/todo", response_model=Dict[str, Any])
async def retrieve_todo():
    """
    todo_list를 가져오는 GET 메소드
    출력은 Dict 타입
    """
    return {
        "todo_list": todo_list,
        "count": len(todo_list),
    }


# APIRouter 등록
app.include_router(router)
