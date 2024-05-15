from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware
from services.genai import YoutubeProcessor, GeminiProcessor

class Video(BaseModel):
    youtube_link: HttpUrl

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze_videos")
def analyze_video(video: Video):
    processor = YoutubeProcessor()
    
    result = processor.retrieve_text(str(video.youtube_link), verbose=True)

    genai_processor = GeminiProcessor(model_name="gemini-pro", project="enduring-honor-422922-k7")

    summary = genai_processor.generate_document_summary(result, verbose = True)

    return {
        "result": summary
    }