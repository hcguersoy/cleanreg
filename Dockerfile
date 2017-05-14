FROM python:2.7-alpine
RUN pip install requests
COPY cleanreg.py /cleanreg.py
COPY LICENSE /LICENSE
RUN /cleanreg.py -h
ENTRYPOINT ["/cleanreg.py"]
CMD ["-h"]
