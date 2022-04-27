from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from .routes import router as api_router


def get_application() -> FastAPI:
    app = FastAPI(title='jeffastor_tutor', default_response_class=ORJSONResponse)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix='/api')

    return app

app = get_application()
