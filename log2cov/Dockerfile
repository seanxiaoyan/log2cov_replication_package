# python 3.9 and debian 10
FROM python:3.9-slim-buster

# Set the working directory to /log2cov
WORKDIR /log2cov
COPY ./requirements.txt /log2cov/requirements.txt

# Install requirements
RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN pip install requests

# Set mongodb database tools
COPY ./mongodb-database-tools-debian10-x86_64-100.5.2 /mongodb-database-tools-debian10-x86_64-100.5.2
RUN mv /mongodb-database-tools-debian10-x86_64-100.5.2/bin/* /usr/local/bin && \
    rm -rf /mongodb-database-tools-debian10-x86_64-100.5.2
RUN apt-get update && \
    apt-get install -y krb5-user

# Make port 5000 available to the world outside this container
EXPOSE 5000


    