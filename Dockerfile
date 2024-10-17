FROM python:3.9


WORKDIR /code


COPY ./requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


COPY ./main/ /code/


CMD ["fastapi", "run", "main/app.py", "--port", "7000"]