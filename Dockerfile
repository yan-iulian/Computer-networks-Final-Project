FROM python:3.11-slim

WORKDIR /app

COPY server.py ./server.py
COPY engine.py ./engine.py

RUN mkdir -p programs
COPY programe/program1.txt ./programs/program1.txt
COPY programe/program2.txt ./programs/program2.txt
COPY programe/program3.txt ./programs/program3.txt

EXPOSE 5050

CMD ["python", "server.py"]
