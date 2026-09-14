#!/usr/bin/env python3
"""Builds the complete `push_knowledge` call from structured data: validates
the entities and relations against the curated vocabulary below (transcribed
from KNOWLEDGE_MODEL.md, which lives in the root of intelica-brain-ia — the
knowledge repo, not this one), writes both the `.md`
and its sibling `.graph.yaml`, and computes the deterministic parts (today's
date, slugs, branch name, paths).

Why the script writes the YAML instead of checking YAML the model wrote:
invalid output stops being *possible* rather than being something we catch
afterwards. It also removes three things that used to be done by hand and
could silently drift apart -- the frontmatter block, the sibling file, and
the `graph:`/`documents:` cross-reference that has to match in both
directions.

The vocabulary check matters because nothing else in the chain does it.
`build_graph.py` in intelica-brain-ia only rejects entities with no `id` and
incomplete relations -- an invented type like `SecurityGroup` (instead of
`Resource` with `resource_type: security_group`) sails through the PR, through
CI, and lands in graph.json, where `find_entity(entity_type="security_group")`
will never find it again.

Usage:
    python3 build_push_args.py <<'EOF'
    [
      {
        "title": "NAT Gateway cost spike",
        "domain": "aws",
        "account": "Portal-Prod",
        "category_raw": "Analisis de costos",
        "summary": "Por que el NAT Gateway de Portal-Prod subio 4x en julio.",
        "tags": ["nat-gateway", "costos", "factura"],
        "body": "## Resumen\n\n...",
        "entities": [
          {"type": "Resource", "id": "nat-0abc123", "resource_type": "nat_gateway"},
          {"type": "Account", "id": "Portal-Prod"}
        ],
        "relations": [
          {"from": "nat-0abc123", "type": "BELONGS_TO", "to": "Portal-Prod"}
        ],
        "commit_message": "docs: add NAT Gateway cost spike"
      }
    ]
    EOF

On success prints JSON on stdout, ready to pass straight to push_knowledge:
    {"new_branch_name": "...", "files": [{"path", "content", "commit_message"}, ...]}

On a validation error prints nothing on stdout and exits 1, so a broken draft
can never be pushed by accident. Fix what stderr reports and run it again.
"""

import json
import re
import secrets
import sys
import unicodedata
from datetime import datetime, timezone

# --- Vocabulario de KNOWLEDGE_MODEL.md -------------------------------------
# Fijo y curado a proposito: si algo no encaja, se modela con lo que hay o se
# extiende el modelo por PR -- no se inventa un tipo acá.

REQUIRED_FIELDS = {
    "Account": ("id",),
    "Resource": ("id", "resource_type"),
    "Finding": ("id", "finding_type"),
    "Decision": ("id", "title"),
    "Incident": ("id",),
    "Project": ("id",),
    "DatabaseServer": ("id", "engine"),
    "Database": ("id",),
    "WindowsServer": ("id",),
    "PatchReview": ("id", "date"),
}

# El conocimiento esta particionado por dominio; todo tema declara a cual
# pertenece, y eso decide en que carpeta de `inbox/` va.
DOMAINS = {"aws", "database", "windows"}

# `Document` existe en el modelo pero se deriva del archivo, no se declara.
DERIVED_ENTITY_TYPES = {"Document"}

RELATION_TYPES = {
    "BELONGS_TO",
    "HAS_SECURITY_GROUP",
    "IN_VPC",
    "IN_SUBNET",
    "ASSUMES_ROLE",
    "ENCRYPTED_BY",
    "ATTACHED_TO",
    "REGISTERED_ON",
    "AFFECTS",
    "MITIGATED_BY",
    "RELATED_TO",
    "HOSTS_DATABASE",
    "RUNS_ON",
    "REVIEWED_IN",
    "SAME_AS",
}

# `DOCUMENTED_IN` es automatica: la deriva el reconstructor del par
# .md/.graph.yaml, no se escribe a mano.
DERIVED_RELATION_TYPES = {"DOCUMENTED_IN"}

# No es cerrado: el modelo dice explicitamente que un servicio nuevo de AWS es
# un resource_type nuevo, no una entidad nueva. Sirve para cazar typos
# (`ec2-instance`, `EC2Instance`), no para bloquear lo que no este en la lista.
KNOWN_RESOURCE_TYPES = {
    "ec2_instance", "security_group", "vpc", "subnet", "s3_bucket", "lambda",
    "rds_instance", "iam_role", "kms_key", "load_balancer", "nat_gateway",
    "dynamodb_table", "ebs_volume", "ecr_repository", "eks_cluster",
    "route_table", "network_acl", "secret", "certificate", "sqs_queue",
    "sns_topic", "transit_gateway", "vpc_endpoint",
}

IP_LIKE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
SNAKE_CASE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")

# Metadatos de trabajo que agrega consolidate.py: sirven para curar, no son
# conocimiento, y no tienen que llegar al grafo.
WORKING_METADATA = {"seen_in"}


def slugify(title: str) -> str:
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "topic"


# --- Validacion -------------------------------------------------------------

def validate_topic(topic: dict, position: str, errors: list[str], warnings: list[str]) -> None:
    for field in ("title", "summary", "body"):
        if not str(topic.get(field) or "").strip():
            errors.append(f"{position}: falta `{field}`")

    domain = topic.get("domain")
    if domain not in DOMAINS:
        errors.append(
            f"{position}: `domain` tiene que ser uno de {', '.join(sorted(DOMAINS))}, "
            f"llego {domain!r}. El conocimiento esta particionado por dominio y decide "
            "en que carpeta de inbox/ se escribe."
        )

    # `account` es un concepto de AWS (una cuenta de la organizacion). Para
    # database/windows no siempre aplica -- se exige solo en `aws`, donde ya
    # es la convencion establecida de la carpeta por cuenta.
    if domain == "aws" and not str(topic.get("account") or "").strip():
        errors.append(f"{position}: falta `account` (dominio `aws`)")

    summary = str(topic.get("summary") or "")
    if "\n" in summary:
        errors.append(
            f"{position}: `summary` tiene salto de linea; va en una celda de tabla "
            "de INDEX.md y la rompe. Una sola linea."
        )

    if not topic.get("tags"):
        warnings.append(
            f"{position}: sin `tags`. Junto con `summary` son la unica senal para "
            "elegir este documento desde INDEX.md -- no hay busqueda semantica."
        )

    declared_ids = validate_entities(topic, position, errors, warnings)
    validate_relations(topic, position, declared_ids, errors, warnings)


def validate_entities(
    topic: dict, position: str, errors: list[str], warnings: list[str]
) -> set[str]:
    declared_ids: set[str] = set()
    seen_ids: set[str] = set()

    for index, entity in enumerate(topic.get("entities") or []):
        where = f"{position}, entidad #{index + 1}"

        if not isinstance(entity, dict):
            errors.append(f"{where}: tiene que ser un objeto, no {type(entity).__name__}")
            continue

        entity_type = entity.get("type")
        entity_id = entity.get("id")

        if entity_type == "Person":
            errors.append(
                f"{where}: `Person` no existe en el modelo, a proposito. Quien hizo o "
                "dijo algo no se modela en el grafo (privacidad); la autoria del PR ya "
                "queda en el propio PR."
            )
            continue

        if entity_type in DERIVED_ENTITY_TYPES:
            errors.append(
                f"{where}: `{entity_type}` no se declara a mano, se deriva del archivo "
                "que contiene el fragmento."
            )
            continue

        if entity_type not in REQUIRED_FIELDS:
            errors.append(
                f"{where}: tipo `{entity_type}` no existe en KNOWLEDGE_MODEL.md. "
                f"Validos: {', '.join(sorted(REQUIRED_FIELDS))}. Un recurso de AWS es "
                "`Resource` con `resource_type`, nunca un tipo propio."
            )
            continue

        missing = [f for f in REQUIRED_FIELDS[entity_type] if not entity.get(f)]
        if missing:
            errors.append(
                f"{where} (`{entity_id or 'sin id'}`): a `{entity_type}` le falta "
                f"{', '.join('`' + m + '`' for m in missing)}"
            )
            continue

        if entity_id in seen_ids:
            warnings.append(f"{where}: `{entity_id}` esta declarada dos veces, se unifica")
        seen_ids.add(entity_id)
        declared_ids.add(entity_id)

        if IP_LIKE.match(str(entity_id)):
            errors.append(
                f"{where}: `{entity_id}` es una IP. Los IDs tienen que ser estables "
                "entre curaciones y una IP cambia -- usar el ID real del recurso."
            )

        if entity_type == "Resource":
            resource_type = str(entity.get("resource_type"))
            if not SNAKE_CASE.match(resource_type):
                errors.append(
                    f"{where}: `resource_type: {resource_type}` tiene que ser "
                    "snake_case (`ec2_instance`, no `ec2-instance` ni `EC2Instance`)."
                )
            elif resource_type not in KNOWN_RESOURCE_TYPES:
                warnings.append(
                    f"{where}: `resource_type: {resource_type}` no se habia visto antes. "
                    "Si es un servicio nuevo esta bien; si es un typo, corregilo -- el "
                    "grafo no une dos escrituras distintas del mismo tipo."
                )

        # No se puede validar que la fecha sea la de inicio y no la de
        # deteccion -- eso es criterio. Pero si se puede exigir que este:
        # sin ella, el incidente queda fechado por cuando se documento, que
        # ya paso una vez y perdio cuatro dias de deteccion tardia.
        if entity_type == "Incident" and not entity.get("date"):
            warnings.append(
                f"{where} (`{entity_id}`): `Incident` sin `date`. El indice ordena y "
                "contesta \"cuando paso\" con ese campo. Recorda que es cuando EMPEZO, "
                "no cuando se detecto."
            )

    return declared_ids


def validate_relations(
    topic: dict,
    position: str,
    declared_ids: set[str],
    errors: list[str],
    warnings: list[str],
) -> None:
    for index, relation in enumerate(topic.get("relations") or []):
        where = f"{position}, relacion #{index + 1}"

        if not isinstance(relation, dict):
            errors.append(f"{where}: tiene que ser un objeto, no {type(relation).__name__}")
            continue

        source, rel_type, target = relation.get("from"), relation.get("type"), relation.get("to")

        if not source or not rel_type or not target:
            errors.append(f"{where}: necesita `from`, `type` y `to`; llego {relation}")
            continue

        if rel_type in DERIVED_RELATION_TYPES:
            errors.append(
                f"{where}: `{rel_type}` es automatica -- toda entidad del fragmento queda "
                "vinculada a su documento sola. No se declara."
            )
            continue

        if rel_type not in RELATION_TYPES:
            errors.append(
                f"{where}: relacion `{rel_type}` no existe en KNOWLEDGE_MODEL.md. "
                f"Validas: {', '.join(sorted(RELATION_TYPES))}."
            )
            continue

        # Apuntar a una entidad declarada en OTRO documento es legitimo y comun
        # (`BELONGS_TO Portal-Prod`, que vive en el inventario), asi que esto
        # avisa y no bloquea. Declararla igual acá hace el fragmento autonomo.
        for end, value in (("from", source), ("to", target)):
            if value not in declared_ids:
                warnings.append(
                    f"{where}: `{end}: {value}` no esta declarada en este documento. "
                    "Si vive en otro (una cuenta, un recurso del inventario) esta bien; "
                    "si no, la relacion va a quedar colgando en el grafo."
                )


# --- Serializacion YAML -----------------------------------------------------
# Minima y a mano: estos scripts corren con el python3 del sistema de cada uno,
# sin garantia de que PyYAML este instalado.

def yaml_scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)

    text = str(value)
    needs_quotes = (
        not text
        # Todo digitos entrecomillado o se lee como int: un account_id perderia
        # los ceros a la izquierda y dejaria de matchear como string.
        or text.isdigit()
        or text.lower() in {"true", "false", "null", "yes", "no", "on", "off", "~"}
        or text != text.strip()
        or text[0] in "-?:,[]{}#&*!|>'\"%@`"
        or ": " in text
        or " #" in text
        or "\n" in text
    )
    if needs_quotes:
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'
    return text


def yaml_inline_list(values) -> str:
    return "[" + ", ".join(yaml_scalar(v) for v in values) + "]"


def render_graph_file(topic: dict, md_filename: str) -> str:
    lines = [
        f"documents: {yaml_scalar(md_filename)}",
        f"domain: {yaml_scalar(topic['domain'])}",
    ]
    if topic.get("account"):
        lines.append(f"account: {yaml_scalar(topic['account'])}")

    entities = topic.get("entities") or []
    if entities:
        lines.append("entities:")
        for entity in entities:
            clean = {k: v for k, v in entity.items() if k not in WORKING_METADATA}
            # type/id primero y el resto ordenado: salida estable, para que dos
            # curaciones del mismo contenido den el mismo archivo.
            ordered = ["type", "id"] + sorted(k for k in clean if k not in ("type", "id"))
            first = True
            for key in ordered:
                if key not in clean:
                    continue
                prefix = "  - " if first else "    "
                lines.append(f"{prefix}{key}: {yaml_scalar(clean[key])}")
                first = False

    relations = topic.get("relations") or []
    if relations:
        lines.append("relations:")
        for relation in relations:
            lines.append(f"  - from: {yaml_scalar(relation['from'])}")
            lines.append(f"    type: {yaml_scalar(relation['type'])}")
            lines.append(f"    to: {yaml_scalar(relation['to'])}")

    return "\n".join(lines) + "\n"


def render_markdown(topic: dict, today: str, graph_filename: str) -> str:
    frontmatter = [
        "---",
        f"title: {yaml_scalar(topic['title'])}",
        f"domain: {yaml_scalar(topic['domain'])}",
    ]
    if topic.get("account"):
        frontmatter.append(f"account: {yaml_scalar(topic['account'])}")
    frontmatter += [
        f"category_raw: {yaml_scalar(topic.get('category_raw', ''))}",
        "category_confirmed: false",
        f"date: {today}",
        f"summary: {yaml_scalar(topic['summary'])}",
        f"tags: {yaml_inline_list(topic.get('tags') or [])}",
        f"graph: {yaml_scalar(graph_filename)}",
        "---",
        "",
        "",
    ]
    return "\n".join(frontmatter) + topic["body"].strip() + "\n"


# --- Main -------------------------------------------------------------------

def main() -> int:
    try:
        topics = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"La entrada no es JSON valido: {exc}", file=sys.stderr)
        return 1

    if not isinstance(topics, list) or not topics:
        print("Se esperaba una lista de temas, no vacia.", file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    for index, topic in enumerate(topics):
        if not isinstance(topic, dict):
            errors.append(f"tema #{index + 1}: tiene que ser un objeto")
            continue
        validate_topic(topic, f"tema #{index + 1} ({topic.get('title', 'sin titulo')})",
                       errors, warnings)

    for warning in warnings:
        print(f"  AVISO  {warning}", file=sys.stderr)

    if errors:
        print("", file=sys.stderr)
        for error in errors:
            print(f"  ERROR  {error}", file=sys.stderr)
        print(
            f"\n{len(errors)} error(es) contra KNOWLEDGE_MODEL.md. No se genero nada: "
            "corregi el borrador y volve a correr el script.",
            file=sys.stderr,
        )
        return 1

    today = datetime.now(timezone.utc).date().isoformat()
    suffix = secrets.token_hex(2)
    identifier = slugify(topics[0]["title"]) if len(topics) == 1 else f"multi-{len(topics)}"
    branch = f"docs/brain-{today}-{identifier}-{suffix}"

    files = []
    for topic in topics:
        slug = slugify(topic["title"])
        domain = topic["domain"]
        account = topic.get("account") or ""
        if account in ("N/A", "n/a"):
            account = ""

        md_filename = f"{today}-{slug}.md"
        graph_filename = f"{today}-{slug}.graph.yaml"
        # `aws` mantiene la convencion existente de una subcarpeta por cuenta
        # (inbox/aws/<Cuenta>/...). database/windows no tienen ese concepto
        # todavia, asi que van directo a inbox/<dominio>/ salvo que el tema
        # declare una cuenta igual.
        directory = f"inbox/{domain}/{account}" if account else f"inbox/{domain}"
        commit_message = topic.get("commit_message", f"docs: add {slug}")

        files.append(
            {
                "path": f"{directory}/{md_filename}",
                "content": render_markdown(topic, today, graph_filename),
                "commit_message": commit_message,
            }
        )
        if topic.get("entities") or topic.get("relations"):
            files.append(
                {
                    "path": f"{directory}/{graph_filename}",
                    "content": render_graph_file(topic, md_filename),
                    "commit_message": commit_message,
                }
            )

    json.dump({"new_branch_name": branch, "files": files}, sys.stdout, ensure_ascii=False)
    print(f"\nOK: {len(files)} archivo(s) generado(s) para {len(topics)} tema(s).",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
