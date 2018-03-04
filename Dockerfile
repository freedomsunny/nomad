FROM opsbase:latest
MAINTAINER huangyj
COPY nomad /root/nomad
WORKDIR /root/nomad
RUN yum -y install mysql-connector-python.noarch redis.x86_64 ipmitool.x86_64 \
    && mkdir /etc/ops_nd/ \
#    && cp etc/ops_nd.conf /etc/ops_nd/ \
    && pip install -r requirements.txt \
    && echo -e "redis-server &\n python /root/nomad/bin/ops_nd_api" > /root/start.sh
CMD sh /root/start.sh