FROM python:3.6

# System prerequisites
RUN apt-get update \
 && apt-get -y install build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# If you require additional OS dependencies, install them here:
# RUN apt-get update \
#  && apt-get -y install imagemagick nodejs \
#  && rm -rf /var/lib/apt/lists/*

# Install Gunicorn. If Gunicorn is already present in your requirements.txt,
# you don't need that (but if won't hurt).
# RUN pip install gunicorn

ADD requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt

ADD . /app

# Collect assets. This approach is not fully production-ready, but
# will help you experiment with Enclave before bothering with static
# files.
# Review http://go.aptible.com/assets for production-ready advice.
RUN set -a \
 && . ./.aptible.env \
 &&  python manage.py collectstatic --noinput

EXPOSE 8000
# Environment settings for django configuration
ENV DJANGO_SETTINGS_MODULE=backend.settings
ENV DJANGO_CONFIGURATION=Prod

CMD ["gunicorn", "--access-logfile=-", "--error-logfile=-", "--bind=0.0.0.0:8000", "--workers=3", "backend.wsgi"]