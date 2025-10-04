# 🌦️ Campeche Weather API

**Campeche Weather API** es un proyecto en **FastAPI** que permite consultar, comparar y clasificar condiciones climáticas basadas en **probabilidades históricas**.  
No realiza pronósticos deterministas, sino análisis de probabilidad histórica para categorías como *very hot/cold*, *very windy*, *very wet*, y *very uncomfortable*.

---

## Instalación 
Se debera instalar los requerimientos del mismo proyecto en un entorno vitual de python (requirements.txt) En caso de Windows debera instarlos manualmente, en caso de usar linux, podra ejecutarlos en sricpts, recuerda darle permiso a los dos para ejecutar cambios

## Estructura
La estructura se base en donde los routers tenemos los EndPoinst de la Api 
# Services 
seria donde tendriamos la manera de extraer los datos o el modelo de estadistica para calcular la estimación en base de estadistica 


## Deploy
Para el deply de la api deben realizar la instalacion de las dependencias de la API y realizar el comando para prederlo
# Opción manual
 - source .venv/bin/activate
- uvicorn app.main:app --reload --port 8000 <--- comando para ejecutar la api

