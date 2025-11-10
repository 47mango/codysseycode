# client_app.py
import requests

BASE_URL = "http://127.0.0.1:8000"


def print_response(title: str, resp: requests.Response):
    print(f"\n=== {title} ===")
    print(f"Status: {resp.status_code}")
    try:
        print(resp.json())
    except Exception:
        print(resp.text)


def create_todo():
    data = {
        "title": "클라이언트에서 추가한 TODO",
        "description": "client_app.py 테스트",
        "done": False,
    }
    resp = requests.post(f"{BASE_URL}/todo", json=data)
    print_response("CREATE TODO", resp)
    if resp.ok:
        return resp.json()["todo"]["id"]
    return None


def get_all_todos():
    resp = requests.get(f"{BASE_URL}/todo")
    print_response("GET ALL TODOS", resp)


def get_single_todo(todo_id: int):
    resp = requests.get(f"{BASE_URL}/todo/{todo_id}")
    print_response(f"GET TODO id={todo_id}", resp)


def update_todo(todo_id: int):
    data = {
        "done": True,
        "description": "client_app.py에서 수정 완료",
    }
    resp = requests.put(f"{BASE_URL}/todo/{todo_id}", json=data)
    print_response(f"UPDATE TODO id={todo_id}", resp)


def delete_todo(todo_id: int):
    resp = requests.delete(f"{BASE_URL}/todo/{todo_id}")
    print_response(f"DELETE TODO id={todo_id}", resp)


if __name__ == "__main__":
    # 1. TODO 하나 생성
    new_id = create_todo()
    if new_id is None:
        print("TODO 생성 실패, 종료합니다.")
        raise SystemExit(1)

    # 2. 전체 목록 조회
    get_all_todos()

    # 3. 단건 조회
    get_single_todo(new_id)

    # 4. 수정
    update_todo(new_id)

    # 5. 수정 결과 확인
    get_single_todo(new_id)

    # 6. 삭제
    delete_todo(new_id)

    # 7. 최종 전체 목록 조회
    get_all_todos()
