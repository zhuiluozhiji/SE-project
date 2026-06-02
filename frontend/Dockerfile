FROM node:20-alpine

WORKDIR /workspace/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm config set registry https://registry.npmmirror.com \
    && npm install

COPY frontend /workspace/frontend
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
