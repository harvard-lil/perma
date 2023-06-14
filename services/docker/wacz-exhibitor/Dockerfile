FROM registry.lil.tools/harvardlil/nginx:0.03 as builder

RUN apt-get update && apt-get install -y git
RUN git clone https://github.com/rebeccacremona/wacz-exhibitor.git
RUN cd wacz-exhibitor; git checkout override-element-attr

FROM registry.lil.tools/harvardlil/nginx:0.03

COPY --from=builder /wacz-exhibitor/html/ /usr/share/nginx/html/
COPY ./nginx.conf /etc/nginx/conf.d/nginx.conf
