FROM public.ecr.aws/lambda/python:3.7

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install PostgreSQL development libraries and other dependencies
RUN yum -y update && \
    yum install -y \
    gcc \
    postgresql-devel \
    libpq \
    libpq-devel \
    python3-devel && \
    yum clean all
    
RUN pip install --upgrade pip
RUN python -m pip install psycopg2-binary>=2.9.1
RUN pip install -r requirements.txt

ADD .aws ${LAMBDA_TASK_ROOT}

# Copy function code
COPY index.py ${LAMBDA_TASK_ROOT}
COPY data_processing.py ${LAMBDA_TASK_ROOT}
COPY models.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD ["index.handler"]