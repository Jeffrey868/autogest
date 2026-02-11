from fastapi import FastAPI
from database import engine
import models

from routes import auth_routes, veiculo_routes, dashboard_routes, renave_routes

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth_routes.router)
app.include_router(veiculo_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(renave_routes.router)
