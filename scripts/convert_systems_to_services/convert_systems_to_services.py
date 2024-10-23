import os
import requests
import json
from datetime import datetime

# Constants
OPSLEVEL_API_TOKEN = os.environ["OPSLEVEL_API_TOKEN"]
OPSLEVEL_ENDPOINT = "https://app.opslevel.com/graphql"

OL_DOMAINS_QUERY = """
query get_all_domains($endCursor: String) {
  account {
    domains(after: $endCursor) {
      nodes {
        id
        name
        description
        aliases
        managedAliases
        owner {
          ... on Team {
            id
            name
            alias
          }
        }
        tags {
          nodes {
            id
            key
            value
          }
        }
        childSystems {
          nodes {
            id
            name
            aliases
            managedAliases
          }
        }
        note
      }
      pageInfo {
        endCursor
        hasNextPage
      }
      totalCount
    }
  }
}
"""

OL_SYSTEMS_QUERY = """
query get_all_systems($endCursor: String) {
  account {
    systems(after: $endCursor) {
      nodes {
        id
        name
        description
        aliases
        managedAliases
        owner {
          ... on Team {
            id
            name
            alias
          }
        }
        tags {
          nodes {
            id
            key
            value
          }
        }
        parent {
          id
          name
        }
        childServices {
          nodes {
            id
            name
          }
        }
        childInfrastructureResources {
          nodes {
            id
            name
          }
        }
        note
      }
      pageInfo {
        endCursor
        hasNextPage
      }
    }
  }
}
"""

OL_SYSTEM_MUTATION = """
mutation create_system($alias:String, $description:String, $ownerId: ID, $note:String){
  systemCreate(input:{name:$alias, description:$description, ownerId: $ownerId, note:$note}){
    system{
      id
      name
      aliases
      description
      owner{
        ... on Team{
          id
          name
        }
      }
    }
  }
}
"""

OL_SERVICE_MUTATION = """
mutation service_create($alias: String!, $description: String, $ownerInput: IdentifierInput) {
  serviceCreate(
    input: {name: $alias, description: $description, ownerInput: $ownerInput}
  ) {
    service {
      id
      name
      description
      aliases
      htmlUrl
      owner {
        alias
      }
      tier {
        alias
      }
      tags {
        totalCount
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          key
          value
        }
      }
    }
    errors {
      message
      path
    }
  }
}
"""

OL_SYSTEMS_SERVICE_ASSIGN_MUTATION = """
mutation systemupdate($system: IdentifierInput!, $childServices:[IdentifierInput!]!){
  systemChildAssign(system: $system, childServices: $childServices){
    system{
      id
      name
      aliases
      childServices{
        nodes{
          id
          name
        }
      }
    }
    errors{
      message
      path
    }
  }
}
"""

def opslevel_graphql_query(query, variables=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPSLEVEL_API_TOKEN}",
    }
    data = {"query": query, "variables": variables}
    response = requests.post(OPSLEVEL_ENDPOINT, json=data, headers=headers)
    if response.status_code != 200:
        raise Exception(f"OpsLevel request failed: {response.content.decode()}")
    return response.json()

def save_to_file(filename, data):
    """Save data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def fetch_and_save_systems():
    """Fetch systems using the OL_SYSTEMS_QUERY and save to file."""
    systems_data = []
    end_cursor = None
    has_next_page = True
    
    # Loop to paginate through results
    while has_next_page:
        variables = {"endCursor": end_cursor}
        result = opslevel_graphql_query(OL_SYSTEMS_QUERY, variables)
        systems = result['data']['account']['systems']['nodes']
        systems_data.extend(systems)
        
        # Check if there's more data to fetch
        page_info = result['data']['account']['systems']['pageInfo']
        end_cursor = page_info['endCursor']
        has_next_page = page_info['hasNextPage']
    
    # Save the systems data to a file with the date appended
    date_suffix = datetime.now().strftime('%Y%m%d')
    filename = f"systems_data_{date_suffix}.json"
    save_to_file(filename, systems_data)
    print(f"Systems data saved to {filename}")

def create_service(system):
    """Create service from a system and handle its dependencies."""
    if system.get('owner', ''):
        ownerInput = {"id": system['owner']['id']}
    else:
        ownerInput = None

    # Create the service
    variables = {
        "alias": "SEARCH-" +system['name'],
        "description": system.get('description', ''),
        "ownerInput": ownerInput,
    }
    opslevel_graphql_query(OL_SERVICE_MUTATION, variables)


def convert_systems_to_services():
    """Fetch systems, create services"""
    end_cursor = None
    has_next_page = True
    
    # Loop to fetch systems
    while has_next_page:
        variables = {"endCursor": end_cursor}
        result = opslevel_graphql_query(OL_SYSTEMS_QUERY, variables)
        systems = result['data']['account']['systems']['nodes']
        
        # For each system, create services and dependencies
        for system in systems:
            create_service(system)
        
        # Pagination
        page_info = result['data']['account']['systems']['pageInfo']
        end_cursor = page_info['endCursor']
        has_next_page = page_info['hasNextPage']

def fetch_and_save_domains():
    """Fetch domains using the OL_DOMAINS_QUERY and save to file."""
    domains_data = []
    end_cursor = None
    has_next_page = True

    # Loop to paginate through results
    while has_next_page:
        variables = {"endCursor": end_cursor}
        result = opslevel_graphql_query(OL_DOMAINS_QUERY, variables)
        domains = result['data']['account']['domains']['nodes']
        domains_data.extend(domains)

        # Check if there's more data to fetch
        page_info = result['data']['account']['domains']['pageInfo']
        end_cursor = page_info['endCursor']
        has_next_page = page_info['hasNextPage']

    # Save the domains data to a file with the date appended
    date_suffix = datetime.now().strftime('%Y%m%d')
    filename = f"domains_data_{date_suffix}.json"
    save_to_file(filename, domains_data)
    print(f"Domains data saved to {filename}")

# New function to convert domains to systems
def convert_domain_to_system(domain):
    """Convert a domain to a system using the OL_SYSTEM_MUTATION."""
    if domain.get('owner', ''):
        owner_id = domain['owner']['id']
    else:
        owner_id = None

    variables = {
        "alias": domain['name'],
        "description": domain.get('description', ''),
        "ownerId": owner_id,
        "note": domain.get('note', '')
    }

    result = opslevel_graphql_query(OL_SYSTEM_MUTATION, variables)
    print("RESULT,", result)
    system_id = result['data']['systemCreate']['system']['id']
    print(f"Domain {domain['name']} converted to system with ID {system_id}")

def convert_domains_to_systems():
    """Fetch domains and convert them to systems."""
    end_cursor = None
    has_next_page = True

    # Loop to fetch domains
    while has_next_page:
        variables = {"endCursor": end_cursor}
        result = opslevel_graphql_query(OL_DOMAINS_QUERY, variables)
        domains = result['data']['account']['domains']['nodes']

        # Convert each domain to a system
        for domain in domains:
            convert_domain_to_system(domain)

        # Pagination
        page_info = result['data']['account']['domains']['pageInfo']
        end_cursor = page_info['endCursor']
        has_next_page = page_info['hasNextPage']

def update_systems_with_services():
    domains_data_file = input("Please enter the path to the domains_data.json file: ")
    
    try:
        domains_data = load_domains_from_file(domains_data_file)
    except FileNotFoundError:
        print(f"File {domains_data_file} not found. Please try again.")
        return
    
    """Fetch systems, compare to domains backup data, assign services to systems."""
    end_cursor = None
    has_next_page = True
    
    # Loop to fetch systems
    while has_next_page:
        variables = {"endCursor": end_cursor}
        result = opslevel_graphql_query(OL_SYSTEMS_QUERY, variables)
        systems = result['data']['account']['systems']['nodes']
        
        # For each system, create services and dependencies
        for system in systems:
            update_system_with_service(system)
        
        # Pagination
        page_info = result['data']['account']['systems']['pageInfo']
        end_cursor = page_info['endCursor']
        has_next_page = page_info['hasNextPage']
    

# Main function
def main():
    """Main function to handle user choice."""
    print("Select an option:")
    print("1. Fetch systems and write to a file.")
    print("2. Convert systems to services.")
    print("3. Fetch domains and write to a file.")
    print("4. Convert domains to systems.")
    choice = input("Enter your choice (1/2/3/4): ")

    if choice == '1':
        fetch_and_save_systems()
    elif choice == '2':
        convert_systems_to_services()
    elif choice == '3':
        fetch_and_save_domains()
    elif choice == '4':
        convert_domains_to_systems()
    elif choice == '5':
        update_systems_with_services()
    else:
        print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    main()
