import os
from app.model import MODEL

print("MODEL imported from app.model:", MODEL)
print("MODEL in os.environ:         ", os.environ.get("MODEL"))