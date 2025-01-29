import requests
import json
import os
from collections import defaultdict

# Replace these with your details
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO_OWNER = os.environ["REPO_OWNER"]
REPO_NAME = os.environ["REPO_NAME"]
OPSLEVEL_URL = "https://upload.opslevel.com/integrations/custom_event/"
OPSLEVEL_ROUTING_ID = os.environ["OPSLEVEL_ROUTING_ID"]

# GitHub API URL for Dependabot alerts
URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/dependabot/alerts"

# Headers for GitHub API and OpsLevel
GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

OPSLEVEL_HEADERS = {
    "content-type": "application/json",
    "X-OpsLevel-Routing-ID": OPSLEVEL_ROUTING_ID,
}

def fetch_dependabot_alerts():
    response = requests.get(URL, headers=GITHUB_HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch alerts: {response.status_code}")
        print(response.json())
        return None
    return response.json()

def organize_alerts_by_severity(alerts):
    # Group alerts by severity
    severity_grouped = defaultdict(lambda: {"open": 0, "closed": 0, "alerts": []})
    for alert in alerts:
        severity = alert['security_advisory']['severity']
        state = alert['state']
        identifiers = [id['value'] for id in alert['security_advisory']['identifiers'] if id['type'] == 'CVE']

        # Increment open or closed alert count
        if state == "open":
            severity_grouped[severity]["open"] += 1
        elif state in {"fixed", "dismissed"}:
            severity_grouped[severity]["closed"] += 1

        # Add alert details
        severity_grouped[severity]["alerts"].append({
            "dependency": alert['dependency']['package']['name'],
            "vulnerability": alert['security_advisory']['summary'],
            "cves": identifiers,
            "state": state,
            "fix": alert.get('fixed_in', 'No fix available'),
        })
    return severity_grouped

def send_to_opslevel(payload):
    """
    Send the JSON payload to OpsLevel custom event integration.
    """
    try:
        response = requests.post(OPSLEVEL_URL, headers=OPSLEVEL_HEADERS, json=payload)
        if response.status_code == 202:
            print("Payload sent successfully to OpsLevel.")
        else:
            print(f"Failed to send payload: {response.status_code}")
            print(response.text)
    except requests.RequestException as e:
        print(f"Error sending data to OpsLevel: {e}")

def save_to_json(data, filename="dependabot_alerts.json"):
    with open(filename, "w") as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Alerts saved to {filename}")


def main():
    # Fetch Dependabot alerts
    alerts = fetch_dependabot_alerts()
    if not alerts:
        print("No alerts to process. Exiting.")
        return

    # Organize alerts by severity
    grouped_alerts = organize_alerts_by_severity(alerts)

    # Prepare the payload
    ol_req_payload = {
        "dependabot_alerts": {
            **grouped_alerts,
            "repository": f"{REPO_NAME}"
        }
    }

    # Send the payload to OpsLevel
    send_to_opslevel(ol_req_payload)
    save_to_json(ol_req_payload)

if __name__ == "__main__":
    main()