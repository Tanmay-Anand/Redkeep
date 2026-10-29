"""Redkeep VAPT runner.

A thin orchestration layer over Nmap, Metasploit (aux), OWASP ZAP, nuclei,
nikto and schemathesis. Every pass goes through the target allowlist gate in
``vapt.targets`` before any tool is launched, and results are ingested into
DefectDojo via ``vapt.ingest``.
"""

__version__ = "0.1.0"
