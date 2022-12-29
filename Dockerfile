# (C) Copyright Banco do Brasil 2022.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM atf.intranet.bb.com.br:5001/python:3.10 AS pre-sgs-container

COPY pip.conf /etc/pip.conf
COPY requirements.txt /tmp/requirements.txt
COPY bundle.crt /etc/ssl/certs/bb.bundle.crt

RUN pip install --no-cache-dir --upgrade --prefix /usr/local pip==22.0.4 setuptools==60.10.0 wheel==0.37.1 && \
    pip install --no-cache-dir -r /tmp/requirements.txt


FROM atf.intranet.bb.com.br:5001/python:3.10

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


# dnsutils=1:9.16.27-1~deb11u1 \

RUN mkdir /csv && \
    apt-get update && \
    apt-get install --no-install-recommends -y vim=2:8.2.2434-3+deb11u1 \
                       supervisor=4.2.2-2 \
                       iputils-ping=3:20210202-1 \
                       telnet=0.17-42 \
                       nginx=1.18.0-6.1+deb11u3 && \
    apt-get clean && \
    chown www-data:www-data /sgs_caminho_critico -R && \
    rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime
COPY nginx.conf /etc/nginx/nginx.conf

WORKDIR /sgs_caminho_critico

CMD ["/usr/bin/supervisord","-c","/etc/supervisord.conf"]
