# api_core.py
import re
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import os

# Configuración desde variables de entorno
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-b548565594984101afa3ba4b478760c7")

class CopyEvaluatorAPI:
    def __init__(self):
        self.ultimo_texto = ""
        self.ultimo_analisis = ""
        self.ultimo_feedback = ""
        self.puntajes = []
        self.comentarios = []
        self.pilares = [
            "Claridad brutal",
            "Tono directo y emocional",
            "Beneficio claro y egoísta",
            "Urgencia y empuje",
            "Llamado a la acción picante",
            "Autenticidad (voz propia)"
        ]

    def extraer_texto_url(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return {
                    "error": f"Error al obtener la página (código {response.status_code})",
                    "status": "error"
                }
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for script in soup(["script", "style", "head", "footer", "nav", "aside"]):
                script.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            if not clean_text:
                return {
                    "error": "La página no contiene texto visible para análisis",
                    "status": "error"
                }
                
            return {
                "texto": clean_text,
                "caracteres": len(clean_text),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "error": f"Error al extraer texto: {str(e)}",
                "status": "error"
            }

    def evaluar_copy(self, texto):
        self.ultimo_texto = texto.strip()

        if not self.ultimo_texto:
            return {
                "error": "Por favor, escribe un texto para evaluar",
                "status": "error"
            }

        # 🔥 DISPARADORES BRUTALES
        comentarios_disparadores = []
        disparadores = [
            {"condicion": lambda t: t.lower().startswith("hola"), "mensaje": "¿Estás vendiendo o saludando? Esto no es WhatsApp."},
            {"condicion": lambda t: len(t.split()) <= 3, "mensaje": "¿Y esto qué coño es? Dale forma o bórralo."},
            {"condicion": lambda t: len(t) == 0, "mensaje": "¿Vas a vender con poder mental o qué?"},
            {"condicion": lambda t: any(x in t.lower() for x in ["quisiera", "me gustaría", "podrías"]), "mensaje": "¡No vengas a pedir permiso! Esto es venta, no una carta de amor."},
            {"condicion": lambda t: any(x in t.lower() for x in ["soluciones", "brindamos", "experiencia única", "fomentamos", "apoyamos"]), "mensaje": "Parece sacado de una consultora que no vende nada. ¿Quién va a leer esto?"}
        ]

        for disparador in disparadores:
            if disparador["condicion"](self.ultimo_texto):
                comentarios_disparadores.append(disparador["mensaje"])

        if comentarios_disparadores:
            return {
                "disparadores": comentarios_disparadores,
                "status": "disparadores",
                "puntajes": [0]*6,
                "comentarios": [""]*6
            }

        # Normalizar texto para análisis
        lower = self.ultimo_texto.lower()
        palabras = self.ultimo_texto.split()

        # Resultados individuales por pilar (0 a 10)
        puntajes = [0]*6
        comentarios = [""]*6

        # -------- 1. Claridad brutal --------
        claridad = 9 if (len(palabras) <= 200 and any(p in lower for p in ["claro", "directo", "al grano", "compra aqui"])) else 7 if len(palabras) <= 300 else 3 if len(palabras) > 400 else 5
        comentarios[0] = "✔️ Tu mensaje es claro y directo. ¡Así se conecta de verdad!" if claridad >= 8 else "🟡 El mensaje es entendible, pero dale más filo y precisión." if claridad >= 5 else "❌ Aquí hay demasiada habladera de huevonadas. Ve al grano sin miedo."
        puntajes[0] = claridad

        # -------- 2. Tono directo y emocional --------
        tono = 8 if any(p in self.ultimo_texto for p in ["tú", "te", "oye", "imagina"]) else 10 if any(p in self.ultimo_texto for p in ["carajo", "puta", "joder"]) else 4
        tono = min(tono, 4) if any(p in self.ultimo_texto for p in ["usted", "estimado", "cliente", "consumidor"]) else tono
        comentarios[1] = "✔️ Hablas como se debe: directo y con emoción auténtica." if tono >= 8 else "🟡 Tono correcto pero podría ser más cercano o con más bolas." if tono >= 5 else "❌ Suena formal o distante. ¡Ponle pasión y saca el palo de tu culo!"
        puntajes[1] = tono

        # -------- 3. Beneficio claro y egoísta --------
        beneficios_claves = ["vas a ganar", "vas a conseguir", "beneficio", "te vas a ahorrar", "para que no", "consigue", "vas a"]
        conteo_benef = sum(lower.count(b) for b in beneficios_claves)
        beneficio = 10 if conteo_benef >= 3 else 7 if conteo_benef == 2 else 5 if conteo_benef == 1 else 3
        comentarios[2] = "✔️ El beneficio está clarísimo y despierta deseo. Excelente." if beneficio >= 8 else "🟡 El beneficio está presente pero puede ser más contundente." if beneficio >= 5 else "❌ Aquí no veo claro qué gana el cliente. No vendas cuentos."
        puntajes[2] = beneficio

        # -------- 4. Urgencia y empuje --------
        palabras_urgencia = ["ahora", "ya", "hoy", "última", "limitado", "no esperes", "oferta especial", "solo hoy"]
        conteo_urg = sum(lower.count(u) for u in palabras_urgencia)
        urgencia = 10 if conteo_urg >= 3 else 7 if conteo_urg == 2 else 5 if conteo_urg == 1 else 3
        comentarios[3] = "✔️ Urgencia sólida que invita a actuar ya mismo." if urgencia >= 8 else "🟡 Algo de urgencia, pero podría apretar más el acelerador." if urgencia >= 5 else "❌ Sin apuro, sin presión. Así no se vende rápido."
        puntajes[3] = urgencia

        # -------- 5. Llamado a la acción picante --------
        ctas_fuertes = ["compra", "llama", "haz clic", "escribe ya", "apúrate", "contacta", "no lo pienses", "descarga"]
        conteo_cta = sum(lower.count(c) for c in ctas_fuertes)
        cta = 10 if conteo_cta >= 3 else 7 if conteo_cta == 2 else 5 if conteo_cta == 1 else 3
        comentarios[4] = "✔️ El llamado a la acción es claro, directo y contundente." if cta >= 8 else "🟡 El CTA está, pero puede ser más tajante o urgente." if cta >= 5 else "❌ ¿Dónde está el llamado a la acción? No vendas sin decir cómo."
        puntajes[4] = cta

        # -------- 6. Autenticidad (voz propia) --------
        frases_ia = ["en conclusión", "en resumen", "es importante destacar", "según estudios", "inteligencia artificial"]
        conteo_ia = sum(lower.count(f) for f in frases_ia)
        si_palabras_callejeras = any(x in lower for x in ["coño", "pana", "compa", "parcero", "puta madre", "joder", "huevón"])
        autenticidad = 3 if conteo_ia > 0 else 10 if si_palabras_callejeras else 7
        comentarios[5] = "✔️ Hablas con tu voz única, nada robótico ni cliché." if autenticidad >= 8 else "🟡 Tienes buena voz, pero falta ese toque personal más fuerte." if autenticidad >= 5 else "❌ Suena a robot o copia barata. Ponte la camiseta."
        puntajes[5] = autenticidad

        # Guardar resultados
        self.puntajes = puntajes
        self.comentarios = comentarios

        # Generar HTML de resultados
        resumen_html = """<div style="font-family: Arial; font-size: 12pt;">"""
        for i, pilar in enumerate(self.pilares):
            score_class = "good" if puntajes[i] >= 8 else "medium" if puntajes[i] >= 5 else "bad"
            resumen_html += f"""
            <div class="section">
                <div class="title">{pilar}</div>
                <div class="score {score_class}">{puntajes[i]}/10</div>
                <div class="comment">{comentarios[i]}</div>
            </div>
            """
        resumen_html += "</div>"

        self.ultimo_analisis = resumen_html

        return {
            "status": "success",
            "analisis": {
                "pilares": self.pilares,
                "puntajes": puntajes,
                "comentarios": comentarios,
                "html": resumen_html
            }
        }

    def obtener_feedback_profundo(self):
        try:
            # Construir el prompt para la API
            prompt = (
                "Eres un experto en copywriting con un estilo directo, ingenioso y brutalmente honesto. "
                "Analiza el siguiente texto usando el método ZEN TAO de Ygor Abreu. El texto es:\n\n"
                f"\"{self.ultimo_texto}\"\n\n"
                "Y estos son los resultados del análisis inicial:\n\n"
                f"{self.ultimo_analisis}\n\n"
                "Da un feedback profundo y personalizado que incluya:\n"
                "1. Críticas específicas de las partes más flojas\n"
                "2. Sugerencias concretas para mejorar\n"
                "3. Ejemplos de reescritura\n"
                "4. Consejos para aumentar la conversión con porcentaje estimado\n"
                "Usa un tono directo, ingenioso (venezolano) y con humor negro."
            )
            
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Eres un experto en copywriting, especializado en marketing directo y ventas. Tu estilo es directo, ingenioso y sin pelos en la lengua."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                return {
                    "error": f"Error en el análisis profundo (código {response.status_code})",
                    "status": "error"
                }
                
            response_data = response.json()
            ai_feedback = response_data['choices'][0]['message']['content']
            self.ultimo_feedback = ai_feedback

            return {
                "status": "success",
                "feedback": ai_feedback
            }
            
        except Exception as e:
            return {
                "error": f"Error al obtener feedback: {str(e)}",
                "status": "error"
            }

    def generar_pdf(self, file_path=None):
        try:
            # Si no se especifica ruta, creamos un archivo temporal
            if not file_path:
                file_path = f"/tmp/Evaluacion_Copy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Estilos personalizados
            estilo_titulo = styles["Heading1"]
            estilo_titulo.alignment = 1  # Centrado
            estilo_titulo.textColor = colors.HexColor("#2c3e50")
            
            estilo_subtitulo = styles["Heading2"]
            estilo_subtitulo.alignment = 1
            estilo_subtitulo.textColor = colors.HexColor("#7f8c8d")
            
            estilo_seccion = styles["Heading3"]
            estilo_seccion.textColor = colors.HexColor("#2980b9")
            
            estilo_normal = styles["BodyText"]
            estilo_normal.fontSize = 10
            estilo_normal.leading = 14
            
            # Cabecera
            elements.append(Paragraph("Evaluador de Copywriting - Método ZEN TAO", estilo_titulo))
            elements.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", estilo_subtitulo))
            elements.append(Spacer(1, 0.4 * inch))

            # Sección 1: Texto analizado
            elements.append(Paragraph("TEXTO ANALIZADO", estilo_seccion))
            texto_mostrar = self.ultimo_texto[:1500] + ("..." if len(self.ultimo_texto) > 1500 else "")
            elements.append(Paragraph(texto_mostrar.replace('\n', '<br/>'), estilo_normal))
            elements.append(Spacer(1, 0.3 * inch))

            # Sección 2: Resultados del análisis
            elements.append(Paragraph("RESULTADOS DEL ANÁLISIS", estilo_seccion))
            
            # Crear tabla con resultados
            data = [["PILAR", "PUNTAJE", "COMENTARIO"]]
            for i, pilar in enumerate(self.pilares):
                data.append([pilar, f"{self.puntajes[i]}/10", self.comentarios[i]])
            
            tabla = Table(data, colWidths=[180, 60, 240])
            estilo_tabla = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3498db")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#e0e0e0")),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ])
            
            # Colorear filas según puntaje
            for i in range(1, len(data)):
                if self.puntajes[i-1] >= 8:
                    estilo_tabla.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#e8f5e9"))
                elif self.puntajes[i-1] >= 5:
                    estilo_tabla.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#fff3e0"))
                else:
                    estilo_tabla.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#ffebee"))
            
            tabla.setStyle(estilo_tabla)
            elements.append(tabla)
            elements.append(Spacer(1, 0.3 * inch))

            # Sección 3: Feedback profundo
            elements.append(Paragraph("FEEDBACK PROFUNDO", estilo_seccion))
            elements.append(Paragraph("La opinión NO solicitada de Ygor:", estilo_normal))
            
            # Dividir feedback en párrafos
            feedback_parrafos = self.ultimo_feedback.split('\n\n')
            for parrafo in feedback_parrafos:
                if parrafo.strip():
                    elements.append(Paragraph(parrafo.strip().replace('\n', '<br/>'), estilo_normal))
                    elements.append(Spacer(1, 0.2 * inch))
            
            # Pie de página
            elements.append(Spacer(1, 0.4 * inch))
            elements.append(Paragraph("Generado con Evaluador de Copywriting - Método ZEN TAO", estilo_normal))
            elements.append(Paragraph("© Estimulante, C.A. - Todos los derechos reservados", estilo_normal))

            # Generar PDF
            doc.build(elements)
            
            return {
                "status": "success",
                "file_path": file_path
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }