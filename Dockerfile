FROM python:alpine3.19
LABEL author="Maksim.A"

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY source/ /app/

WORKDIR /app/

EXPOSE 80

ENTRYPOINT ["python", "__main__.py"]