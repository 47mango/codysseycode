# todo.py
from typing import Dict, Any, List

from fastapi import FastAPI, APIRouter, HTTPException
from model import TodoItem

app = FastAPI()
router = APIRouter()

# TODO 리스트와 ID 카운터
todo_list: List[Dict[str, Any]] = []
current_id: int = 0


@router.post("/todo", response_model=Dict[str, Any])
async def add_todo(item: Dict[str, Any]):
    """
    todo_list에 새로운 항목을 추가하는 POST 메소드
    - 입력/출력 Dict
    - 입력 Dict가 비어 있으면 경고(에러) 반환
    """
    global current_id

    if not item:
        raise HTTPException(
            status_code=400,
            detail="입력된 Dict가 비어 있습니다. 값을 넣어 주세요."
        )

    todo = {"id": current_id}
    todo.update(item)  # 사용자가 보낸 값 덮어쓰기
    todo_list.append(todo)
    current_id += 1

    return {
        "message": "TODO가 추가되었습니다.",
        "todo": todo,
        "count": len(todo_list),
    }


@router.get("/todo", response_model=Dict[str, Any])
async def retrieve_todo():
    """
    전체 todo_list를 가져오는 GET 메소드
    - 출력 Dict
    """
    return {
        "todo_list": todo_list,
        "count": len(todo_list),
    }


@router.get("/todo/{todo_id}", response_model=Dict[str, Any])
async def get_single_todo(todo_id: int):
    """
    개별 TODO 조회 (GET /todo/{todo_id})
    - 경로 매개변수로 id 사용
    """
    for todo in todo_list:
        if todo.get("id") == todo_id:
            return {"todo": todo}

    raise HTTPException(
        status_code=404,
        detail=f"id={todo_id} 인 TODO를 찾을 수 없습니다."
    )


@router.put("/todo/{todo_id}", response_model=Dict[str, Any])
async def update_todo(todo_id: int, item: TodoItem):
    """
    TODO 수정 (PUT /todo/{todo_id})
    - 경로 매개변수: todo_id
    - 요청 본문: TodoItem(BaseModel)
    - 보낸 필드만 부분 수정
    """
    item_data = item.dict(exclude_unset=True)

    if not item_data:
        # 모델은 들어왔지만 안에 내용이 전부 비어 있는 경우
        raise HTTPException(
            status_code=400,
            detail="수정할 내용이 비어 있습니다."
        )

    for idx, todo in enumerate(todo_list):
        if todo.get("id") == todo_id:
            todo_list[idx].update(item_data)
            return {
                "message": "TODO가 수정되었습니다.",
                "todo": todo_list[idx],
            }

    raise HTTPException(
        status_code=404,
        detail=f"id={todo_id} 인 TODO를 찾을 수 없습니다."
    )


@router.delete("/todo/{todo_id}", response_model=Dict[str, Any])
async def delete_single_todo(todo_id: int):
    """
    TODO 삭제 (DELETE /todo/{todo_id})
    - 경로 매개변수: todo_id
    """
    for idx, todo in enumerate(todo_list):
        if todo.get("id") == todo_id:
            removed = todo_list.pop(idx)
            return {
                "message": "TODO가 삭제되었습니다.",
                "todo": removed,
                "count": len(todo_list),
            }

    raise HTTPException(
        status_code=404,
        detail=f"id={todo_id} 인 TODO를 찾을 수 없습니다."
    )


# APIRouter 등록
app.include_router(router)
