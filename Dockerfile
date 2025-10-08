# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY sysinfo.py .
RUN useradd -m app && mkdir -p /output && chown -R app:app /output
USER app
VOLUME ["/output"]
ENTRYPOINT ["python","/app/sysinfo.py","--outdir","/output"]

