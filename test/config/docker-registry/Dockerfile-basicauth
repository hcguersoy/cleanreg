ARG BASEIMAGE
FROM ${BASEIMAGE}

ENV REGISTRY_AUTH_HTPASSWD_REALM=basic-realm \
    REGISTRY_AUTH_HTPASSWD_PATH=/data/htpasswd
	
#Login: test, PW: secret, required hash algorithm: bcrypt
#see https://docs.docker.com/registry/configuration/#htpasswd
#htpassword generator: http://aspirine.org/htpasswd_en.html
RUN mkdir /data \ 
 && echo 'test:$2y$13$Vq5rKlr5CndIOookav9tWuodY4EPUb..hrHbQbUA1ViRKOJFTWknO' > /data/htpasswd
