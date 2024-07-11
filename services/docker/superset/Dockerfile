FROM apache/superset:latest
USER root

COPY ./superset-init.sh /superset-init.sh

RUN chmod u+x /superset-init.sh
ENTRYPOINT ["/superset-init.sh"]
