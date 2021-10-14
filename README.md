# verkeersvergunningen
A proxy-api which exposes vergunningen by querying the decos api. The focus for now is exposing "zwaar verkeer" permits 
to the Cleopatra system, but this may change in the future to also include exposing more permits to other third parties.

### Getting started
1. Make a new virtualenv
2. Install requirements: `make install`
3. Run tests: `make test`

### Development
We follow the [general Django project structure](https://github.com/Amsterdam/opdrachten_team_dev/tree/master/project_architecture)
and [our common dependency management](https://github.com/Amsterdam/opdrachten_team_dev/tree/master/dependency_management)

- Upgrade dependencies: run `make upgrade` in the virtualenv
- Run local dev version: `make dev`
- To expose ports locally, copy docker-compose.override.yml.example to docker-compose.override.yml

### Decos Join
Decos Join has a rather "challenging" API. Some things to note about the api:

- Field names are things such as `text17`, `date6`, etc. A mapping of these in constants can be found 
  in src/zwaarverkeer/decos_join.py
- To get details about the permits, a header should be supplied being `accept-header:application/itemdata`
- Authentication is done through BasicAuth.
- The endpoint can only be queried from our infrastructure. So to fiddle around with the API, ssh into 
  the secure acceptance environment and use curl from there. An example can be found below.

For easy copy pasting, here's an example of how to query the Decos Join endpoint using curl:

    curl -u '<USER>:<KEY>' -H "accept:application/itemdata" "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/8A02814D73B3421B9C65262A45A43BD8/FOLDERS?filter=TEXT48%20has%20'XXXXXX'%20and%20DFUNCTION%20eq%20'Verleend'%20and%20PROCESSED%20eq%20'J'"
