from fastapi import Request, APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import (
    AsyncSession)
from sqlalchemy.future import select
from sqlalchemy import delete
# custom imports 
from rest_schema import Task, DeleteTask, UpdateTask
from .model import User,UserTasks
from utility import * 


task_router = APIRouter() 

@task_router.get("/")
async def task_test(dbs=Depends(get_db)):
    all_tasks = await dbs.execute(select(UserTasks))
    tasks = all_tasks.scalars().all()
    return {"Test":tasks}


@task_router.post("/")
async def create_task(request: Request, task: Task, dbs: AsyncSession = Depends(get_db)):
    """Add a new user task"""

    # Ensure user_id exists (For now, assuming user_id = 1 exists)
    existing_user = await dbs.execute(select(User).where(User.id == 1))
    user = existing_user.scalar()

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    # Create the task with a valid user_id
    task_data = {**task.model_dump(), "user_id": user.id}
    
    new_task = UserTasks(**task_data)
    dbs.add(new_task)
    await dbs.commit()
    await dbs.refresh(new_task)

    return {"message": "Task created successfully", "task": new_task}



@task_router.delete("/")
async def remove_task(task:DeleteTask,dbs:AsyncSession=Depends(get_db)):
    
    result = await dbs.execute(select(UserTasks).filter(UserTasks.task_id == task.task_id))

    task = result.scalar_one_or_none() 

    if not task:
        raise HTTPException(status_code=402,detail="Task not exists")

    await dbs.execute(delete(UserTasks).where(UserTasks.task_id == task.task_id))
    await dbs.commit()
    return {
        "message":"Task Deleted!"
    }



@task_router.post("/modify")
async def update_task(task:UpdateTask,dbs:AsyncSession=Depends(get_db)):
    
    task_id = task.task_id 

    result = await dbs.execute(select(UserTasks).where(UserTasks.task_id == task_id))

    prevtask = result.scalar_one_or_none() 

    if not prevtask:
        raise HTTPException(status_code=404,detail="Task not exists")

    # Update fields only if they are provided
    update_data = task.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prevtask, key, value)

    # Commit the changes
    await dbs.commit()
    await dbs.refresh(prevtask)  # Refresh instance with updated data

    return prevtask
@task_router.options("/")
async def preflight_tasks():
    """Handles preflight requests for PATCH and other methods."""
    headers = {
        "Access-Control-Allow-Origin": "*",  # Adjust for security
        "Access-Control-Allow-Methods": "GET, POST, PATCH, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(content={"message": "Preflight request allowed"}, headers=headers)
