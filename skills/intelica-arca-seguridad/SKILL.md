---
name: intelica-arca-seguridad
description: "Method and read-only recipes for reviewing the security of Intelica's AWS accounts and EKS clusters: what is reachable from the internet and through which path, who holds which credentials, where data and secrets sit and whether they are exposed, what runs privileged in Kubernetes, and what the account would and wouldn't detect. Ranks findings by exposure, not by count. Use it when the question is about exposure, access or detection — 'qué está abierto a internet en portal-qa', 'quién tiene llaves viejas', 'este SG deja entrar a cualquiera', 'redisinsight está publicado', 'GuardDuty está andando'. Loaded by the seraph agent. Never prints a secret's value. Read-only: any fix is handed over as a script with its rollback."
---

# Security review

The question is always the same: **who can reach what, with which
credential, and would anyone notice.** A finding is a path, not a setting.

## Exposure scale

Rank by the worst thing someone could do through the path, not by how many
resources share it:

| Level | What it means | Examples |
|---|---|---|
| **Crítico** | Reachable from the internet with no credential, or a credential is exposed where others can read it | An admin UI (redisinsight, grafana, argocd, airflow, metabase, appsmith) on an `internet-facing` ALB with no `authenticate-oidc/cognito` rule and no IP restriction; 22/3389/a database port open to `0.0.0.0/0` on an ENI with a public IP; a public snapshot or AMI; a bucket readable by anyone; a password in plain text in a manifest |
| **Alto** | Reachable from the internet behind a weak or shared credential, or an internal credential with far more permission than its job needs | A database or EKS API endpoint public with an allow-list of `0.0.0.0/0`; IAM user keys older than 90 days in use; a workload role with `*FullAccess` or `*:*`; a role trusting another account or `*` without `ExternalId` |
| **Medio** | Not reachable from outside, but a mistake away from it, or a blind spot | A SG open to the world on an ENI without a public IP; a rule pointing to a SG that no longer exists; GuardDuty or Security Hub off or its agent crashlooping; CloudTrail not multi-region; unencrypted volumes or databases |
| **Bajo** | Hygiene | `:latest` images, unused SGs, old access keys never used |

**Verify the path before the level.** Public IP or `internet-facing`
balancer → route to an internet gateway → SG → NACL → listener rule →
target. A configuration that would be open but has no path is one level
lower and says so. Nobody sends requests to the services to prove it: the
level comes from configuration.

## Fronts and recipes

| Front | Check | How (`aws_api`, `k8s_*`) |
|---|---|---|
| Exposición | SGs open to the world | `DescribeSecurityGroupRules` with `CidrIpv4 = 0.0.0.0/0` or `CidrIpv6 = ::/0` on ingress; which ENIs use the group (`DescribeNetworkInterfaces` filter `group-id`) and whether they have `Association.PublicIp` |
| Exposición | Stale references | `DescribeStaleSecurityGroups` per VPC |
| Exposición | Public balancers | `DescribeLoadBalancers` `Scheme = internet-facing`; `DescribeListeners` and `DescribeRules`: an `authenticate-*` action or a `source-ip` condition, or neither; the target groups and what they serve (for EKS, the `ingress.k8s.aws/stack` tag and the Ingress); `wafv2 GetWebACLForResource` |
| Exposición | Public endpoints | RDS `PubliclyAccessible`; EKS `resourcesVpcConfig.endpointPublicAccess` and `publicAccessCidrs`; OpenSearch/Elasticsearch domain policies |
| Exposición | Public data | S3 `GetPublicAccessBlock` (account and bucket) and `GetBucketPolicyStatus`; `DescribeSnapshotAttribute createVolumePermission` and `DescribeImageAttribute launchPermission` looking for `all`; RDS snapshot attribute `restore` with `all` |
| Identidad | IAM users | `ListUsers`; per user `ListAccessKeys`, `GetAccessKeyLastUsed`, `ListMFADevices`, `GetLoginProfile`. Keys > 90 days, console without MFA, users that should be roles |
| Identidad | Over-permissioned roles | Instance profiles and IRSA roles (`ListAttachedRolePolicies`, `GetPolicyVersion` of the default version): `*:*`, `*FullAccess`, `iam:PassRole` on `*`, `ssm:SendCommand` on `*` |
| Identidad | Trust | `GetRole` `AssumeRolePolicyDocument`: other accounts, `*`, no `sts:ExternalId`, OIDC providers without `sub` condition |
| Datos y secretos | Plain-text secrets | Kubernetes Deployments, StatefulSets, CronJobs and ConfigMaps: variables named like `*PASSWORD*`, `*SECRET*`, `*TOKEN*`, `*KEY*` with a literal `value` instead of `valueFrom.secretKeyRef`. **Name only, never the value** |
| Datos y secretos | Encryption | `DescribeVolumes` `Encrypted`, `DescribeDBInstances` `StorageEncrypted`, `GetBucketEncryption` |
| Kubernetes | Privileged workloads | `k8s_get pod` across namespaces: `securityContext.privileged`, `hostNetwork`, `hostPID`, `hostPath`, `runAsUser: 0`, capabilities `SYS_ADMIN`/`NET_ADMIN`, `:latest` images |
| Kubernetes | Exposure inside out | Services `type: LoadBalancer` and Ingresses with public schemes; what they route to |
| Detección | Is anyone watching | `guardduty ListDetectors` / `GetDetector` / `ListFindings` + `GetFindings` (high severity, last 30 days); the `aws-guardduty-agent` DaemonSet healthy; `securityhub GetFindings`; `cloudtrail DescribeTrails` + `GetTrailStatus` (multi-region, logging); `accessanalyzer ListFindings` |

What the tools can't do, verified: they don't read secret values (by
design), `GenerateCredentialReport` isn't a read, and Kubernetes
cluster-scoped objects (nodes, PVs, ClusterRoles, ClusterRoleBindings) return
403 with the current access entries.

## Secrets

- **Never write a secret's value**, whole or partial, in a finding, a
  command, a script or memory. The finding is that it exists, where, and
  what it opens.
- If a tool returns a value that should have been redacted, that is a
  finding against the MCP server: name the tool, the resource and the field,
  without the value. Known case (2026-10-11): the annotation
  `kubectl.kubernetes.io/last-applied-configuration` carries the whole
  manifest as text and `guard.redact` doesn't look inside it.
- A fix for a plain-text secret is two steps, in this order: rotate the
  credential (it has been readable), then move it to a Secret or Secrets
  Manager. Moving it without rotating leaves the old one valid.

## The change

Same as any change here: real IDs, rollback, a window, how to verify. And
one more question that savings never ask: **who uses this path today.**
Closing a port or adding authentication to a balancer someone depends on is
an incident. VPC flow logs (`FilterLogEvents` on the flow log group, by
`dstport` and `srcaddr` outside the VPC) or the ALB's `RequestCount` say
whether there is traffic; if there's no way to tell, the finding says so.

Terraform first: tags of IaC or the `itl-NNNN-…` name mean the change goes
in the module; a CLI change is reverted by the next `apply`.
