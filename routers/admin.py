from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from supabase import Client

from core.database import get_db
from schemas import PoemCreate
from services.poem_service import PoemService
from dependencies.auth import get_admin_user

router = APIRouter(prefix="", tags=["admin"])

@router.get("/admin_panel", response_class=HTMLResponse)
async def admin_panel(request: Request, admin: dict = Depends(get_admin_user)):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("admin_panel.html", {"request": request, "current_user": admin})

@router.get("/api/poems")
async def get_all_poems_api(db: Client = Depends(get_db), admin: dict = Depends(get_admin_user)):
    poems_resp = db.table('poem').select("*").execute()
    poems_data = PoemService.process_poems_data(poems_resp.data or [])
    return {"success": True, "poems": poems_data}

@router.post("/add_poem")
async def add_poem_post(
    poem_in: PoemCreate,
    db: Client = Depends(get_db),
    admin: dict = Depends(get_admin_user)
):
    if not all([poem_in.title, poem_in.author, poem_in.text]):
        raise HTTPException(status_code=400, detail="Все поля должны быть заполнены.")

    if db.table('poem').select('title').eq('title', poem_in.title).execute().data:
        raise HTTPException(status_code=409, detail=f'Стих с названием "{poem_in.title}" уже существует.')

    try:
        new_poem_data = poem_in.dict()
        response = db.table('poem').insert(new_poem_data).execute()
        
        if not response.data:
             raise HTTPException(status_code=500, detail="Не удалось добавить стих.")

        new_poem = PoemService.process_poem_data(response.data[0])
        return {"success": True, "message": f'Стих "{new_poem["title"]}" успешно добавлен!', "poem": new_poem}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")

@router.post("/edit_poem/{original_title}")
async def edit_poem_post(
    original_title: str,
    poem_in: PoemCreate,
    db: Client = Depends(get_db),
    admin: dict = Depends(get_admin_user)
):
    poem_to_edit = db.table('poem').select('title').eq('title', original_title).execute()
    if not poem_to_edit.data:
        raise HTTPException(status_code=404, detail="Стих для редактирования не найден.")
        
    update_data = poem_in.dict()

    if not all(update_data.values()):
        raise HTTPException(status_code=400, detail="Все поля должны быть заполнены.")
            
    try:
        if update_data['title'] != original_title:
            if db.table('poem').select('title').eq('title', update_data['title']).execute().data:
                raise HTTPException(status_code=409, detail=f'Стих с новым названием "{update_data["title"]}" уже существует.')
        
        response = db.table('poem').update(update_data).eq('title', original_title).execute()
        
        if not response.data:
             raise HTTPException(status_code=500, detail="Не удалось обновить стих.")
        
        updated_poem = PoemService.process_poem_data(response.data[0])
        return {"success": True, "message": f'Стих "{updated_poem["title"]}" успешно обновлен!', "poem": updated_poem}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")

@router.post("/delete_poem/{title}")
async def delete_poem(title: str, db: Client = Depends(get_db), admin: dict = Depends(get_admin_user)):
    poem_to_delete = db.table('poem').select('title').eq('title', title).execute()
    if not poem_to_delete.data:
        raise HTTPException(status_code=404, detail="Стих не найден.")
        
    try:
        db.table('poem').delete().eq('title', title).execute()
        return {"success": True, "message": f"Стих '{title}' успешно удален."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении: {str(e)}")
