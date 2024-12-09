FROM public.ecr.aws/lambda/python:3.7

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}
    
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy function code
COPY index.py ${LAMBDA_TASK_ROOT}
COPY data_processing.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD ["index.handler"]