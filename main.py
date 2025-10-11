"API de de ejemplo para manejo de activos financieros"


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import yfinance as yf
import uvicorn


app = FastAPI()

# Ruta básica
@app.get("/") # Define una ruta que responde a solicitudes GET en la raíz (/) de la API.
def read_root(): # Función que se ejecuta cuando se accede a /
    return {"message": "API de precios de acciones"} # Retorna un diccionario convertido automáticamente a JSON

# Parámetro en la ruta
@app.get("/stocks/{symbol}")
def get_stock(symbol: str):
    return {"symbol": symbol, "price": "120 USD"}

# Parámetros de consulta (query)
@app.get("/stocks/")
def get_stock_by_query(symbol: str, exchange: str = "NYSE"):
    return {"symbol": symbol, "exchange": exchange, "price": "120 USD"}


#########################################################################################################################################


# Método HTTP - GET:

@app.get("/stocks/{symbol}/price")
def get_stock_price_on_date(symbol: str, date: str):
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
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

        # Descargar los datos de la acción
        stock = yf.Ticker(symbol)
        history = stock.history(start=date_obj - timedelta(days=3), end=date_obj + timedelta(days=3))

        if history.empty:
            raise HTTPException(status_code=404, detail=f"No hay datos disponibles para {symbol} en {date}")

        # Filtrar los datos por la fecha más cercana si no hay datos exactos
        closest_date = min(history.index, key=lambda d: abs(d.date() - date_obj))
        closing_price = history.loc[closest_date]['Close']

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
    
# Ejemplo de uso
# get_stock_price_on_date("AAPL", "2024-09-18")

#########################################################################################################################################

# Método HTTP - POST:

# Diccionario para almacenar los portafolios de los usuarios
portfolios_db = {}

# Modelo de datos Pydantic para el portafolio
class Portfolio(BaseModel):
    stocks: dict[str, float]

@app.post("/portfolios/{user_id}")
def save_portfolio(user_id: str, portfolio: Portfolio):
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
        raise HTTPException(status_code=400, detail=f"El usuario {user_id} ya tiene un portafolio guardado")

    # Verificamos que las ponderaciones sumen 100%
    total_weight = sum(portfolio.stocks.values())
    if total_weight != 100:
        raise HTTPException(status_code=400, detail="Las ponderaciones deben sumar 100%")

    # Guardar el portafolio del usuario
    portfolios_db[user_id] = portfolio.stocks
    
    return {"message": f"Portafolio guardado para el usuario {user_id}"}

#########################################################################################################################################

# Método HTTP - PUT:

@app.put("/portfolios/{user_id}")
def update_portfolio(user_id: str, portfolio: Portfolio):
    """
    Actualiza el portafolio de un usuario.
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
    portfolios_db[user_id] = portfolio.stocks
    return {"message": f"Portafolio actualizado para el usuario {user_id}"}

########################################################################################################################################

# Método HTTP - DELETE:

@app.delete("/portfolios/{user_id}")
def delete_portfolio(user_id: str):
    """
    Elimina el portafolio de un usuario.

    Parámetros:
    - user_id: ID único del usuario.

    Retorna:
    Un mensaje de confirmación.
    """
    if user_id not in portfolios_db:
        raise HTTPException(status_code=404, detail="Portafolio no encontrado para este usuario")

    # Elimino el portafolio del usuario
    del portfolios_db[user_id]
    
    return {"message": f"Portafolio eliminado para el usuario {user_id}"}