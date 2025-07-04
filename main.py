from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from api_core import CopyEvaluatorAPI
import os
import uvicorn

app = FastAPI()
evaluator = CopyEvaluatorAPI()

# Configuración CORS - Permite tu dominio WordPress y localhost
origins = [
    "http://localhost",
    "https://estimulante.online",
    "https://www.estimulante.online",
    "https://evaluador-copy-api.onrender.com"  # Tu dominio de API
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para validación
class EvaluarRequest(BaseModel):
    texto: str = ""
    url: str = ""

class FeedbackRequest(BaseModel):
    texto: str

# Endpoint para evaluación
@app.post("/evaluar")
async def evaluar_endpoint(request: EvaluarRequest):
    # Manejar URL si se proporciona
    if request.url:
        resultado = evaluator.extraer_texto_url(request.url)
        if resultado["status"] == "error":
            raise HTTPException(status_code=400, detail=resultado["error"])
        texto = resultado["texto"]
    else:
        texto = request.texto
    
    # Evaluar el texto
    resultado = evaluator.evaluar_copy(texto)
    
    if resultado["status"] == "error":
        raise HTTPException(status_code=400, detail=resultado["error"])
    elif resultado["status"] == "disparadores":
        return resultado
    
    return {
        "status": "success",
        "analisis": resultado["analisis"]
    }

# Endpoint para feedback profundo
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

# Endpoint de prueba GET
@app.get("/test")
def test_endpoint():
    return {"status": "success", "message": "API funcionando"}

# Endpoint raíz
@app.get("/")
def home():
    return {"message": "Bienvenido a la API de Evaluación de Copywriting"}

# Solo para ejecución local
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
# Este bloque es necesario para Render
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="216.24.60.0/24", port=port)
