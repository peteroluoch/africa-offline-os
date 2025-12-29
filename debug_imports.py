import time
print("Importing state...")
from aos.api.state import core_state
print("Importing app...")
from aos.api.app import create_app
print("Importing routers...")
from aos.api.routers.auth import router as auth_router
from aos.api.routers.agri import router as agri_router
print("Success!")
