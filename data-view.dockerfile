FROM debian:bookworm-slim as builder

# create the appropriate directories
ENV HOME=/code
ENV APP_HOME=$HOME
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/static
WORKDIR $APP_HOME

# set work directory
WORKDIR $HOME

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update\
 && apt-get install -y --no-install-recommends\
 "cron"\
 "python3-dev"\
 "python3-wheel"\
 "python3-setuptools"\
 "python3-virtualenv"\
 "libtool"\
 "python3-pip"\
 "libpq-dev"\
  && apt-get clean\
 && rm -rf /var/lib/apt/lists/*

RUN python3 -m virtualenv /venv
ENV PATH=/venv/bin:$PATH

# install dependencies
RUN pip3 install --upgrade pip

COPY ./data-view/requirements.txt .
RUN pip3 wheel --no-cache-dir --no-deps --wheel-dir $APP_HOME/data-view/wheels -r requirements.txt

# copy project
COPY . $HOME

WORKDIR $HOME


FROM debian:bookworm-slim

# create the appropriate directories
ENV HOME=/code
ENV APP_HOME=$HOME
RUN mkdir $APP_HOME
WORKDIR $APP_HOME
RUN mkdir $APP_HOME/static
RUN mkdir $APP_HOME/media

RUN apt-get update\
 && apt-get install -y --no-install-recommends\
 "cron"\
 "netcat-traditional"\
 "python3-pip"\
 "python3-virtualenv"\
 "screen"\
 "postgresql-client"\
 "mc"\
 "systemd"\
 "libpango-1.0-0"\
 "libpangoft2-1.0-0"\
 "libharfbuzz-subset0"\
 && apt-get clean\
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder $APP_HOME/data-view/wheels /wheels
COPY --from=builder $APP_HOME/data-view/requirements.txt .

COPY ./entrypoint.data-view.sh $HOME

RUN python3 -m virtualenv /venv
ENV PATH=/venv/bin:$PATH

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache /wheels/*

# copy and run cron jobs
# COPY ./data-view/cronjobs /etc/cron.d/
# RUN chmod 0644 /etc/cron.d/cronjobs
# RUN crontab /etc/cron.d/cronjobs

RUN chmod 0777 $HOME/entrypoint.data-view.sh
# RUN chmod 0777 $HOME/data-view/permissions.sh
# run entrypoint.data-view.sh
ENTRYPOINT ["sh", "/code/entrypoint.data-view.sh"]
