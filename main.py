from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from api_core import CopyEvaluatorAPI
import os

app = FastAPI()
evaluator = CopyEvaluatorAPI()

# Configurar CORS - Permite todos los orígenes temporalmente
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EvaluarRequest(BaseModel):
    texto: str = ""
    url: str = ""

class FeedbackRequest(BaseModel):
    texto: str

@app.post("/evaluar")
async def evaluar_endpoint(request: EvaluarRequest):
    if request.url:
        resultado_extraccion = evaluator.extraer_texto_url(request.url)
        if resultado_extraccion["status"] == "error":
            raise HTTPException(status_code=400, detail=resultado_extraccion["error"])
        texto = resultado_extraccion["texto"]
    else:
        texto = request.texto
    
    resultado = evaluator.evaluar_copy(texto)
    
    if resultado["status"] == "error":
        raise HTTPException(status_code=400, detail=resultado["error"])
    elif resultado["status"] == "disparadores":
        return {
            "status": "disparadores",
            "disparadores": resultado["disparadores"]
        }
    
    return {
        "status": "success",
        "analisis": resultado["analisis"]
    }

@app.post("/feedback")
async def feedback_endpoint(request: FeedbackRequest):
    evaluator.ultimo_texto = request.texto
    resultado = evaluator.obtener_feedback_profundo()
    
    if resultado["status"] == "error":
        raise HTTPException(status_code=500, detail=resultado["error"])
    
    return {
        "status": "success",
        "feedback": resultado["feedback"]
    }

# Añade un endpoint de prueba
@app.get("/")
def read_root():
    return {"status": "success", "message": "API funcionando"}
@app.get("/test")
def test_endpoint():
    return {"status": "success", "message": "API funcionando"}
# Este bloque es necesario para Render
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="216.24.60.0/24", port=port)