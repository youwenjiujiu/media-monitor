import logging
from fastapi import FastAPI, Form, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import DEFAULT_CLIENT
from scraper import scrape_articles
from analyzer import analyze_articles
from report_generator import generate_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Media Monitoring Report Generator")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
def generate(urls: str = Form(...)):
    url_list = [u.strip() for u in urls.strip().splitlines() if u.strip()]

    if not url_list:
        return {"error": "No URLs provided."}

    logger.info(f"Processing {len(url_list)} URLs")

    # Step 1: Scrape
    scraped = scrape_articles(url_list)

    # Step 2: Analyze
    analyzed = analyze_articles(scraped, DEFAULT_CLIENT)

    # Step 3: Generate report
    buffer = generate_report(analyzed, DEFAULT_CLIENT)

    filename = f"{DEFAULT_CLIENT.client_name.replace(' ', '_')}_Media_Report.docx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
