FROM apache/superset:latest
USER root

ENV ADMIN_USERNAME $ADMIN_USERNAME
ENV ADMIN_EMAIL $ADMIN_EMAIL
ENV ADMIN_PASSWORD $ADMIN_PASSWORD

COPY ./superset-init.sh /superset-init.sh

RUN chmod u+x /superset-init.sh
ENTRYPOINT ["/superset-init.sh"]
