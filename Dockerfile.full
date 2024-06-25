FROM ghcr.io/darpa-askem/askem-julia:8.0.1 AS JULIA_BASE_IMAGE
FROM ghcr.io/darpa-askem/askem-forecast-hub:latest AS FORECAST_HUB_BASE

FROM python:3.10

USER root

# Install custom Julia
ENV JULIA_PATH=/usr/local/julia
ENV JULIA_DEPOT_PATH=/usr/local/julia
ENV JULIA_PROJECT=/home/jupyter/.julia/environments/askem

# Install r-lang and kernel
RUN apt update && \
    apt install -y r-base r-cran-irkernel \
        graphviz libgraphviz-dev \
        libevent-core-2.1-7 libevent-pthreads-2.1-7 \
        lsof && \
    apt clean -y && \
    apt autoclean -y \
    apt autoremove -y

# # Install forecast hub requirements from precompiled image (Rlang)
COPY --chown=1000:1000 --from=FORECAST_HUB_BASE /usr/local/lib/R/site-library/ /usr/local/lib/R/site-library/

RUN apt-get install -y build-essential make gcc g++ git gfortran npm \
        gdal-bin libgdal-dev python3-all-dev libspatialindex-dev && \
    npm install -g typescript
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

COPY --chown=1000:1000 --from=JULIA_BASE_IMAGE /usr/local/julia /usr/local/julia
COPY --chown=1000:1000 --from=JULIA_BASE_IMAGE /Project.toml /Manifest.toml /home/jupyter/.julia/environments/askem/
RUN chmod -R 777 /usr/local/julia/logs
RUN ln -sf /usr/local/julia/bin/julia /usr/local/bin/julia

# Switch to non-root user. It is crucial for security reasons to not run jupyter as root user!
RUN useradd -m jupyter
USER jupyter

# Install PyCIEMSS from GitHub
RUN pip install --no-cache-dir git+https://github.com/ciemss/pyciemss.git@9aa5d8849c630e8d2b208d25464d7b006fcd4d60 --use-pep517


# Install Mira from github, with cache-bust
ADD https://api.github.com/repos/DARPA-ASKEM/askem-beaker/git/refs/heads/main bust-cache.json

RUN git clone https://github.com/indralab/mira.git /home/jupyter/mira && \
    pip install --no-cache-dir /home/jupyter/mira/"[ode,tests,dkg-client,sbml]" && \
    rm -r /home/jupyter/mira

# Install Gilda - Mira Dependency 
RUN pip install gilda==1.2.1

#### START Installs for PySB context
# Install project requirements
USER root
WORKDIR /tmp
RUN wget https://github.com/RuleWorld/bionetgen/releases/download/BioNetGen-2.9.2/BioNetGen-2.9.2-linux.tar.gz && \
    tar -xzf BioNetGen-2.9.2-linux.tar.gz && \
    mv BioNetGen-2.9.2 /usr/local/share/BioNetGen && \
    rm BioNetGen-2.9.2-linux.tar.gz

WORKDIR /opt/stochkit
ENV STOCHKIT_HOME=/opt/stochkit
RUN git clone https://github.com/StochSS/StochKit.git /opt/stochkit
RUN bash ./install.sh
USER jupyter
ENV PATH=$PATH:$STOCHKIT_HOME/bin
RUN pip install --no-cache-dir beaker-pysb
####  END  Installs for PySB context

# Install project requirements
COPY --chown=1000:1000 pyproject.toml README.md hatch_build.py /home/jupyter/askem_beaker/
RUN mkdir -p /home/jupyter/askem_beaker/src/askem_beaker && touch /home/jupyter/askem_beaker/src/askem_beaker/__init__.py
RUN pip install --no-cache-dir --upgrade -e /home/jupyter/askem_beaker

COPY --chown=1000:1000 . /home/jupyter/askem_beaker/

# Installs the askem specific subkernels
RUN pip install --no-cache-dir --upgrade /home/jupyter/askem_beaker

#WORKDIR /askem_beaker
WORKDIR /home/jupyter
RUN unzip /home/jupyter/askem_beaker/resources/chromadb_functions_mira.zip \
    && mv /home/jupyter/chromadb_functions /home/jupyter/chromadb_functions_mira && ls
RUN unzip /home/jupyter/askem_beaker/resources/chromadb_functions_chirho.zip \
    && mv /home/jupyter/chromadb_functions /home/jupyter/chromadb_functions_chirho && ls
RUN unzip /home/jupyter/askem_beaker/resources/chromadb_functions_mimi.zip

# Install Julia kernel (as user jupyter)
RUN /usr/local/julia/bin/julia -e 'using IJulia; IJulia.installkernel("julia"; julia=`/usr/local/julia/bin/julia --threads=4`)'

RUN mkdir /home/jupyter/workspace
WORKDIR /home/jupyter/workspace

CMD ["python", "-m", "beaker_kernel.server.main", "--ip", "0.0.0.0"]
