# Convert Domains and Systems using the opslevel-cli

The opslevel-cli commands and steps below can be used to convert domains into systems, and systems into services.

Notes on converting domains into systems:
* Domain names will be preserved
* Owner will be preserved
* Description will be preserved

Notes on converting Systems into services:
* System names will be preserved
  * Optionally: System names will be prefixed with "SEARCH-"
* Owner will be preserved
* Description will be preserved
* Link to new system (previously domain) will be preserved

# Requirements

* opslevel-cli installed https://github.com/OpsLevel/cli
* jq https://stedolan.github.io/jq/
* yq https://github.com/mikefarah/yq
* Ensure that the domains only have 1 alias defined (the alias should be indicated as locked in the UI)

# Steps and commands

1. Backup systems and domains, replace <date-time> with the current date and time for uniqueness. e.g. systems_20241022-1636.json

```
opslevel list systems -o json > systems_<date-time>.json
opslevel list domains -o json > domains_<date-time>.json
```

2.  Delete systems

```
cat systems_<date-time>.json | jq '.[] | .Id' | xargs -n1 opslevel delete system
```

3. Delete domains

```
cat domains_<date-time>.json | jq '.[] | .Id' | xargs -n1 opslevel delete domain
```

4. Create domains into systems, preserve name, preserve owner, preserve description

```
cat domains_<date-time>.json | jq -c 'map({name: .Name, ownerId: .Owner.OnTeam.id, description: .Description}) | .[]' | while read -r item; do
  echo "$item" | yq eval | opslevel create system
done
```

5. Create systems into services, preserve name, preserve owner, preserve description, preserve link to domain (now a system), output the service ids to a file to use to assign tags and properties

```
cat systems_<date-time>.json| jq -c 'map({name: .Name, owner: {id: .Owner.OnTeam.id}, description: .Description, parent: {alias: .Parent.Aliases[0]}}) | .[]' | while read -r item; do
  echo "$item" | yq eval | opslevel create service
done > service_ids_output.txt
```

Optionally, you can add additional data if needed. For example, adding prefix "SEARCH-" to the name.

```
cat systems_<date-time>.json| jq -c 'map({name: ("SEARCH-" + .Name), owner: {id: .Owner.OnTeam.id}, description: .Description, parent: {alias: .Parent.Aliases[0]}}) | .[]' | while read -r item; do
  echo "$item" | yq eval | opslevel create service
done
```

6. Assign tags to services using the service ids from service_ids_output.txt. In this example, we are assigning the tag "type" with the value "Sub-Feature". 

```
cat service_ids_output.txt | while read -r item; do
if [ -n "$item" ]; then
item=$(echo "$item" | tr -d '"' | xargs)
opslevel create tag --type=Service $item type sub-feature1
fi
done
```

7. You can query back services matching the tag key and value with the opslevel-cli. The example below returns the list of services by name.

```
opslevel list services -o json | jq '.[] | if .tags.Nodes[] | .key=="type" and .value=="sub-feature1" then .name else empty end'
```

8. Assign properties to services using the service ids from service_ids_output.txt. In this example, we are assigning the property "type" with the value "Sub-Feature".

```
cat service_ids_output.txt | while read -r item; do
if [ -n "$item" ]; then
item=$(echo "$item" | tr -d '"' | xargs)
cat << EOF | opslevel assign property -f -
owner:
  id: $item
definition:
  alias: "type"
value: "\"Sub-Feature\""
runValidation: false
EOF
fi
done
```

9. You can query back services matching the property key and value with the opslevel-cli. The example below returns the list of services by name.

```
opslevel list services --properties -o json | jq '.[] | if .Properties.Nodes[] | (.Definition.aliases[0]=="type" and .Value =="\"Sub-Feature\"") then .name else empty end'
```
