---
name: intelica-arca-finops
description: "Recipes and verified billing facts for cost and license questions about Intelica's AWS accounts: what a service costs per day or month, which usage type a charge comes from, when a charge starts or stops, who actually uses a QuickSight license and who doesn't, who owns which dashboards or datasets, and what a user would lose if removed. Use it when the question is about money, licenses, seats or usage — 'how much do we pay for QuickSight', 'who hasn't logged in', 'if I delete this user today, how much do we save', 'why did the bill go up'. Read-only: any change (deleting users, changing roles, cancelling a subscription) is handed over as a script, never executed. Not for generic AWS pricing questions that don't involve Intelica's accounts."
---

# Intelica ARCA FinOps

How to answer cost and license questions with the `intelica-aws` tools, and
the billing behaviour already verified in these accounts. Everything here was
checked against real data on the date given; re-check before relying on a
fact older than a few months.

## Cost Explorer

- `aws_api(account, "ce", "GetCostAndUsage", ..., region="us-east-1")`.
  **Each call costs US$0.01** — ask for the right period, granularity and
  grouping in one call instead of iterating.
- `Granularity: DAILY` is what shows *when* a charge changed. Monthly totals
  hide it.
- Group by `USAGE_TYPE` to see what a charge is made of. Filter by
  `SERVICE` (e.g. `Amazon QuickSight`) or by the usage types themselves.
- A linked account sees its own costs. Numbers are what was billed, after
  discounts: compare them with list prices, never replace them.
- **How many users are being billed**: for a `-Month` usage type, the daily
  `UsageQuantity` is users ÷ days in the month (5 readers in October →
  0.16129). Quantity × days = users billed that day; cost ÷ quantity = price
  per user-month. One `DAILY` call grouped by `USAGE_TYPE` answers both.
- Report the Cost Explorer charge once. Since intelica-arca-mcp #29 the
  `_costo` of a `ce` response carries `costo_aws_usd_aprox: 0.01`: use it as
  is. If a `ce` response doesn't carry it (server not yet deployed), add
  US$0.01 per call yourself. Never both.

## QuickSight billing (verified 2026-10-08, portal-dev and portal-prod)

| Usage type | What it is | Billed per user-month |
|---|---|---|
| `QS-User-Enterprise-Month` | Authors **and** admins | US$22.08 (list US$24) |
| `USE1-Reader-Enterprise-Month` | Readers | US$2.76 (list US$3) |
| `USE1-QuickSuite-Index` | Fixed per account | ~US$1.15 |
| `EUS2-QS-Enterprise-SPICE` | SPICE capacity in eu-south-2 | by GB |
| `USE1-Author-Pro-Enterprise-Month` | Author Pro / Admin Pro | US$36.80 (list US$40) |
| `USE1-Amazon-Q-QS-Fee` | Account fee once there is a Pro user with Q enabled | US$230/month (list US$250) |

One Pro user is enough to trigger the US$250 account fee: in June 2026
portal-dev paid 0.975 Author Pro user-month (US$35.88) **and** the full
US$230 fee; both disappeared in July.

- **A user added mid-month is charged from that moment**, prorated by the
  hours left in the month (a registration on 2026-10-01 at 14:02 UTC shows
  as 0.42 of that day).
- **A user deleted mid-month is charged for the whole month** and stops on
  the 1st of the next one (an author deleted 2026-09-09 kept being charged
  until 2026-10-01). AWS's pricing page and FAQ don't document this; the
  daily Cost Explorer data does.
- Consequence: deleting, downgrading or cancelling saves nothing in the
  current month. Schedule those changes for the last days of the month.
- A reader costs the same whether or not they log in. There is no suspended
  state; reader capacity pricing starts at US$250/month.

## QuickSight: who is billed, user by user

To answer "who are we paying for" without deducing it from a total:

- `aws_api(account, "ce", "GetCostAndUsageWithResources", region="us-east-1")`
  with `Filter` on `SERVICE = Amazon QuickSight` (and the usage type if you
  want only one), `GroupBy` `RESOURCE_ID` (add `USAGE_TYPE` to see every
  charge), `Granularity: MONTHLY`. Each row is the **ARN of a QuickSight
  user** with its quantity and cost.
- It only covers **the last 14 days**. Before that, only totals.
- Each ARN comes at **list price** (US$24 author, US$3 reader). The discount
  is a separate `NoResourceId` row with quantity 0 and a negative cost. If
  `NoResourceId` has quantity 0, the ARNs account for everything billed.
- Compare the ARNs with `ListUsers`: a user in the list with no row is not
  being billed; a billed ARN not in the list was deleted this month (and is
  still charged until the 1st).
- Verified 2026-10-10 in portal-dev, portal-prod and interchange-dev. It
  found that `hildebrando.nunez` (ADMIN, `ItlAWSAllAdm`) has no billing row in
  portal-dev while he is billed in the other two accounts; the cause is open
  with AWS Support, not a known rule.

## QuickSight: who uses a license

1. **Users live in the identity region**, `us-east-1`:
   `ListUsers(AwsAccountId, Namespace="default")`. Dashboards and their
   activity live in `eu-south-2`.
2. **`Active: false` says nothing about use** — not as proof, not as a hint,
   not to decide who to look at first. Users that come in through the
   Portal's embedded dashboards never activate by email and are used daily.
   Only CloudTrail answers whether someone uses a license.
3. **Activity is in CloudTrail**, `eu-south-2`, `LookupEvents` with
   `AttributeKey=Username`:
   - SSO users (`AWSReservedSSO_.../email`): the username is the **email**,
     the text after `:` in the `PrincipalId`.
   - Native QuickSight users (`user/d-.../<guid>`): the username is the
     **GUID** at the end of the `PrincipalId`.
   - Keep only `EventSource == quicksight.amazonaws.com`. Opening a
     dashboard logs `GetStaticAsset` and, for direct-query datasets,
     `QueryDatabase`.
   - CloudTrail keeps **90 days**. "No events" means none in that window.
   - SSO users also generate events in other services. If a full page comes
     back with no QuickSight event, the answer is "undetermined", not
     "unused".
4. **Who was added or removed, and when**: CloudTrail in `us-east-1`,
   `LookupEvents` by `EventName` (`RegisterUser`, `DeleteUser`), then keep
   `EventSource == quicksight.amazonaws.com`. `Resources` comes back empty,
   but the user **is** in the `CloudTrailEvent` JSON, in a different place
   for each event:
   - `DeleteUser`: `serviceEventDetails.eventRequestDetails.user.userName`
     and `.role` (`USER` means author), plus `transferResourceToUser` when
     assets were handed over.
   - `RegisterUser`: `requestParameters.sessionName` and `.userRole`, and
     `responseElements.user.userName`. There is no `serviceEventDetails`.
5. **What they can see**: `SearchDashboards` in `eu-south-2` with
   `Filters=[{Operator: StringEquals, Name: QUICKSIGHT_VIEWER_OR_OWNER,
   Value: <user ARN>}]`. Use `QUICKSIGHT_OWNER` for ownership, and
   `SearchDataSets` for datasets. `SearchAnalyses` is not allowed to the
   reader role yet.

## What a change costs the people affected

- **Deleting a user** removes it from every dashboard permission, and
  permanently deletes the assets it alone owns unless they are transferred
  first. Dashboards in these accounts are shared user by user, not by
  group: a re-created user comes back with nothing.
- **SSO users can't re-register themselves today**: the QuickSight
  permission sets (`ItlAWSPortalPRDQs`, `ItlAWSPortalDevQs`) are `Deny *`,
  and users were registered by an admin. Self-registration needs
  `quicksight:CreateReader` on `arn:aws:quicksight::<account>:user/${aws:userid}`
  in the permission set (IAM Identity Center).
- **Downgrading an author** (`UpdateUser` with `Role=READER`) keeps the user
  and its access to shared dashboards; check first that it owns nothing.
- Cancelling a subscription (`DeleteAccountSubscription`) needs termination
  protection off first.

## Rules

- Read-only. Changes go out as a script with the real identifiers, a dry-run
  by default, a re-check of the condition right before acting, and the date
  it should run (end of month).
- Separate what the bill shows from what you infer from it. Quote the usage
  type and the amount.
- Exact numbers. If you counted 13 inactive readers, it's 13 — and say over
  which window.
