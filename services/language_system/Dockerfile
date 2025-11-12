FROM 695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services:base-latest

# Service-specific CMD
CMD ["python", "-m", "uvicorn", "language_system.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
