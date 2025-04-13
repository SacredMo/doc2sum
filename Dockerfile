
FROM python:3.9-slim

WORKDIR /app

COPY . .
RUN pip install -r requirements.txt
RUN chmod +x setup.sh

# 初始化数据库
RUN python db_setup.py

EXPOSE 8501

CMD ["sh", "setup.sh"]
