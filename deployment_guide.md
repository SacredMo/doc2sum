
# 文件处理平台部署指南

本指南提供了将文件处理平台部署到不同云平台的详细步骤。

## 目录

1. [准备工作](#准备工作)
2. [Streamlit Cloud部署](#streamlit-cloud部署)
3. [Heroku部署](#heroku部署)
4. [AWS Elastic Beanstalk部署](#aws-elastic-beanstalk部署)
5. [Docker部署](#docker部署)
6. [部署后配置](#部署后配置)
7. [故障排除](#故障排除)

## 准备工作

在部署之前，请确保您已经：

1. 安装了必要的工具：Git、Python 3.8+
2. 获取了OpenAI或Google Gemini的API密钥（可选，也可以在应用中设置）
3. 准备了部署平台的账号（Streamlit Cloud、Heroku、AWS等）

## Streamlit Cloud部署

[Streamlit Cloud](https://streamlit.io/cloud) 是部署Streamlit应用最简单的方式。

### 步骤：

1. 将代码推送到GitHub仓库
2. 登录Streamlit Cloud
3. 点击"New app"按钮
4. 选择您的GitHub仓库、分支和主文件(app.py)
5. 点击"Deploy"

### 环境变量配置：

在Streamlit Cloud的应用设置中，添加以下环境变量：

- `PORT`: 8501
- `DATABASE_URL`: sqlite:///data/users.db

## Heroku部署

### 步骤：

1. 安装[Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. 登录Heroku: `heroku login`
3. 创建Heroku应用: `heroku create your-app-name`
4. 初始化Git仓库（如果尚未初始化）:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   ```
5. 添加Heroku远程仓库: `heroku git:remote -a your-app-name`
6. 推送代码到Heroku: `git push heroku master`

### 环境变量配置：

```
heroku config:set PORT=8501
heroku config:set DATABASE_URL=sqlite:///data/users.db
```

## AWS Elastic Beanstalk部署

### 步骤：

1. 安装[AWS CLI](https://aws.amazon.com/cli/)和[EB CLI](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html)
2. 配置AWS凭证: `aws configure`
3. 初始化EB应用: `eb init -p python-3.8 your-app-name`
4. 创建环境: `eb create your-env-name`
5. 部署应用: `eb deploy`

### 环境变量配置：

在AWS Elastic Beanstalk控制台中，导航到您的环境 -> 配置 -> 软件 -> 环境属性，添加以下键值对：

- `PORT`: 8501
- `DATABASE_URL`: sqlite:///data/users.db

## Docker部署

### 创建Dockerfile：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY . .
RUN pip install -r requirements.txt
RUN chmod +x setup.sh

EXPOSE 8501

CMD ["sh", "setup.sh"]
```

### 构建和运行Docker镜像：

```
docker build -t file-processing-platform .
docker run -p 8501:8501 file-processing-platform
```

## 部署后配置

1. 访问应用URL
2. 使用默认管理员账户登录（用户名: admin, 密码: admin）
3. 立即更改默认密码
4. 配置API密钥

## 故障排除

### 常见问题：

1. **应用无法启动**
   - 检查日志: `heroku logs --tail` 或相应平台的日志查看命令
   - 确认所有依赖都已正确安装

2. **数据库错误**
   - 确保数据目录存在且有写入权限
   - 检查数据库连接字符串是否正确

3. **API调用失败**
   - 验证API密钥是否正确
   - 检查网络连接和防火墙设置

如需更多帮助，请提交issue或联系管理员。
