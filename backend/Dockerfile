FROM python:3.12-slim

WORKDIR /code

# Copy and install requirements
COPY ./requirements.txt /code/requirements.txt

# In Docker, we can install psycopg2-binary since compilers/dependencies are handled by python:3.12-slim Linux,
# but we will stick to requirements.txt which is clean and works across both Windows/Linux.
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy application files
COPY ./app /code/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
