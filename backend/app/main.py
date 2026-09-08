from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from backend.app.db import init_db
from backend.app.routes import cart, checkout, orders, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="NexusQA Mock Backend", lifespan=lifespan)

app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(orders.router)
app.include_router(webhooks.router)


@app.get("/checkout-page", response_class=HTMLResponse)
def checkout_page():
    return """
    <html><body>
        <button id="pay-button"
            onclick="document.getElementById('confirmation').style.display='block'">
            Pay Now
        </button>
        <div id="confirmation" style="display:none">Payment Confirmed</div>
    </body></html>
    """
