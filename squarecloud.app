DISPLAY_NAME="LicitaME API"
DESCRIPTION="Plataforma de apoio à participação de MEIs em licitações públicas"
MAIN=api/main.py
MEMORY=512
VERSION=recommended
START=python -m uvicorn api.main:app --host 0.0.0.0 --port 80
