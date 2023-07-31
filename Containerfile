FROM python:3.11-bookworm

ADD dist/*.whl /tmp/

# install genomephone server, bcftools
RUN pip install /tmp/*.whl \
    && rm -rf /tmp/*.whl \
    && curl -s https://api.github.com/repos/samtools/bcftools/releases/latest | grep browser_download_url | grep '.tar.bz2' | head -n 1 | cut -d '"' -f 4 | wget -qi - \
    && mv bcftools*.tar.bz2 bcftools.tar.bz2 \
    && tar -xjf bcftools.tar.bz2 \
    && cd bcftools* \
    && mkdir -p /opt/bcftools \
    && ./configure --prefix="/opt/bcftools" \
    && make \
    && make install \
    && cd .. \
    && rm -rf bcftools.tar.bz2

CMD 