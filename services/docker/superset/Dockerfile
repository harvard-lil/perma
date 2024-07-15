FROM apache/superset:latest
USER root

ENV ADMIN_USERNAME $ADMIN_USERNAME
ENV ADMIN_EMAIL $ADMIN_EMAIL
ENV ADMIN_PASSWORD $ADMIN_PASSWORD
ENV DATABASE_NAME $DATABASE_NAME
ENV SQLALCHEMY_URI $SQLALCHEMY_URI

COPY ./superset-init.sh /superset-init.sh
COPY superset_config.py /app/
ENV SUPERSET_CONFIG_PATH /app/superset_config.py
# copy the file with timestamp removed so import-dashboards command in superset-init.sh can locate it
COPY dashboard_export*.zip /app/dashboard_export.zip

RUN chmod u+x /superset-init.sh
ENTRYPOINT ["/superset-init.sh"]
