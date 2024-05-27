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

genai_processor = GeminiProcessor(model_name="gemini-pro", project="dynamo-mission-423519", location="us-central1")

@app.post("/analyze_videos")
def analyze_video(video: Video):
    processor = YoutubeProcessor(genai_processor=genai_processor)
    
    result = processor.retrieve_text(str(video.youtube_link), verbose=True)


    #summary = genai_processor.generate_document_summary(result, verbose = True)
    key_concepts = processor.find_key_concepts(result,group_size=10,verbose = True)
    return {
        "key_concepts": key_concepts
    }