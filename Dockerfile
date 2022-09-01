# (C) Copyright Banco do Brasil 2022.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
FROM atf.intranet.bb.com.br:5001/bb/lnx/lnx-python3:3.8.2

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

# exemplo
RUN \
    apk add --quiet --no-cache \
        unzip=6.0-r4

CMD ["/bin/sh"]
