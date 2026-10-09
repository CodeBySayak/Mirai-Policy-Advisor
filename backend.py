from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import ChatRequest, ChatResponse, IngestResponse, SourceCitation
from rag_pipeline import rag_pipeline
import tempfile
import os

app = FastAPI(title="MirAI Policy Advisor API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Save uploaded file to temp file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            tmp.write(content)
            tmp_path = tmp.name

        page_count, chunk_count = rag_pipeline.ingest_pdf(tmp_path)
        
        # Cleanup
        os.remove(tmp_path)
        
        return IngestResponse(
            status="success",
            page_count=page_count,
            chunk_count=chunk_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty.")
            
        answer, sources_data = rag_pipeline.chat(request.question)
        
        sources = [SourceCitation(page=s["page"], content=s["content"]) for s in sources_data]
        
        return ChatResponse(answer=answer, sources=sources)
    except HTTPException:
        raise
    except ValueError as e:
        return ChatResponse(answer=str(e), sources=[], error=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}
