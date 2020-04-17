from troposphere import Base64, Ref, Template
from troposphere.elasticloadbalancingv2 import Action, Condition, ListenerRule, Matcher, TargetGroup
from troposphere.ecs import Environment, TaskDefinition, Service, ContainerDefinition, PortMapping, LoadBalancer

template = Template(
    "traefikingress"
)

vpc_id = "vpc-0e2786487ff4f2ef4"
region = "eu-west-1"

traefik_config = """
defaultEntryPoints = ["http"]
[entryPoints]
  [entryPoints.http]
  address = ":80"
[ping]
entryPoint = "http"
"""

traefik_entry_point = ["sh", "-c"]
traefik_command = ["mkdir /etc/traefik && echo $TRAEFIK_CONFIG | base64 -d > /etc/traefik/traefik.toml && /entrypoint.sh traefik"]

test_target_group = TargetGroup(
    "targetgroup",
    Name="public-ingress",
    Port=80,
    HealthCheckPath="/ping",
    HealthCheckIntervalSeconds=5,
    HealthCheckProtocol="HTTP",
    HealthCheckTimeoutSeconds=2,
    HealthyThresholdCount=5,
    Protocol="HTTP",
    TargetType="instance",
    VpcId=vpc_id,
    Matcher=Matcher(
        HttpCode="200-299"
    )
)
template.add_resource(test_target_group)

listener_rule = ListenerRule(
    "listenerrule",
    Actions=[
        Action(
            TargetGroupArn=Ref(test_target_group),
            Type='forward'
        )
    ],
    Conditions=[
        Condition(
            Field="path-pattern",
            Values=[
                "/"
            ]
        )
    ],
    Priority=1,
    ListenerArn="arn:aws:elasticloadbalancing:eu-west-1:837380460554:listener/app/live-euwes-14F0KA84VQMOV/95ccdb141691f73e/01a71f7b4d1f6a1d"
)

template.add_resource(listener_rule)

test_task_definition = TaskDefinition(
    "taskdefinition",
    ContainerDefinitions=[
        ContainerDefinition(
            DockerLabels={},
            Command=traefik_command,
            EntryPoint=["sh", "-c"],
            Environment=[
                Environment(
                    Name="TRAEFIK_CONFIG",
                    Value=Base64(traefik_config)
                )
            ],
            Image="traefik:maroilles-alpine",
            Name="traefik",
            MemoryReservation=64,
            PortMappings=[
                PortMapping(
                    "httpportmapping",
                    ContainerPort=80,
                    Protocol="tcp"
                )
            ]
        )
    ]
)

template.add_resource(test_task_definition)

service = Service(
    "service",
    Cluster="live",
    DesiredCount=1,
    LaunchType="EC2",
    LoadBalancers=[
        LoadBalancer(
            "serviceloadbalancer",
            ContainerName="traefik",
            ContainerPort=80,
            TargetGroupArn=Ref(test_target_group)
        )
    ],
    SchedulingStrategy="REPLICA",
    ServiceName="traefik",
    TaskDefinition=Ref(test_task_definition)
)

template.add_resource(service)

print(template.to_yaml())

# {
#   "Type" : "AWS::ECS::TaskDefinition",
#   "Properties" : {
#       "ContainerDefinitions" : [ ContainerDefinition, ... ],
#       "Cpu" : String,
#       "ExecutionRoleArn" : String,
#       "Family" : String,
#       "InferenceAccelerators" : [ InferenceAccelerator, ... ],
#       "IpcMode" : String,
#       "Memory" : String,
#       "NetworkMode" : String,
#       "PidMode" : String,
#       "PlacementConstraints" : [ TaskDefinitionPlacementConstraint, ... ],
#       "ProxyConfiguration" : ProxyConfiguration,
#       "RequiresCompatibilities" : [ String, ... ],
#       "Tags" : [ Tag, ... ],
#       "TaskRoleArn" : String,
#       "Volumes" : [ Volume, ... ]
#     }
# }


# #!/bin/sh
# set -e

# # first arg is `-f` or `--some-option`
# if [ "${1#-}" != "$1" ]; then
#     set -- traefik "$@"
# fi

# # if our command is a valid Traefik subcommand, let's invoke it through Traefik instead
# # (this allows for "docker run traefik version", etc)
# if traefik "$1" --help >/dev/null 2>&1
# then
#     set -- traefik "$@"
# else
#     echo "= '$1' is not a Traefik command: assuming shell execution." 1>&2
# fi

# exec "$@"

# / # traefik --help
# traefik is a modern HTTP reverse proxy and load balancer made to deploy microservices with ease.
# Complete documentation is available at https://traefik.io

# Usage: traefik [flags] <command> [<arguments>]

# Use "traefik <command> --help" for help on any command.

# Commands:
#         bug                                                Report an issue on Traefik bugtracker
#         healthcheck                                        Calls traefik /ping to check health (web provider must be enabled)
#         storeconfig                                        Store the static traefik configuration into a Key-value stores. Traefik will not start.
#         version                                            Print version

# Flag's usage: traefik [--flag=flag_argument] [-f[flag_argument]] ...     set flag_argument to flag(s)
#           or: traefik [--flag[=true|false| ]] [-f[true|false| ]] ...     set true/false to boolean flag(s)

# Flags:
#     --accesslog                                   Access log settings                                                              (default "false")
#     --accesslog.bufferingsize                     Number of access log lines to process in a buffered way. Default 0.              (default "0")
#     --accesslog.fields                            AccessLogFields                                                                  (default "false")
#     --accesslog.fields.defaultmode                Default mode for fields: keep | drop                                             (default "keep")
#     --accesslog.fields.headers                    Headers to keep, drop or redact                                                  (default "false")
#     --accesslog.fields.headers.defaultmode        Default mode for fields: keep | drop | redact                                    (default "keep")
#     --accesslog.fields.headers.names              Override mode for headers                                                        (default "map[]")
#     --accesslog.fields.names                      Override mode for fields                                                         (default "map[]")
#     --accesslog.filepath                          Access log file path. Stdout is used when omitted or empty
#     --accesslog.filters                           Access log filters, used to keep only specific access logs                       (default "false")
#     --accesslog.filters.minduration               Keep access logs when request took longer than the specified duration            (default "0s")
#     --accesslog.filters.retryattempts             Keep access logs when at least one retry happened                                (default "false")
#     --accesslog.filters.statuscodes               Keep access logs with status codes in the specified range                        (default "[]")
#     --accesslog.format                            Access log format: json | common                                                 (default "common")
#     --accesslogsfile                              (Deprecated) Access logs file
#     --acme                                        Enable ACME (Let's Encrypt): automatic SSL                                       (default "false")
#     --acme.acmelogging                            Enable debug logging of ACME actions.                                            (default "false")
#     --acme.caserver                               CA server to use.
#     --acme.delaydontcheckdns                      (Deprecated) Assume DNS propagates after a delay in seconds rather than finding  (default "0s")
#                                                   and querying nameservers.
#     --acme.dnschallenge                           Activate DNS-01 Challenge                                                        (default "false")
#     --acme.dnschallenge.delaybeforecheck          Assume DNS propagates after a delay in seconds rather than finding and querying  (default "0s")
#                                                   nameservers.
#     --acme.dnschallenge.disablepropagationcheck   Disable the DNS propagation checks before notifying ACME that the DNS challenge  (default "false")
#                                                   is ready. [not recommended]
#     --acme.dnschallenge.provider                  Use a DNS-01 based challenge provider rather than HTTPS.
#     --acme.dnschallenge.resolvers                 Use following DNS servers to resolve the FQDN authority.
#     --acme.dnsprovider                            (Deprecated) Activate DNS-01 Challenge
#     --acme.domains                                SANs (alternative domains) to each main domain using format:                     (default "[]")
#                                                   --acme.domains='main.com,san1.com,san2.com'
#                                                   --acme.domains='main.net,san1.net,san2.net'
#     --acme.email                                  Email address used for registration
#     --acme.entrypoint                             Entrypoint to proxy acme challenge to.
#     --acme.httpchallenge                          Activate HTTP-01 Challenge                                                       (default "false")
#     --acme.httpchallenge.entrypoint               HTTP challenge EntryPoint
#     --acme.keytype                                KeyType used for generating certificate private key. Allow value 'EC256',
#                                                   'EC384', 'RSA2048', 'RSA4096', 'RSA8192'. Default to 'RSA4096'
#     --acme.ondemand                               (Deprecated) Enable on demand certificate generation. This will request a        (default "false")
#                                                   certificate from Let's Encrypt during the first TLS handshake for a hostname
#                                                   that does not yet have a certificate.
#     --acme.onhostrule                             Enable certificate generation on frontends Host rules.                           (default "false")
#     --acme.overridecertificates                   Enable to override certificates in key-value store when using storeconfig        (default "false")
#     --acme.storage                                File or key used for certificates storage.
#     --acme.tlschallenge                           Activate TLS-ALPN-01 Challenge                                                   (default "false")
#     --acme.tlsconfig                              TLS config in case wildcard certs are used                                       (default "false")
#     --allowminweightzero                          Allow weight to take 0 as minimum real value.                                    (default "false")
#     --api                                         Enable api/dashboard                                                             (default "false")
#     --api.dashboard                               Activate dashboard                                                               (default "true")
#     --api.entrypoint                              EntryPoint                                                                       (default "traefik")
#     --api.statistics                              Enable more detailed statistics                                                  (default "true")
#     --api.statistics.recenterrors                 Number of recent errors logged                                                   (default "10")
#     --boltdb                                      Enable Boltdb backend with default settings                                      (default "true")
#     --boltdb.constraints                          Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --boltdb.debugloggeneratedtemplate            Enable debug logging of generated configuration template.                        (default "false")
#     --boltdb.endpoint                             Comma separated server endpoints                                                 (default "127.0.0.1:4001")
#     --boltdb.filename                             Override default configuration template. For advanced users :)
#     --boltdb.password                             KV Password
#     --boltdb.prefix                               Prefix used for KV store                                                         (default "/traefik")
#     --boltdb.templateversion                      Template version.                                                                (default "0")
#     --boltdb.tls                                  Enable TLS support                                                               (default "false")
#     --boltdb.tls.ca                               TLS CA
#     --boltdb.tls.caoptional                       TLS CA.Optional                                                                  (default "false")
#     --boltdb.tls.cert                             TLS cert
#     --boltdb.tls.insecureskipverify               TLS insecure skip verify                                                         (default "false")
#     --boltdb.tls.key                              TLS key
#     --boltdb.trace                                Display additional provider logs (if available).                                 (default "false")
#     --boltdb.username                             KV Username
#     --boltdb.watch                                Watch provider                                                                   (default "true")
#     --checknewversion                             Periodically check if a new version has been released                            (default "true")
# -c, --configfile                                  Configuration file to use (TOML).
#     --constraints                                 Filter services by constraint, matching with service tags                        (default "[]")
#     --consul                                      Enable Consul backend with default settings                                      (default "true")
#     --consul.constraints                          Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --consul.debugloggeneratedtemplate            Enable debug logging of generated configuration template.                        (default "false")
#     --consul.endpoint                             Comma separated server endpoints                                                 (default "127.0.0.1:8500")
#     --consul.filename                             Override default configuration template. For advanced users :)
#     --consul.password                             KV Password
#     --consul.prefix                               Prefix used for KV store                                                         (default "traefik")
#     --consul.templateversion                      Template version.                                                                (default "0")
#     --consul.tls                                  Enable TLS support                                                               (default "false")
#     --consul.tls.ca                               TLS CA
#     --consul.tls.caoptional                       TLS CA.Optional                                                                  (default "false")
#     --consul.tls.cert                             TLS cert
#     --consul.tls.insecureskipverify               TLS insecure skip verify                                                         (default "false")
#     --consul.tls.key                              TLS key
#     --consul.trace                                Display additional provider logs (if available).                                 (default "false")
#     --consul.username                             KV Username
#     --consul.watch                                Watch provider                                                                   (default "true")
#     --consulcatalog                               Enable Consul catalog backend with default settings                              (default "true")
#     --consulcatalog.constraints                   Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --consulcatalog.debugloggeneratedtemplate     Enable debug logging of generated configuration template.                        (default "false")
#     --consulcatalog.domain                        Default domain used
#     --consulcatalog.endpoint                      Consul server endpoint                                                           (default "127.0.0.1:8500")
#     --consulcatalog.exposedbydefault              Expose Consul services by default                                                (default "true")
#     --consulcatalog.filename                      Override default configuration template. For advanced users :)
#     --consulcatalog.frontendrule                  Frontend rule used for Consul services                                           (default "Host:{{.ServiceName}}.{{.Domain}}")
#     --consulcatalog.prefix                        Prefix used for Consul catalog tags                                              (default "traefik")
#     --consulcatalog.stale                         Use stale consistency for catalog reads                                          (default "false")
#     --consulcatalog.strictchecks                  Keep a Consul node only if all checks status are passing                         (default "true")
#     --consulcatalog.templateversion               Template version.                                                                (default "0")
#     --consulcatalog.tls                           Enable TLS support                                                               (default "true")
#     --consulcatalog.tls.ca                        TLS CA
#     --consulcatalog.tls.caoptional                TLS CA.Optional                                                                  (default "false")
#     --consulcatalog.tls.cert                      TLS cert
#     --consulcatalog.tls.insecureskipverify        TLS insecure skip verify                                                         (default "false")
#     --consulcatalog.tls.key                       TLS key
#     --consulcatalog.trace                         Display additional provider logs (if available).                                 (default "false")
#     --consulcatalog.watch                         Watch provider                                                                   (default "false")
# -d, --debug                                       Enable debug mode                                                                (default "false")
#     --defaultentrypoints                          Entrypoints to be used by frontends that do not specify any entrypoint           (default "http")
#     --docker                                      Enable Docker backend with default settings                                      (default "false")
#     --docker.constraints                          Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --docker.debugloggeneratedtemplate            Enable debug logging of generated configuration template.                        (default "false")
#     --docker.domain                               Default domain used
#     --docker.endpoint                             Docker server endpoint. Can be a tcp or a unix socket endpoint                   (default "unix:///var/run/docker.sock")
#     --docker.exposedbydefault                     Expose containers by default                                                     (default "true")
#     --docker.filename                             Override default configuration template. For advanced users :)
#     --docker.network                              Default Docker network used
#     --docker.swarmmode                            Use Docker on Swarm Mode                                                         (default "false")
#     --docker.swarmmoderefreshseconds              Polling interval for swarm mode (in seconds)                                     (default "15")
#     --docker.templateversion                      Template version.                                                                (default "0")
#     --docker.tls                                  Enable Docker TLS support                                                        (default "false")
#     --docker.tls.ca                               TLS CA
#     --docker.tls.caoptional                       TLS CA.Optional                                                                  (default "false")
#     --docker.tls.cert                             TLS cert
#     --docker.tls.insecureskipverify               TLS insecure skip verify                                                         (default "false")
#     --docker.tls.key                              TLS key
#     --docker.trace                                Display additional provider logs (if available).                                 (default "false")
#     --docker.usebindportip                        Use the ip address from the bound port, rather than from the inner network       (default "false")
#     --docker.watch                                Watch provider                                                                   (default "true")
#     --dynamodb                                    Enable DynamoDB backend with default settings                                    (default "true")
#     --dynamodb.accesskeyid                        The AWS credentials access key to use for making requests
#     --dynamodb.constraints                        Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --dynamodb.debugloggeneratedtemplate          Enable debug logging of generated configuration template.                        (default "false")
#     --dynamodb.endpoint                           The endpoint of a dynamodb. Used for testing with a local dynamodb
#     --dynamodb.filename                           Override default configuration template. For advanced users :)
#     --dynamodb.refreshseconds                     Polling interval (in seconds)                                                    (default "15")
#     --dynamodb.region                             The AWS region to use for requests
#     --dynamodb.secretaccesskey                    The AWS credentials secret key to use for making requests
#     --dynamodb.tablename                          The AWS dynamodb table that stores configuration for traefik                     (default "traefik")
#     --dynamodb.templateversion                    Template version.                                                                (default "0")
#     --dynamodb.trace                              Display additional provider logs (if available).                                 (default "false")
#     --dynamodb.watch                              Watch provider                                                                   (default "true")
#     --ecs                                         Enable ECS backend with default settings                                         (default "true")
#     --ecs.accesskeyid                             The AWS credentials access key to use for making requests
#     --ecs.autodiscoverclusters                    Auto discover cluster                                                            (default "false")
#     --ecs.cluster                                 deprecated - ECS Cluster name
#     --ecs.clusters                                ECS Clusters name                                                                (default "[default]")
#     --ecs.constraints                             Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --ecs.debugloggeneratedtemplate               Enable debug logging of generated configuration template.                        (default "false")
#     --ecs.domain                                  Default domain used
#     --ecs.exposedbydefault                        Expose containers by default                                                     (default "true")
#     --ecs.filename                                Override default configuration template. For advanced users :)
#     --ecs.refreshseconds                          Polling interval (in seconds)                                                    (default "15")
#     --ecs.region                                  The AWS region to use for requests
#     --ecs.secretaccesskey                         The AWS credentials access key to use for making requests
#     --ecs.templateversion                         Template version.                                                                (default "0")
#     --ecs.trace                                   Display additional provider logs (if available).                                 (default "false")
#     --ecs.watch                                   Watch provider                                                                   (default "true")
#     --entrypoints                                 Entrypoints definition using format: --entryPoints='Name:http Address::8000      (default "map[]")
#                                                   Redirect.EntryPoint:https' --entryPoints='Name:https Address::4442
#                                                   TLS:tests/traefik.crt,tests/traefik.key;prod/traefik.crt,prod/traefik.key'
#     --etcd                                        Enable Etcd backend with default settings                                        (default "true")
#     --etcd.constraints                            Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --etcd.debugloggeneratedtemplate              Enable debug logging of generated configuration template.                        (default "false")
#     --etcd.endpoint                               Comma separated server endpoints                                                 (default "127.0.0.1:2379")
#     --etcd.filename                               Override default configuration template. For advanced users :)
#     --etcd.password                               KV Password
#     --etcd.prefix                                 Prefix used for KV store                                                         (default "/traefik")
#     --etcd.templateversion                        Template version.                                                                (default "0")
#     --etcd.tls                                    Enable TLS support                                                               (default "false")
#     --etcd.tls.ca                                 TLS CA
#     --etcd.tls.caoptional                         TLS CA.Optional                                                                  (default "false")
#     --etcd.tls.cert                               TLS cert
#     --etcd.tls.insecureskipverify                 TLS insecure skip verify                                                         (default "false")
#     --etcd.tls.key                                TLS key
#     --etcd.trace                                  Display additional provider logs (if available).                                 (default "false")
#     --etcd.useapiv3                               Use ETCD API V3                                                                  (default "false")
#     --etcd.username                               KV Username
#     --etcd.watch                                  Watch provider                                                                   (default "true")
#     --eureka                                      Enable Eureka backend with default settings                                      (default "true")
#     --eureka.constraints                          Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --eureka.debugloggeneratedtemplate            Enable debug logging of generated configuration template.                        (default "false")
#     --eureka.delay                                Override default configuration time between refresh (Deprecated)                 (default "0s")
#     --eureka.endpoint                             Eureka server endpoint
#     --eureka.filename                             Override default configuration template. For advanced users :)
#     --eureka.refreshseconds                       Override default configuration time between refresh                              (default "30s")
#     --eureka.templateversion                      Template version.                                                                (default "0")
#     --eureka.trace                                Display additional provider logs (if available).                                 (default "false")
#     --eureka.watch                                Watch provider                                                                   (default "false")
#     --file                                        Enable File backend with default settings                                        (default "false")
#     --file.constraints                            Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --file.debugloggeneratedtemplate              Enable debug logging of generated configuration template.                        (default "false")
#     --file.directory                              Load configuration from one or more .toml files in a directory
#     --file.filename                               Override default configuration template. For advanced users :)
#     --file.templateversion                        Template version.                                                                (default "0")
#     --file.trace                                  Display additional provider logs (if available).                                 (default "false")
#     --file.watch                                  Watch provider                                                                   (default "true")
#     --forwardingtimeouts                          Timeouts for requests forwarded to the backend servers                           (default "true")
#     --forwardingtimeouts.dialtimeout              The amount of time to wait until a connection to a backend server can be         (default "30s")
#                                                   established. Defaults to 30 seconds. If zero, no timeout exists
#     --forwardingtimeouts.responseheadertimeout    The amount of time to wait for a server's response headers after fully writing   (default "0s")
#                                                   the request (including its body, if any). If zero, no timeout exists
# -g, --gracetimeout                                (Deprecated) Duration to give active requests a chance to finish before Traefik  (default "0s")
#                                                   stops
#     --healthcheck                                 Health check parameters                                                          (default "true")
#     --healthcheck.interval                        Default periodicity of enabled health checks                                     (default "30s")
#     --hostresolver                                Enable CNAME Flattening                                                          (default "true")
#     --hostresolver.cnameflattening                A flag to enable/disable CNAME flattening                                        (default "false")
#     --hostresolver.resolvconfig                   resolv.conf used for DNS resolving                                               (default "/etc/resolv.conf")
#     --hostresolver.resolvdepth                    The maximal depth of DNS recursive resolving                                     (default "5")
#     --idletimeout                                 (Deprecated) maximum amount of time an idle (keep-alive) connection will remain  (default "0s")
#                                                   idle before closing itself.
#     --insecureskipverify                          Disable SSL certificate verification                                             (default "false")
#     --keeptrailingslash                           Do not remove trailing slash.                                                    (default "false")
#     --kubernetes                                  Enable Kubernetes backend with default settings                                  (default "false")
#     --kubernetes.certauthfilepath                 Kubernetes certificate authority file path (not needed for in-cluster client)
#     --kubernetes.constraints                      Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --kubernetes.debugloggeneratedtemplate        Enable debug logging of generated configuration template.                        (default "false")
#     --kubernetes.disablepasshostheaders           Kubernetes disable PassHost Headers                                              (default "false")
#     --kubernetes.enablepasstlscert                Kubernetes enable Pass TLS Client Certs                                          (default "false")
#     --kubernetes.endpoint                         Kubernetes server endpoint (required for external cluster client)
#     --kubernetes.filename                         Override default configuration template. For advanced users :)
#     --kubernetes.ingressclass                     Value of kubernetes.io/ingress.class annotation to watch for
#     --kubernetes.ingressendpoint                  Kubernetes Ingress Endpoint                                                      (default "false")
#     --kubernetes.ingressendpoint.hostname         Hostname used for Kubernetes Ingress endpoints
#     --kubernetes.ingressendpoint.ip               IP used for Kubernetes Ingress endpoints
#     --kubernetes.ingressendpoint.publishedservice Published Kubernetes Service to copy status from
#     --kubernetes.labelselector                    Kubernetes Ingress label selector to use
#     --kubernetes.namespaces                       Kubernetes namespaces                                                            (default "[]")
#     --kubernetes.templateversion                  Template version.                                                                (default "0")
#     --kubernetes.throttleduration                 Ingress refresh throttle duration                                                (default "0s")
#     --kubernetes.token                            Kubernetes bearer token (not needed for in-cluster client)
#     --kubernetes.trace                            Display additional provider logs (if available).                                 (default "false")
#     --kubernetes.watch                            Watch provider                                                                   (default "true")
#     --lifecycle                                   Timeouts influencing the server life cycle                                       (default "true")
#     --lifecycle.gracetimeout                      Duration to give active requests a chance to finish before Traefik stops         (default "10s")
#     --lifecycle.requestacceptgracetimeout         Duration to keep accepting requests before Traefik initiates the graceful        (default "0s")
#                                                   shutdown procedure
# -l, --loglevel                                    Log level
#     --marathon                                    Enable Marathon backend with default settings                                    (default "true")
#     --marathon.basic                              Enable basic authentication                                                      (default "true")
#     --marathon.basic.httpbasicauthuser            Basic authentication User
#     --marathon.basic.httpbasicpassword            Basic authentication Password
#     --marathon.constraints                        Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --marathon.dcostoken                          DCOSToken for DCOS environment, This will override the Authorization header
#     --marathon.debugloggeneratedtemplate          Enable debug logging of generated configuration template.                        (default "false")
#     --marathon.dialertimeout                      Set a dialer timeout for Marathon                                                (default "5s")
#     --marathon.domain                             Default domain used
#     --marathon.endpoint                           Marathon server endpoint. You can also specify multiple endpoint for Marathon    (default "http://127.0.0.1:8080")
#     --marathon.exposedbydefault                   Expose Marathon apps by default                                                  (default "true")
#     --marathon.filename                           Override default configuration template. For advanced users :)
#     --marathon.filtermarathonconstraints          Enable use of Marathon constraints in constraint filtering                       (default "false")
#     --marathon.forcetaskhostname                  Force to use the task's hostname.                                                (default "false")
#     --marathon.groupsassubdomains                 Convert Marathon groups to subdomains                                            (default "false")
#     --marathon.keepalive                          Set a TCP Keep Alive time in seconds                                             (default "10s")
#     --marathon.marathonlbcompatibility            Add compatibility with marathon-lb labels                                        (default "false")
#     --marathon.respectreadinesschecks             Filter out tasks with non-successful readiness checks during deployments         (default "false")
#     --marathon.responseheadertimeout              Set a response header timeout for Marathon                                       (default "1m0s")
#     --marathon.templateversion                    Template version.                                                                (default "0")
#     --marathon.tls                                Enable TLS support                                                               (default "false")
#     --marathon.tls.ca                             TLS CA
#     --marathon.tls.caoptional                     TLS CA.Optional                                                                  (default "false")
#     --marathon.tls.cert                           TLS cert
#     --marathon.tls.insecureskipverify             TLS insecure skip verify                                                         (default "false")
#     --marathon.tls.key                            TLS key
#     --marathon.tlshandshaketimeout                Set a TLS handhsake timeout for Marathon                                         (default "5s")
#     --marathon.trace                              Display additional provider logs (if available).                                 (default "false")
#     --marathon.watch                              Watch provider                                                                   (default "true")
#     --maxidleconnsperhost                         If non-zero, controls the maximum idle (keep-alive) to keep per-host.  If zero,  (default "200")
#                                                   DefaultMaxIdleConnsPerHost is used
#     --mesos                                       Enable Mesos backend with default settings                                       (default "true")
#     --mesos.constraints                           Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --mesos.debugloggeneratedtemplate             Enable debug logging of generated configuration template.                        (default "false")
#     --mesos.domain                                Default domain used
#     --mesos.endpoint                              Mesos server endpoint. You can also specify multiple endpoint for Mesos          (default "http://127.0.0.1:5050")
#     --mesos.exposedbydefault                      Expose Mesos apps by default                                                     (default "true")
#     --mesos.filename                              Override default configuration template. For advanced users :)
#     --mesos.groupsassubdomains                    Convert Mesos groups to subdomains                                               (default "false")
#     --mesos.ipsources                             IPSources (e.g. host, docker, mesos, netinfo)
#     --mesos.refreshseconds                        Polling interval (in seconds)                                                    (default "30")
#     --mesos.statetimeoutsecond                    HTTP Timeout (in seconds)                                                        (default "30")
#     --mesos.templateversion                       Template version.                                                                (default "0")
#     --mesos.trace                                 Display additional provider logs (if available).                                 (default "false")
#     --mesos.watch                                 Watch provider                                                                   (default "true")
#     --mesos.zkdetectiontimeout                    Zookeeper timeout (in seconds)                                                   (default "30")
#     --metrics                                     Enable a metrics exporter                                                        (default "true")
#     --metrics.datadog                             DataDog metrics exporter type                                                    (default "true")
#     --metrics.datadog.address                     DataDog's address                                                                (default "localhost:8125")
#     --metrics.datadog.pushinterval                DataDog push interval                                                            (default "10s")
#     --metrics.influxdb                            InfluxDB metrics exporter type                                                   (default "true")
#     --metrics.influxdb.address                    InfluxDB address                                                                 (default "localhost:8089")
#     --metrics.influxdb.database                   InfluxDB database used when protocol is http
#     --metrics.influxdb.protocol                   InfluxDB address protocol (udp or http)                                          (default "udp")
#     --metrics.influxdb.pushinterval               InfluxDB push interval                                                           (default "10s")
#     --metrics.influxdb.retentionpolicy            InfluxDB retention policy used when protocol is http
#     --metrics.prometheus                          Prometheus metrics exporter type                                                 (default "true")
#     --metrics.prometheus.buckets                  Buckets for latency metrics                                                      (default "[0.1 0.3 1.2 5]")
#     --metrics.prometheus.entrypoint               EntryPoint                                                                       (default "traefik")
#     --metrics.statsd                              StatsD metrics exporter type                                                     (default "true")
#     --metrics.statsd.address                      StatsD address                                                                   (default "localhost:8125")
#     --metrics.statsd.pushinterval                 StatsD push interval                                                             (default "10s")
#     --ping                                        Enable ping                                                                      (default "true")
#     --ping.entrypoint                             Ping entryPoint                                                                  (default "traefik")
#     --providersthrottleduration                   Backends throttle duration: minimum duration between 2 events from providers     (default "2s")
#                                                   before applying a new configuration. It avoids unnecessary reloads if multiples
#                                                   events are sent in a short amount of time.
#     --rancher                                     Enable Rancher backend with default settings                                     (default "true")
#     --rancher.accesskey                           Rancher server API access key
#     --rancher.api                                 Enable the Rancher API provider                                                  (default "true")
#     --rancher.api.accesskey                       Rancher server API access key
#     --rancher.api.endpoint                        Rancher server API HTTP(S) endpoint
#     --rancher.api.secretkey                       Rancher server API secret key
#     --rancher.constraints                         Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --rancher.debugloggeneratedtemplate           Enable debug logging of generated configuration template.                        (default "false")
#     --rancher.domain                              Default domain used
#     --rancher.enableservicehealthfilter           Filter services with unhealthy states and inactive states                        (default "false")
#     --rancher.endpoint                            Rancher server API HTTP(S) endpoint
#     --rancher.exposedbydefault                    Expose services by default                                                       (default "true")
#     --rancher.filename                            Override default configuration template. For advanced users :)
#     --rancher.metadata                            Enable the Rancher metadata service provider                                     (default "true")
#     --rancher.metadata.intervalpoll               Poll the Rancher metadata service every 'rancher.refreshseconds' (less accurate) (default "false")
#     --rancher.metadata.prefix                     Prefix used for accessing the Rancher metadata service
#     --rancher.refreshseconds                      Polling interval (in seconds)                                                    (default "15")
#     --rancher.secretkey                           Rancher server API secret key
#     --rancher.templateversion                     Template version.                                                                (default "0")
#     --rancher.trace                               Display additional provider logs (if available).                                 (default "false")
#     --rancher.watch                               Watch provider                                                                   (default "true")
#     --respondingtimeouts                          Timeouts for incoming requests to the Traefik instance                           (default "true")
#     --respondingtimeouts.idletimeout              IdleTimeout is the maximum amount duration an idle (keep-alive) connection will  (default "3m0s")
#                                                   remain idle before closing itself. Defaults to 180 seconds. If zero, no timeout
#                                                   is set
#     --respondingtimeouts.readtimeout              ReadTimeout is the maximum duration for reading the entire request, including    (default "0s")
#                                                   the body. If zero, no timeout is set
#     --respondingtimeouts.writetimeout             WriteTimeout is the maximum duration before timing out writes of the response.   (default "0s")
#                                                   If zero, no timeout is set
#     --rest                                        Enable Rest backend with default settings                                        (default "true")
#     --rest.entrypoint                             EntryPoint                                                                       (default "traefik")
#     --retry                                       Enable retry sending request if network error                                    (default "true")
#     --retry.attempts                              Number of attempts                                                               (default "0")
#     --rootcas                                     Add cert file for self-signed certificate
#     --sendanonymoususage                          send periodically anonymous usage statistics                                     (default "false")
#     --servicefabric                               Enable Service Fabric backend with default settings                              (default "false")
#     --servicefabric.apiversion                    Service Fabric API version
#     --servicefabric.appinsightsbatchsize          Number of trace lines per batch, optional                                        (default "0")
#     --servicefabric.appinsightsclientname         The client name, Identifies the cloud instance
#     --servicefabric.appinsightsinterval           The interval for sending data to Application Insights, optional                  (default "0s")
#     --servicefabric.appinsightskey                Application Insights Instrumentation Key
#     --servicefabric.clustermanagementurl          Service Fabric API endpoint
#     --servicefabric.constraints                   Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --servicefabric.debugloggeneratedtemplate     Enable debug logging of generated configuration template.                        (default "false")
#     --servicefabric.filename                      Override default configuration template. For advanced users :)
#     --servicefabric.refreshseconds                Polling interval (in seconds)                                                    (default "0s")
#     --servicefabric.templateversion               Template version.                                                                (default "0")
#     --servicefabric.tls                           Enable TLS support                                                               (default "false")
#     --servicefabric.tls.ca                        TLS CA
#     --servicefabric.tls.caoptional                TLS CA.Optional                                                                  (default "false")
#     --servicefabric.tls.cert                      TLS cert
#     --servicefabric.tls.insecureskipverify        TLS insecure skip verify                                                         (default "false")
#     --servicefabric.tls.key                       TLS key
#     --servicefabric.trace                         Display additional provider logs (if available).                                 (default "false")
#     --servicefabric.watch                         Watch provider                                                                   (default "false")
#     --tracing                                     OpenTracing configuration                                                        (default "false")
#     --tracing.backend                             Selects the tracking backend ('jaeger','zipkin', 'datadog').                     (default "jaeger")
#     --tracing.datadog                             Settings for DataDog                                                             (default "false")
#     --tracing.datadog.bagageprefixheadername      specifies the header name prefix that will be used to store baggage items in a
#                                                   map.
#     --tracing.datadog.debug                       Enable DataDog debug.                                                            (default "false")
#     --tracing.datadog.globaltag                   Key:Value tag to be set on all the spans.
#     --tracing.datadog.localagenthostport          Set datadog-agent's host:port that the reporter will used. Defaults to           (default "localhost:8126")
#                                                   localhost:8126
#     --tracing.datadog.parentidheadername          Specifies the header name that will be used to store the parent ID.
#     --tracing.datadog.prioritysampling            Enable priority sampling. When using distributed tracing, this option must be    (default "false")
#                                                   enabled in order to get all the parts of a distributed trace sampled.
#     --tracing.datadog.samplingpriorityheadername  Specifies the header name that will be used to store the sampling priority.
#     --tracing.datadog.traceidheadername           Specifies the header name that will be used to store the trace ID.
#     --tracing.jaeger                              Settings for jaeger                                                              (default "false")
#     --tracing.jaeger.localagenthostport           set jaeger-agent's host:port that the reporter will used.                        (default "127.0.0.1:6831")
#     --tracing.jaeger.samplingparam                set the sampling parameter.                                                      (default "1")
#     --tracing.jaeger.samplingserverurl            set the sampling server url.                                                     (default "http://localhost:5778/sampling")
#     --tracing.jaeger.samplingtype                 set the sampling type.                                                           (default "const")
#     --tracing.jaeger.tracecontextheadername       set the header to use for the trace-id.                                          (default "uber-trace-id")
#     --tracing.servicename                         Set the name for this service                                                    (default "traefik")
#     --tracing.spannamelimit                       Set the maximum character limit for Span names (default 0 = no limit)            (default "0")
#     --tracing.zipkin                              Settings for zipkin                                                              (default "false")
#     --tracing.zipkin.debug                        Enable Zipkin debug.                                                             (default "false")
#     --tracing.zipkin.httpendpoint                 HTTP Endpoint to report traces to.                                               (default "http://localhost:9411/api/v1/spans")
#     --tracing.zipkin.id128bit                     Use ZipKin 128 bit root span IDs.                                                (default "true")
#     --tracing.zipkin.samespan                     Use ZipKin SameSpan RPC style traces.                                            (default "false")
#     --traefiklog                                  Traefik log settings                                                             (default "false")
#     --traefiklog.filepath                         Traefik log file path. Stdout is used when omitted or empty
#     --traefiklog.format                           Traefik log format: json | common                                                (default "common")
#     --traefiklogsfile                             (Deprecated) Traefik logs file. Stdout is used when omitted or empty
#     --web                                         (Deprecated) Enable Web backend with default settings                            (default "false")
#     --web.address                                 (Deprecated) Web administration port                                             (default ":8080")
#     --web.certfile                                (Deprecated) SSL certificate
#     --web.keyfile                                 (Deprecated) SSL certificate
#     --web.metrics                                 (Deprecated) Enable a metrics exporter                                           (default "false")
#     --web.metrics.datadog                         DataDog metrics exporter type                                                    (default "false")
#     --web.metrics.datadog.address                 DataDog's address                                                                (default "localhost:8125")
#     --web.metrics.datadog.pushinterval            DataDog push interval                                                            (default "10s")
#     --web.metrics.influxdb                        InfluxDB metrics exporter type                                                   (default "false")
#     --web.metrics.influxdb.address                InfluxDB address                                                                 (default "localhost:8089")
#     --web.metrics.influxdb.database               InfluxDB database used when protocol is http
#     --web.metrics.influxdb.protocol               InfluxDB address protocol (udp or http)                                          (default "udp")
#     --web.metrics.influxdb.pushinterval           InfluxDB push interval                                                           (default "10s")
#     --web.metrics.influxdb.retentionpolicy        InfluxDB retention policy used when protocol is http
#     --web.metrics.prometheus                      Prometheus metrics exporter type                                                 (default "false")
#     --web.metrics.prometheus.buckets              Buckets for latency metrics                                                      (default "[0.1 0.3 1.2 5]")
#     --web.metrics.prometheus.entrypoint           EntryPoint                                                                       (default "traefik")
#     --web.metrics.statsd                          StatsD metrics exporter type                                                     (default "false")
#     --web.metrics.statsd.address                  StatsD address                                                                   (default "localhost:8125")
#     --web.metrics.statsd.pushinterval             StatsD push interval                                                             (default "10s")
#     --web.path                                    (Deprecated) Root path for dashboard and API
#     --web.readonly                                (Deprecated) Enable read only API                                                (default "false")
#     --web.statistics                              (Deprecated) Enable more detailed statistics                                     (default "false")
#     --web.statistics.recenterrors                 Number of recent errors logged                                                   (default "10")
#     --zookeeper                                   Enable Zookeeper backend with default settings                                   (default "false")
#     --zookeeper.constraints                       Filter services by constraint, matching with Traefik tags.                       (default "[]")
#     --zookeeper.debugloggeneratedtemplate         Enable debug logging of generated configuration template.                        (default "false")
#     --zookeeper.endpoint                          Comma separated server endpoints                                                 (default "127.0.0.1:2181")
#     --zookeeper.filename                          Override default configuration template. For advanced users :)
#     --zookeeper.password                          KV Password
#     --zookeeper.prefix                            Prefix used for KV store                                                         (default "traefik")
#     --zookeeper.templateversion                   Template version.                                                                (default "0")
#     --zookeeper.tls                               Enable TLS support                                                               (default "false")
#     --zookeeper.tls.ca                            TLS CA
#     --zookeeper.tls.caoptional                    TLS CA.Optional                                                                  (default "false")
#     --zookeeper.tls.cert                          TLS cert
#     --zookeeper.tls.insecureskipverify            TLS insecure skip verify                                                         (default "false")
#     --zookeeper.tls.key                           TLS key
#     --zookeeper.trace                             Display additional provider logs (if available).                                 (default "false")
#     --zookeeper.username                          KV Username
#     --zookeeper.watch                             Watch provider                                                                   (default "true")
# -h, --help                                        Print Help (this message) and exit
# / # [ec2-user@ip-10-128-1-173 ~]$