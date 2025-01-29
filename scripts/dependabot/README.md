# **Dependabot and OpsLevel Integration**

This project provides a Python script that integrates **Dependabot alerts** with **OpsLevel** to automate the tracking and management of vulnerabilities across your repositories. The script fetches alerts from GitHub using the Dependabot API, processes the data, and sends it to OpsLevel via a custom event integration endpoint. 

With this integration, you can also create **custom checks** in OpsLevel to ensure that critical vulnerabilities are addressed promptly.

---

## **Features**
- [List Dependabot alerts for a repository](https://docs.github.com/en/rest/dependabot/alerts?apiVersion=2022-11-28#list-dependabot-alerts-for-a-repository) using the GitHub API. Update the API request as needed to use
    - [List Dependabot alerts for an enterprise](https://docs.github.com/en/rest/dependabot/alerts?apiVersion=2022-11-28#list-dependabot-alerts-for-an-enterprise)
    - [List Dependabot alerts for an organization](https://docs.github.com/en/rest/dependabot/alerts?apiVersion=2022-11-28#list-dependabot-alerts-for-an-organization)
- Processes the alerts and groups them by severity (e.g., `critical`, `high`, `medium`).
- Sends the processed data to OpsLevel's custom event integration endpoint.
- Supports custom OpsLevel checks to monitor and validate vulnerabilities.

---

## **Prerequisites**
1. **GitHub Personal Access Token**:
   - Required to authenticate with the GitHub API.
   - Token must have the `security_events` scope for accessing Dependabot alerts.

2. **OpsLevel Routing ID**:
   - A unique identifier for the OpsLevel custom event integration endpoint.

3. **Python Environment**:
   - Python `>=3.7` installed.
   - Dependencies installed via `pip` (see [Installation](#installation)).

---

## **Setup**

### **1. Clone the Repository**
```bash
git clone https://github.com/OpsLevel/community-integrations/dependabot.git
cd dependabot-opslevel-integration
```
### **2. Create a Configuration File**

To store your GitHub and OpsLevel credentials securely, create a .env file in the root directory of the project with the following content:
```bash
GITHUB_TOKEN=your_github_personal_access_token
OPSLEVEL_ROUTING_ID=your_opslevel_routing_id
REPO_OWNER=your_repo_owner
REPO_NAME=your_repo_name
```
- **GITHUB_TOKEN**: Your GitHub Personal Access Token with the security_events scope.
- **OPSLEVEL_ROUTING_ID**: The unique routing ID for your OpsLevel custom event integration.
- **REPO_OWNER**: The owner of the repository (organization or username).
- **REPO_NAME**: The name of the repository.

### **3. Install Dependencies**
Install the required Python packages:
```bash
pip install -r requirements.txt
```
### **4. Usage**
Run the Python script to fetch Dependabot alerts and send them to OpsLevel:
```bash
python dependabot_alerts.py
```
### **5. How It Works**
1. **Fetch Dependabot Alerts**:
    - The script queries the GitHub API for Dependabot alerts for the specified repository.

2. **Process Alerts**:
    - Alerts are grouped by severity (critical, high, medium, etc.).
    - Each alert includes details like the dependency, vulnerability description, CVEs, and fix availability.

3. **Send to OpsLevel**:
    - The processed data is sent to OpsLevel's custom event integration endpoint.
    - Example payload:
    ```json
    {
    "dependabot_alerts": {
        "high": {
        "open": 2,
        "alerts": [
            {
            "fix": "No fix available",
            "cves": [
                "CVE-2021-23337"
            ],
            "state": "open",
            "dependency": "lodash",
            "vulnerability": "Command Injection in lodash"
            },
            {
            "fix": "No fix available",
            "cves": [
                "CVE-2021-23337"
            ],
            "state": "open",
            "dependency": "lodash",
            "vulnerability": "Command Injection in lodash"
            }
        ],
        "closed": 0
        },
        "medium": {
        "open": 2,
        "alerts": [
            {
            "fix": "No fix available",
            "cves": [
                "CVE-2020-28500"
            ],
            "state": "open",
            "dependency": "lodash",
            "vulnerability": "Regular Expression Denial of Service (ReDoS) in lodash"
            },
            {
            "fix": "No fix available",
            "cves": [
                "CVE-2020-28500"
            ],
            "state": "open",
            "dependency": "lodash",
            "vulnerability": "Regular Expression Denial of Service (ReDoS) in lodash"
            }
        ],
        "closed": 0
        },
        "critical": {
        "open": 1,
        "alerts": [
            {
            "fix": "No fix available",
            "cves": [
                "CVE-2020-6836"
            ],
            "state": "open",
            "dependency": "hot-formula-parser",
            "vulnerability": "Command Injection in hot-formula-parser"
            }
        ],
        "closed": 0
        },
        "repository": "dependabot-demo"
    }
    }
    ```~
## **6. OpsLevel Custom Event Check Setup**
1. **Log in to OpsLevel**.
2. **Create a Custom Event Check**:
   - Navigate to **Maturity > Rubric > Add Check**.
   - Define a check to query the custom event data for critical vulnerabilities.
3. **Example Check Logic**:
   - Component specifier: `.dependabot_alerts | .repository`.
   - Success condition: `.dependabot_alerts |   select(.repository == $ctx.alias) | .high.open == "0"`
   - Result Message:
   ```bash
    {% if check.passed %}
    ### Check passed
    {% else %}
    ### Check failed
    Service **{{ data.dependabot_alerts.repository }}** has **{{ data.dependabot_alerts.high.open }}** unresolved vulnerabilities.
    {% endif %}
     ```