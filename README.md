# OSPool Account Report

Creates a report on the inquiries and approvals of accounts for the OSPool.

# Run
Create a .env file at root with COMANAGE_PASSWORD and FRESHDESK_API_TOKEN, and check that the 
values in config.py are correct.

```shell
export $(grep -v '^#' .env | xargs -0)
docker build -t hub.opensciencegrid.org/opensciencegrid/ospool-request-report:latest .
docker run \
  -e FRESHDESK_API_TOKEN=$FRESHDESK_API_TOKEN \
  -t hub.opensciencegrid.org/opensciencegrid/ospool-request-report:latest
```

# Publish ( need credentials )
```shell
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker build -t hub.opensciencegrid.org/opensciencegrid/ospool-request-report:1.0.0 .
docker push hub.opensciencegrid.org/opensciencegrid/ospool-request-report:1.0.0
```

# Manually run on Tiger
```shell
RANDSTRING=$(openssl rand -hex 12)
kubectl create job --from=cronjob/ospool-account-report ospool-request-report-$RANDSTRING
```
