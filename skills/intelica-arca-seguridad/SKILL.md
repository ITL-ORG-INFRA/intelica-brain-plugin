---
name: intelica-arca-seguridad
description: "Method, read-only recipes, a controls catalog and GuardDuty triage playbooks for the security of Intelica's AWS accounts and EKS clusters: what is reachable from the internet and through which path, who holds which credentials, where data and secrets sit, what runs privileged in Kubernetes, which known vulnerabilities are open (Inspector, ECR scans, versions out of support), what the account would detect, which controls are missing for a goal, and whether a GuardDuty finding is a breach or a false positive. Ranks by exposure, not by count. Loaded by the seraph agent; use it too for 'qué está abierto a internet', 'quién tiene llaves viejas', 'qué controles faltan', 'este finding de GuardDuty es real'. Never prints a secret's value. Read-only: any fix is handed over as a script with its rollback."
---

# Security review

The question is always the same: **who can reach what, with which
credential, and would anyone notice.** A finding is a path, not a setting.

## Exposure scale

Rank by the worst thing someone could do through the path, not by how many
resources share it:

| Level | What it means | Examples |
|---|---|---|
| **Crítico** | Reachable from the internet with no credential, a credential exposed where others can read it, or an active breach | An admin UI (redisinsight, grafana, argocd, airflow, metabase, appsmith) on an `internet-facing` ALB with no `authenticate-oidc/cognito` rule and no IP restriction; 22/3389/a database port open to `0.0.0.0/0` on an ENI with a public IP; a public snapshot, AMI or bucket; a password in plain text in a manifest or a public repo; a GuardDuty finding triaged as *brecha probable*; an exploitable CRITICAL CVE on an internet-facing host |
| **Alto** | Reachable from the internet behind a weak or shared credential, an internal credential with far more permission than its job needs, or an account nobody watches | Database or EKS API public with `0.0.0.0/0`; IAM user keys older than 90 days in use; a workload role with `*FullAccess` or `*:*`; a role trusting another account or `*` without `ExternalId`; GuardDuty disabled for a member; HIGH CVEs on internet-facing workloads |
| **Medio** | Not reachable from outside, but a mistake away from it, or a blind spot | A SG open to the world on an ENI without a public IP; a rule pointing to a SG that no longer exists; a security agent crashlooping; CloudTrail not multi-region; unencrypted volumes; versions out of standard support; an account outside Inspector |
| **Bajo** | Hygiene | `:latest` images, unused SGs, old keys never used |

**Verify the path before the level.** Public IP or `internet-facing`
balancer → route to an internet gateway → SG → NACL → listener rule →
target. A configuration that would be open but has no path is one level
lower and says so. Nobody sends requests to the services to prove it.

## Fronts and recipes

*barrido* marks the checks a platform review runs in every account; the
rest go into a front's deep review or a task.

| Front | Check | How (`aws_api`, `k8s_*`) |
|---|---|---|
| Exposición | *barrido* SGs open to the world | `DescribeSecurityGroupRules` with `CidrIpv4 = 0.0.0.0/0` or `CidrIpv6 = ::/0` on ingress; which ENIs use them (`DescribeNetworkInterfaces` filter `group-id`) and whether they have `Association.PublicIp` |
| Exposición | *barrido* Public balancers | `DescribeLoadBalancers` `Scheme = internet-facing`; `DescribeListeners`, `DescribeRules`: an `authenticate-*` action or a `source-ip` condition, or neither; what the target groups serve; `wafv2 GetWebACLForResource` |
| Exposición | *barrido* Public endpoints and data | RDS `PubliclyAccessible`; EKS `endpointPublicAccess` + `publicAccessCidrs`; S3 `GetPublicAccessBlock` (account and bucket), `GetBucketPolicyStatus`; `DescribeSnapshotAttribute createVolumePermission` and `DescribeImageAttribute launchPermission` with `all` |
| Exposición | Stale references | `DescribeStaleSecurityGroups` per VPC |
| Identidad | *barrido* IAM users | `ListUsers`; per user `ListAccessKeys`, `GetAccessKeyLastUsed`, `ListMFADevices`, `GetLoginProfile` |
| Identidad | Over-permissioned roles | Instance profiles and IRSA roles: `ListAttachedRolePolicies`, `GetPolicyVersion` of the default version: `*:*`, `*FullAccess`, `iam:PassRole` or `ssm:SendCommand` on `*` |
| Identidad | Trust | `GetRole` `AssumeRolePolicyDocument`: other accounts, `*`, no `sts:ExternalId`, OIDC providers without a `sub` condition |
| Datos y secretos | *barrido* Plain-text secrets | Deployments, StatefulSets, CronJobs, ConfigMaps: variables named `*PASSWORD*`, `*SECRET*`, `*TOKEN*`, `*KEY*` with a literal `value` instead of `valueFrom.secretKeyRef`. **Name only** |
| Datos y secretos | Encryption | `DescribeVolumes` `Encrypted`, `GetEbsEncryptionByDefault`, `DescribeDBInstances` `StorageEncrypted`, `GetBucketEncryption` |
| Kubernetes | *barrido* Privileged workloads | `k8s_get pod` across namespaces: `privileged`, `hostNetwork`, `hostPID`, `hostPath`, `runAsUser: 0`, `SYS_ADMIN`/`NET_ADMIN`, `:latest` |
| Kubernetes | Exposure inside out | Services `type: LoadBalancer` and Ingresses with public schemes; what they route to |
| Vulnerabilidades | *barrido* Open CVEs | `inspector2 ListFindings` with `findingStatus = ACTIVE` and `severity` CRITICAL/HIGH, grouped by resource; `fixAvailable`, `exploitAvailable`, and whether the resource is internet-facing (from Exposición). An exploitable CRITICAL on a public host is crítico |
| Vulnerabilidades | *barrido* Coverage | `inspector2 ListCoverage` / `ListCoverageStatistics`: which EC2, ECR repos and Lambdas are scanned; an account outside Inspector is a finding |
| Vulnerabilidades | Images | `ecr DescribeImageScanFindings` for the tags deployed today (from the pods); `ecr DescribeRepositories` `imageScanningConfiguration` |
| Vulnerabilidades | Out of support | EKS `version` and `upgradePolicy`; RDS `DescribeDBEngineVersions` for the running engine versions (`Status: deprecated`); EC2 `PlatformDetails` (Windows Server 2012/2016); Lambda `Runtime` deprecated |
| Detección | *barrido* Is anyone watching | From audit: `guardduty ListMembers` (each account `Enabled`?), `GetFindingsStatistics`; in each account `GetDetector` features (EKS audit logs, runtime monitoring, S3, RDS, malware); the `aws-guardduty-agent` DaemonSet healthy; `securityhub DescribeHub` / `GetEnabledStandards`; `cloudtrail DescribeTrails` + `GetTrailStatus`; `accessanalyzer ListAnalyzers` + `ListFindings` |

GuardDuty findings and Inspector coverage for the whole platform are read
in **audit**, the delegated administrator. Which members are disabled and
which accounts Inspector doesn't cover is in seraph's memory, not here:
**this plugin repository is public**, and a list of blind spots is exactly
what not to publish.

What the tools can't do: they don't read secret values (by design),
`GenerateCredentialReport` isn't a read, and Kubernetes cluster-scoped
objects (nodes, PVs, ClusterRoles, ClusterRoleBindings) return 403.

## Controls catalog (for a task)

What a task proposes comes from here, **verified against the account**:
each control is present, partial or absent, with the evidence. Generic
advice that wasn't checked is not a row.

| Layer | Control | How to verify it |
|---|---|---|
| Preventivo | S3 Block Public Access at account level | `s3control GetPublicAccessBlock` |
| Preventivo | EBS encryption by default | `GetEbsEncryptionByDefault` per region |
| Preventivo | IMDSv2 required | `DescribeInstances` `MetadataOptions.HttpTokens = required`; account default `GetInstanceMetadataDefaults` |
| Preventivo | Admin UIs behind authentication | ALB rules with `authenticate-oidc`/`cognito`, or not public at all (internal scheme, VPN) |
| Preventivo | WAF on public balancers | `wafv2 GetWebACLForResource`; managed rule groups (core, known bad inputs, IP reputation) |
| Preventivo | No long-lived keys | IAM users with keys → roles, SSO, IRSA |
| Preventivo | Secrets out of manifests | `valueFrom.secretKeyRef` or External Secrets → Secrets Manager with rotation (`DescribeSecret` `RotationEnabled`) |
| Preventivo | Least privilege for workloads | IRSA per service account instead of the node role; no `*FullAccess` |
| Preventivo | Guardrails in the organization | SCPs (`organizations ListPolicies` from the management account, if reachable): deny leaving the org, disabling GuardDuty/CloudTrail, public S3 |
| Detectivo | GuardDuty in every account, with EKS audit logs, runtime monitoring, S3, RDS and malware protection | `ListMembers`, `GetDetector` features |
| Detectivo | Inspector on EC2, ECR and Lambda in every account | `ListCoverageStatistics` |
| Detectivo | Security Hub with AWS Foundational Best Practices and CIS | `GetEnabledStandards` |
| Detectivo | CloudTrail multi-region, with log file validation, to Log Archive | `DescribeTrails` |
| Detectivo | IAM Access Analyzer (external access, unused access) | `ListAnalyzers` |
| Detectivo | VPC flow logs on every VPC | `DescribeFlowLogs` |
| Respuesta | Alerts reach someone | EventBridge rules on GuardDuty/Security Hub findings to SNS or a chat channel (`events ListRules` with `aws.guardduty`) |
| Respuesta | Backups that an attacker can't delete | AWS Backup vault lock, cross-account copies (`backup DescribeBackupVault` `Locked`) |
| Respuesta | A way to isolate fast | A quarantine SG per VPC, a documented `AWSRevokeOlderSessions` procedure |

Cost matters for detection controls (runtime monitoring, Inspector,
Security Hub bill per resource or finding): say it, from the bill when the
account already pays for it.

## GuardDuty triage

The findings are read in audit, the delegated administrator. For each
finding (or group of the same type on the same resource), gather the
evidence that decides, then give one verdict — **brecha probable**,
**sospechosa**, **benigna esperada** or **falso positivo** — with a
confidence and the **punto crítico**: the one fact that, if it were
different, would change the verdict.

Always:

- **Who and when**: `cloudtrail LookupEvents` in the finding's account
  around `Service.EventFirstSeen` / `EventLastSeen` (±30 min), by the
  resource, the access key or the role session in the finding. A deploy, an
  apply or a DBA session at that time usually explains it.
- **The remote party**: `Service.Action.*.RemoteIpDetails` — the company's
  IPs (VPN, offices), AWS service ranges and known vendors are benign
  candidates; a hosting ASN or Tor with credentials is not.
- **Repeats and neighbours**: the same type on other resources, other
  findings on the same resource in the same window.
- **The resource's blast radius**: its role's permissions, SG, public IP,
  what data it reaches.

By type — common in EC2 and EKS environments like these:

| Type | Usually | What decides (punto crítico) |
|---|---|---|
| `Persistence:Runtime/SensitiveFileModified`, `DefenseEvasion:Runtime/SensitiveFileModified` | Benign when a package update, config management or a deploy touched `/etc` | The process and its parent in `Service.RuntimeDetails` (yum/apt/dnf, cloud-init, ssm-agent → benign; a shell spawned by a web process → not), and whether the file is `passwd`/`shadow`/`sudoers`/`authorized_keys` and changed outside a maintenance window |
| `CredentialAccess:Kubernetes/AnomalousBehavior.SecretsAccessed` | Benign when the actor is a controller (external-secrets, argocd, a CSI driver) or a human admin during a change | `Resource.KubernetesDetails.KubernetesUserDetails`: a service account of a known controller in its namespace vs. a user or SA that never read secrets before; CloudTrail/EKS audit for the same user at that time |
| `Execution:Kubernetes/AnomalousBehavior.ExecInPod` | Benign when an operator debugs | Who (`KubernetesUserDetails`), into which pod, what command; an exec into a pod in a production namespace by an unknown identity is not benign |
| `PrivilegeEscalation:Kubernetes/AnomalousBehavior.WorkloadDeployed!PrivilegedContainer` | Benign when it's a known DaemonSet (CNI, CSI, security agents) deployed by its addon | The image and the deployer: an AWS or vendor image deployed by the EKS addon manager or the Helm release that owns it → benign; an unknown image or a user → suspicious |
| `DefenseEvasion:EC2/UnusualDNSResolver` | False positive when the resolver is the company's own (domain controllers, an on-prem DNS over VPN, a Route 53 Resolver endpoint) | Whether the resolver IP in `RemoteIpDetails` belongs to the company (intelica-network resolvers, the AD DNS); a public resolver nobody configured is suspicious |
| `Behavior:EC2/NetworkPortUnusual` | Depends on the port and the peer | Whether the remote IP/port is a known service of the app (a partner SFTP, a license server) |
| `Recon:EC2/PortProbeUnprotectedPort` | Expected noise if the port is meant to be public; a real exposure if not | Whether the probed port should be open at all: if it shouldn't, the finding is the SG, not the probe |
| `UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration.*` | Rarely benign | The source IP of the calls made with the instance role's session: outside AWS and outside the company → brecha probable; containment is revoking the role's sessions and isolating the instance |
| `UnauthorizedAccess:EC2/SSHBruteForce`, `RDPBruteForce` | Noise against a public port; serious if the instance is the source, or if a login succeeded | Direction (`Resource` is target or actor) and whether any authentication succeeded |
| `CryptoCurrency:*`, `Trojan:*`, `Backdoor:*` | Not benign | Treat as breach until disproven |

**Containment**, for a likely breach, as a script with rollback, in this
order: isolate (a quarantine SG, or scale the workload to 0), revoke
sessions (`AWSRevokeOlderSessions` on the role), preserve evidence
(snapshot the volumes before anything else changes them), rotate whatever
the resource could read. **A suppression rule**, for a true false positive,
scoped to exactly that type, resource and condition (`guardduty
create-filter` with `Action: ARCHIVE`) — never by type alone, which would
hide the next real one.

## Secrets

- **Never write a secret's value**, whole or partial, in a finding, a
  command, a script, a report or memory. The finding is that it exists,
  where, and what it opens.
- If a tool returns a value that should have been redacted, that is a
  finding against the MCP server: name the tool, the resource and the field,
  without the value.
- A plain-text secret is fixed in this order: rotate the credential (it has
  been readable), then move it to a Secret or Secrets Manager. Moving it
  without rotating leaves the old one valid.

## The change

Real IDs, rollback, a window, how to verify — and the question savings
never ask: **who uses this path today.** Closing a port or adding
authentication to a balancer someone depends on is an incident. VPC flow
logs (`FilterLogEvents` by `dstport` and `srcaddr` outside the VPC) or the
ALB's `RequestCount` say whether there is traffic; if there's no way to
tell, the finding says so.

Terraform first: tags of IaC or the `itl-NNNN-…` name mean the change goes
in the module; a CLI change is reverted by the next `apply`.
