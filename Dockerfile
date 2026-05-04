
# 1. Build React frontend

FROM node:18 AS frontend-build

WORKDIR /app/react-app

COPY react-app/package*.json ./
RUN npm install

COPY react-app/ .
RUN npm run build



# 2. Python backend

FROM python:3.11

WORKDIR /app

# Upgrade pip (good practice)
RUN pip install --upgrade pip

# Copy entire project
COPY . .

# Allow YAML
COPY src/data_science_crew /app/data_science_crew

# Install Python dependencies from pyproject.toml (PEP 621 / setuptools)
RUN pip install .


# Bring React build into backend
COPY --from=frontend-build /app/react-app/build ./build

# Render requires 0.0.0.0 and port 10000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "10000"]