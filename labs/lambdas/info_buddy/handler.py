from mangum import Mangum

from controllers.api import app

# Lambda calls handler(event, context); Mangum turns that event into an ASGI request for FastAPI
handler = Mangum(app, lifespan="off")
