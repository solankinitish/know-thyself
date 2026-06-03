from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from app.services.coaching_service import CoachingService

app = FastAPI(title="KnowThyself")

service = CoachingService()

@app.get("/health")
def health():
    return {"status": "ok"}


# User Request class and post request
class UserRequest(BaseModel):
    user_id: str
    track: str

@ app.post("/user")
def register_user(request: UserRequest):
    try:
        service.get_coach(request.user_id, request.track)
        return {"status": "registered", "user_id": request.user_id, "track": request.track}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Chat Request class and post request
class ChatRequest(BaseModel):
    user_id: str
    track: str
    message: str

@app.post("/chat")
def chat(request: ChatRequest):
    try:
        response = service.chat(request.user_id, request.track, request.message)
        return {"response": response}
    except ValueError as e:
        status = 503 if "LLM unavailable" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e))


# Data Request class and post requests
class DataRequest(BaseModel):
    user_id: str
    track: str
    data: dict

@app.post("/data/fitness")
def fitness_data(request: DataRequest):
    try:
        service.log_fitness(request.user_id, request.data)
        return {"status": "logged"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/data/habits")
def habits_data(request: DataRequest):
    try:
        service.log_habits(request.user_id, request.data)
        return {"status": "logged"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/memory/{user_id}/{track}")
def get_memory(user_id: str, track: str):
    try:
        coach = service.get_coach(user_id, track)
        memory = coach.get_memory()
        return {"memory": memory}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/insights/{user_id}/{track}")
def get_insights(user_id: str, track: str):
    try:
        coach = service.get_coach(user_id, track)
        insights = coach.get_insights()
        status = coach.get_status()
        return {"insights": insights, "status": status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
