import subprocess
import sys


class ServiceManagerError(Exception):
    pass

def run_command(cmd):
    """
    Runs a system command safely and returns stdout.
    Raises ServiceManagerError on failure.
    """
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise ServiceManagerError(
            f"Command failed: {' '.join(cmd)}\nError: {e.stderr.strip()}"
        )


def service_exists(service_name):
    """
    Checks whether a systemd service exists.
    """
    try:
        run_command(["systemctl", "status", service_name])
        return True
    except ServiceManagerError:
        return False


def restart_service(service_name):
    """
    Restarts a service and validates its final state.
    """
    if not service_exists(service_name):
        raise ServiceManagerError(f"Service '{service_name}' does not exist.")

    run_command(["systemctl", "restart", service_name])

    status = run_command(["systemctl", "is-active", service_name])

    if status != "active":
        raise ServiceManagerError(
            f"Service '{service_name}' restarted but is in '{status}' state."
        )

    return status

def main(service_name = "eamlogs"):
    try:
        status = restart_service(service_name)
        return {"response" : f"Service '{service_name}' restarted successfully. Status: {status}"}

    except ServiceManagerError as e:
        sys.exit(1)
        return {"response" : f"ERROR: {e}"}

