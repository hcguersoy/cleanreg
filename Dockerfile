FROM python:2.7-alpine
RUN pip install requests
COPY cleanreg.py /cleanreg.py
ENTRYPOINT ["/cleanreg.py"]
CMD ["-h"]
