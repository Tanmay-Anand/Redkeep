# Redkeep Kali toolbox.
#
# A Kali-based image carrying the VAPT tooling plus the Redkeep Python runner.
# Burp Community is NOT installed here by default (it cannot be automated and is
# used manually); install it in your own session if you want it in-container.
FROM kalilinux/kali-rolling:latest

ENV DEBIAN_FRONTEND=noninteractive

# Core toolchain:
#  - nmap             : network discovery / enumeration
#  - metasploit-fw.   : metasploit framework (auxiliary/scanner modules)
#  - nikto            : web server scanner
#  - python3 / pipx   : the Redkeep runner + schemathesis
#  - nodejs / npm     : newman (authenticated API flows)
#  - default-jre      : OWASP ZAP runtime
#  - zaproxy          : OWASP ZAP (headless daemon mode)
RUN apt-get update && apt-get install -y --no-install-recommends \
        nmap \
        metasploit-framework \
        nikto \
        zaproxy \
        python3 \
        python3-pip \
        python3-venv \
        pipx \
        nodejs \
        npm \
        default-jre-headless \
        curl \
        ca-certificates \
        unzip \
        git \
    && rm -rf /var/lib/apt/lists/*

# nuclei (fast templated scanner) — fetch the released binary.
# The release asset name embeds the version, so resolve the latest tag first;
# no `|| true` here — a broken download must fail the build, not pass silently.
RUN NVER="$(curl -fsSL https://api.github.com/repos/projectdiscovery/nuclei/releases/latest \
        | grep -oE '"tag_name": *"v[^"]+"' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')" \
    && echo "nuclei version: ${NVER}" \
    && curl -fsSL "https://github.com/projectdiscovery/nuclei/releases/download/v${NVER}/nuclei_${NVER}_linux_amd64.zip" \
        -o /tmp/nuclei.zip \
    && unzip -o /tmp/nuclei.zip nuclei -d /usr/local/bin \
    && chmod +x /usr/local/bin/nuclei \
    && rm -f /tmp/nuclei.zip \
    && nuclei -version

# OWASP ZAP ships its launcher at /usr/share/zaproxy/zap.sh; the runner invokes
# it as `zap.sh`, so expose it on PATH.
RUN ln -sf /usr/share/zaproxy/zap.sh /usr/local/bin/zap.sh

# newman for authenticated API flows
RUN npm install -g newman@6 || true

# Python tooling: schemathesis + the Redkeep runner's deps, installed globally.
RUN pip3 install --no-cache-dir --break-system-packages \
        "schemathesis>=3.33,<4" \
        "requests>=2.31" \
        "pyyaml>=6" \
        "jinja2>=3.1" \
        "rich>=13"

# Pre-pull nuclei templates and VERIFY they landed. An empty template dir makes
# nuclei refuse to scan ("no templates provided"), so fail the build loudly
# rather than ship a toolbox that silently finds nothing.
RUN nuclei -update-templates \
    && test -n "$(ls -A /root/nuclei-templates 2>/dev/null)" \
    && echo "nuclei templates: $(find /root/nuclei-templates -name '*.yaml' | wc -l) templates"

# Make the runner callable as `vapt` once the repo is mounted at /redkeep.
ENV PYTHONPATH=/redkeep/runner
RUN printf '#!/bin/sh\nexec python3 -m vapt "$@"\n' > /usr/local/bin/vapt \
    && chmod +x /usr/local/bin/vapt

WORKDIR /redkeep
