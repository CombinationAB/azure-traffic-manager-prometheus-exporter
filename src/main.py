import os, sys
import json
import logging
from azure_tm_exporter import run_exporter

def main():
    name = os.environ.get("AZ_TRAFFICMANAGER_NAME")
    if len(sys.argv) > 1:
        name = sys.argv[1]
    if not name:
        raise ValueError("Traffic manager name is not specified (either use command line or set AZ_TRAFFICMANAGER_NAME)")
    name = name.strip().lower()
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    if not hasattr(logging, log_level):
        raise ValueError(f"Invalid log level {log_level}")
    log_level = getattr(logging, log_level)

    azure_config_file = os.environ.get("AZ_CONFIG_FILE", "/azure.json")
    if not os.path.isfile(azure_config_file):
        raise IOError(f"Azure config file ({azure_config_file}) not found")
    azure_config = json.load(open(azure_config_file))
    az_user = azure_config.get("aadClientId")
    if not az_user:
        raise ValueError("This Azure config file lacks the service principal user (aadClientId)")
    az_secret = azure_config.get("aadClientSecret")
    if not az_secret:
        raise ValueError("This Azure config file lacks the service principal secret (aadClientSecret)")
    az_tenant = azure_config.get("tenantId")
    if not az_tenant:
        raise ValueError("This Azure config file lacks the service principal secret (tenantId)")
    logging.basicConfig()
    logging.getLogger().setLevel(log_level)
    logging.getLogger("azure").setLevel(log_level)
    logging.getLogger("msrest").setLevel(log_level)
    logging.getLogger("urllib3").setLevel(log_level)
    logging.getLogger("adal-python").setLevel(log_level)
    if log_level >= logging.INFO:
        logging.getLogger("cli.azure.cli.core._session").setLevel(logging.WARN)
    run_exporter(name, az_user, az_secret, az_tenant)
    
if __name__ == '__main__':
    main()