# 1 
FROM python:3.7

# 2
RUN pip install -r requirements.txt

# 3
COPY app/ /app
WORKDIR /app

# 4
ENV PORT 5000

# 5
CMD exec python run.py