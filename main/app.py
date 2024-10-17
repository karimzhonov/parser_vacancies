import datetime
import io
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from hh_ru.utils import get_hh_locations, get_text
from hh_ru.api import collect_file

app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class PostData(BaseModel):
    text: str
    area: str
    per_page: float
    date_from: str
    date_to: str
    currency: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="home.html", context={"locations": get_hh_locations(), "texts": get_text()}
    )

@app.post("/download")
async def download(data: PostData):
    file = collect_file(data)
    headers = {
        # By adding this, browsers can download this file.
        'Content-Disposition': f'attachment; filename=hh.ru-{datetime.datetime.now()}.xlsx',
        # Needed by our client readers, for CORS (cross origin resource sharing).
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control_Allow-Methods": "POST, GET, OPTIONS",
    }
    media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return StreamingResponse(io.BytesIO(file),
        headers=headers,
        media_type=media_type
    )
