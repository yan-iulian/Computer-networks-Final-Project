FROM python:3.11-slim

WORKDIR /app

COPY server.py ./server.py
COPY engine.py ./engine.py

RUN mkdir -p programe
COPY programe/program1.txt ./programe/program1.txt
COPY programe/program2.txt ./programe/program2.txt
COPY programe/program3.txt ./programe/program3.txt

EXPOSE 5050

CMD ["python", "-u", "server.py"]
