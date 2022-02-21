FROM python:3.10.2-alpine3.15
RUN python -m pip install --upgrade pip
RUN pip install requests PyYAML
COPY cleanreg.py /cleanreg.py
COPY LICENSE /LICENSE
ENTRYPOINT ["/cleanreg.py"]
CMD ["-h"]
