"API de de ejemplo para manejo de activos financieros"


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import yfinance as yf
import uvicorn

"Este código define una API web simple usando FastAPI"

app = FastAPI() # Se crea una instancia de la aplicación FastAPI. Esta instancia se usa para definir rutas y manejar peticiones HTTP.

# Ruta básica
@app.get("/") # Define una ruta que responde a solicitudes GET en la raíz (/) del servidor.
def read_root(): # Función que se ejecuta cuando se accede a /
    return {"message": "API de precios de acciones"} # Retorna un diccionario convertido automáticamente a JSON para enviarlo como respuesta

# Ruta con parámetro en la URL (path parameter/parámetro de ruta)
@app.get("/stocks/{symbol}") # Define una ruta GET que acepta un parámetro dinámico (symbol) en la URL; ejemplo: /stocks/AAPL
def get_stock(symbol: str): # El parámetro se espera como una cadena (ej. "AAPL", "GOOG").
    return {"symbol": symbol, "price": "120 USD"} # La función devuelve el símbolo que se pidió, junto con un precio fijo (ficticio en este ejemplo).

# Ruta con parámetros de consulta (query parameters/parámetros de consulta)
@app.get("/stocks/") # Define una ruta GET que espera recibir parámetros de consulta en la URL (lo que va después de ?).
def get_stock_by_query(symbol: str, exchange: str = "NYSE"): # El parámetro symbol es obligatorio en la consulta; el parámetro exchange es opcional y tiene un valor por defecto ("NYSE").
"Ejemplo de uso: /stocks/?symbol=TSLA&exchange=NASDAQ"
    return {"symbol": symbol, "exchange": exchange, "price": "120 USD"} # Devuelve un JSON con el símbolo, la bolsa y un precio (también ficticio).


#########################################################################################################################################


# Método HTTP - GET:

# Definición de la ruta:
@app.get("/stocks/{symbol}/price") # Define una ruta HTTP GET tipo: /stocks/AAPL/price?date=2022-05-10
def get_stock_price_on_date(symbol: str, date: str): # Usa un path parameter symbol (ej. "AAPL") y un query parameter date (ej. "2022-05-10").
    """
    Obtiene el precio de la acción en una fecha específica o la fecha hábil más cercana.
    Parámetros:
    - symbol: El símbolo de la acción (ejemplo: AAPL para Apple)
    - date: Fecha en formato YYYY-MM-DD
    
    Retorna:
    - Precio de cierre de la acción en la fecha solicitada o la más cercana disponible.
    """
    try:
        # Convertir la fecha a datetime
        date_obj = datetime.strptime(date, "%Y-%m-%d").date() # Convierte la fecha enviada por el usuario (cadena) en un objeto datetime.date.

        # Descargar los datos de la acción
        stock = yf.Ticker(symbol) # Se usa la librería yfinance para acceder a datos históricos de acciones.
        history = stock.history(start=date_obj - timedelta(days=3), end=date_obj + timedelta(days=3)) # Se descargan 7 días de historial (±3 días desde la fecha solicitada), para encontrar la fecha más cercana si no hay datos exactos.

        if history.empty: # Si no se obtienen datos, se lanza un error 404 (no encontrado).
            raise HTTPException(status_code=404, detail=f"No hay datos disponibles para {symbol} en {date}")

        # Filtrar los datos por la fecha más cercana si no hay datos exactos. Se devuelve un JSON.
        closest_date = min(history.index, key=lambda d: abs(d.date() - date_obj)) # history.index contiene fechas de los datos descargados. Se elige la fecha cuya diferencia con date_obj sea la menor.
        closing_price = history.loc[closest_date]['Close'] # Se accede al precio de cierre ("Close") en la fecha más cercana.
        return {
            "symbol": symbol,
            "requested_date": date,
            "closest_date": closest_date.date().isoformat(),
            "closing_price": round(closing_price, 2)
        }

    except ValueError:
        # Manejar error si el formato de la fecha no es válido
        raise HTTPException(status_code=400, detail="El formato de la fecha debe ser YYYY-MM-DD")
    
    except Exception as e:
        # Manejar cualquier otro error
        raise HTTPException(status_code=500, detail=str(e))

"""
Ejemplo de respuesta en JSON:

{
  "symbol": "MSFT",
  "requested_date": "2023-04-09",
  "closest_date": "2023-04-10",
  "closing_price": 291.6
}

"""
    
#########################################################################################################################################

"""
Comentario sobre Pydantic:

Pydantic es una biblioteca en Python que permite validar datos y gestionar "tipos" (ej: str) de una forma simple y eficiente.

FastAPI utiliza Pydantic para validar automáticamente los datos que reciben los endpoints (que los datos coincidan con los tipos
y estructuras esperados (ej: diccionario) antes de procesarlos).

En FastAPI, los modelos de datos que se utilizan para la validación se definen con "clases" de Pydantic.

Permite tener un control total sobre los datos que recibimos y que enviamos en la API.
"""

# Método HTTP - POST:

# Diccionario para almacenar los portafolios de los usuarios
portfolios_db = {} # Es una estructura en memoria (diccionario de Python) que simula una base de datos. La clave es el user_id y el valor será un diccionario con las acciones y sus ponderaciones (porcentaje del portafolio).

# Modelo de datos Pydantic para el portafolio (para la validación de las entradas de datos que realice el usuario)
class Portfolio(BaseModel):
    stocks: dict[str, float] # portfolio.stocks es un diccionario donde: clave = símbolo de la acción (ej: AAPL), valor = porcentaje del portafolio asignado a esa acción (ej: 40.0)

@app.post("/portfolios/{user_id}") # Define una ruta HTTP POST: /portfolios/{user_id}
def save_portfolio(user_id: str, portfolio: Portfolio): # user_id: parámetro de ruta (por ejemplo, "user123"); portfolio: objeto enviado en el cuerpo de la petición (JSON), validado con el modelo Portfolio.
    """
    Guarda el portafolio de un usuario.

    Parámetros:
    - user_id: ID único del usuario.
    - portfolio: Diccionario con las acciones y sus ponderaciones.

    Retorna:
    Un mensaje de confirmación.
    """
    # Verificamos si el usuario ya tiene un portafolio guardado
    if user_id in portfolios_db:
        raise HTTPException(status_code=400, detail=f"El usuario {user_id} ya tiene un portafolio guardado") # error 400 Bad Request

    # Verificamos que las ponderaciones sumen 100%
    total_weight = sum(portfolio.stocks.values())
    if total_weight != 100:
        raise HTTPException(status_code=400, detail="Las ponderaciones deben sumar 100%") # Si no suman exactamente 100, error 400

    # Guardar el portafolio del usuario
    portfolios_db[user_id] = portfolio.stocks # Si las validaciones pasan, se guarda el portafolio en el diccionario portfolios_db.
    
    return {"message": f"Portafolio guardado para el usuario {user_id}"}

#########################################################################################################################################

# Método HTTP - PUT:

@app.put("/portfolios/{user_id}") # define una ruta HTTP PUT, que se usa para actualizar recursos existentes. {user_id} es un path parameter que representa el identificador del usuario.
def update_portfolio(user_id: str, portfolio: Portfolio): # La función recibe: el ID del usuario, un objeto JSON enviado en el cuerpo de la solicitud, validado con el modelo Portfolio.
    """
    Actualiza el portafolio previamente guardado de un usuario.
    Parámetros:
    - user_id: ID único del usuario.
    - portfolio: Diccionario con las acciones y sus nuevas ponderaciones.

    Retorna:
    Un mensaje de confirmación.
    """
    # Verificamos si el usuario ya tiene un portafolio guardado
    if user_id not in portfolios_db:
        raise HTTPException(status_code=404, detail="Portafolio no encontrado para este usuario")

    # Verificamos que las ponderaciones sumen 100%
    total_weight = sum(portfolio.stocks.values())
    if total_weight != 100:
        raise HTTPException(status_code=400, detail="Las ponderaciones deben sumar 100%")

    # Actualizo el portafolio del usuario
    portfolios_db[user_id] = portfolio.stocks # Sobrescribe el portafolio actual del usuario con el nuevo.
    return {"message": f"Portafolio actualizado para el usuario {user_id}"}

########################################################################################################################################

# Método HTTP - DELETE:

# Definición de la ruta:
@app.delete("/portfolios/{user_id}") # define una ruta HTTP de tipo DELETE, usada para eliminar recursos. {user_id} es un path parameter que identifica al usuario cuyo portafolio se quiere eliminar.
def delete_portfolio(user_id: str): # la función espera que se le pase el ID del usuario como texto.
    """
    Elimina el portafolio de un usuario si existe. Si no existe, devuelve un error.

    Parámetros:
    - user_id: ID único del usuario.

    Retorna:
    Un mensaje de confirmación.
    """
    # Validación:
    if user_id not in portfolios_db: # Antes de intentar eliminar el portafolio, verifica si existe en portfolios_db.
        raise HTTPException(status_code=404, detail="Portafolio no encontrado para este usuario")

    # Eliminación el portafolio del usuario
    del portfolios_db[user_id] # Si pasa la validación, se elimina el portafolio del diccionario portfolios_db usando la palabra clave del.
    
    return {"message": f"Portafolio eliminado para el usuario {user_id}"}