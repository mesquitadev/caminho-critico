# (C) Copyright Banco do Brasil 2022.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM docker.binarios.intranet.bb.com.br/python:3.11 AS pre-sgs-container

COPY pip.conf /etc/pip.conf
COPY requirements.txt /tmp/requirements.txt
COPY bundle.crt /etc/ssl/certs/bb.bundle.crt
COPY skip-ssl-check /etc/apt/apt.conf.d/skip-ssl-check

RUN apt-get update && \
    pip install --no-cache-dir --upgrade --prefix /usr/local pip==22.0.4 setuptools==60.10.0 wheel==0.37.1 && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm -rf /var/lib/apt/lists/*

FROM pre-sgs-container as pythonBuilder
# hadolint ignore=DL3033,DL3018,DL3059,DL3013
RUN pip3 --no-cache-dir install "fastapi[all]"==0.94.1
# hadolint ignore=DL3033,DL3018,DL3059,DL3013
RUN pip3 --no-cache-dir install cx_Oracle==8.3.0
# hadolint ignore=DL3033,DL3018,DL3059,DL3013
RUN pip3 --no-cache-dir install SQLAlchemy==2.0.15
# hadolint ignore=DL3033,DL3018,DL3059,DL3013
RUN pip3 --no-cache-dir install uvicorn==0.22.0
# hadolint ignore=DL3033,DL3018,DL3059,DL3013
RUN pip3 --no-cache-dir install appdynamics==23.8.0.6197
# hadolint ignore=DL3033,DL3018,DL3059,DL3013
RUN python3 setup.py sdist
# hadolint ignore=DL3033,DL3018,DL3059,DL3013
RUN rm -rf dist/*.whl
# hadolint ignore=DL3033,DL3018,DL3059,DL3013
RUN pip3 install --no-cache-dir dist/sgs_caminho_critico*

FROM docker.binarios.intranet.bb.com.br/python:3.11
ARG build_date
ARG vcs_ref
ARG versao
ARG BOM_PATH="/docker/sgs"

LABEL \
    br.com.bb.image.app.sigla="sgs" \
    br.com.bb.image.app.provider="" \
    br.com.bb.image.app.arch="x86_64" \
    br.com.bb.image.app.maintainer="Banco do Brasil S.A. / DITEC <ditec@bb.com.br>" \
    br.com.bb.image.app.version="$versao" \
    br.com.bb.image.description="" \
    org.label-schema.maintainer="Banco do Brasil S.A. / DITEC <ditec@bb.com.br>" \
    org.label-schema.vendor="Banco do Brasil" \
    org.label-schema.url="https://fontes.intranet.bb.com.br/sgs/sgs-caminho-critico/sgs-caminho-critico" \
    org.label-schema.name="" \
    org.label-schema.license="COPYRIGHT" \
    org.label-schema.version="$versao" \
    org.label-schema.vcs-url="https://fontes.intranet.bb.com.br/sgs/sgs-caminho-critico/sgs-caminho-critico" \
    org.label-schema.vcs-ref="$vcs_ref" \
    org.label-schema.build-date="$build_date" \
    org.label-schema.schema-version="1.0" \
    org.label-schema.dockerfile="${BOM_PATH}/Dockerfile"

# Save Bill of Materials to image. Não remova!
# COPY README.md CHANGELOG.md LICENSE Dockerfile ${BOM_PATH}/

ENV \
    VERSAO=$versao

COPY sgs_caminho_critico /sgs_caminho_critico
COPY --from=pre-sgs-container /usr/local/bin /usr/local/bin
COPY --from=pre-sgs-container /usr/local/lib /usr/local/lib
COPY sources.list /etc/apt/sources.list
COPY skip-ssl-check /etc/apt/apt.conf.d/skip-ssl-check
COPY supervisord.conf /etc/supervisord.conf

#  nginx=1.18.0-6.1+deb11u3 && \ apt-get clean && \ chown www-data:www-data /sgs_caminho_critico -R && \
RUN mkdir /csv && \
    apt-get update && \
    rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime

# COPY nginx.conf /etc/nginx/nginx.conf

WORKDIR /sgs_caminho_critico

CMD ["uvicorn", "--host", "0.0.0.0", "app.run:app"]

# CMD ["/usr/bin/supervisord","-c","/etc/supervisord.conf"]

