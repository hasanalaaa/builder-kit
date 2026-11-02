#!/usr/bin/env python3
"""schema_check: scan SQL migrations and Prisma schemas for data-model and migration-safety defects.

Usage: schema_check.py [root]
Reads every *.sql file (in path order = migration order) and every schema.prisma under root.
Each finding: LEVEL rule location  message. Exit 1 on any ERROR.
Silence one statement with a comment "schema-check: ignore" inside it.
"""
import argparse
import collections
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", "vendor", ".venv", "venv", "__pycache__", "coverage"}
MONEY = re.compile(r"(price|amount|total|balance|cost|fee|salary|subtotal|tax|payout|refund)", re.I)
FLOAT = re.compile(r"\b(float\d?|real|double precision|double)\b", re.I)
NAIVE_TS = re.compile(r"\btimestamp\b(?!tz)(?!\s*(\(\d\))?\s+with\s+time\s+zone)", re.I)
CREATED = re.compile(r"^\s*\"?(created_at|inserted_at|created|createdat)\"?\s", re.I)
CREATE_TABLE = re.compile(r"create\s+table\s+(?:if\s+not\s+exists\s+)?([\w.\"]+)\s*\((.*)\)", re.I | re.S)
CREATE_INDEX = re.compile(r"create\s+(unique\s+)?index\s+(concurrently\s+)?(?:if\s+not\s+exists\s+)?[\w\"]*\s*on\s+(?:only\s+)?([\w.\"]+)\s*(?:using\s+\w+\s*)?\(([^)]*)\)", re.I)
ALTER = re.compile(r"alter\s+table\s+(?:if\s+exists\s+)?(?:only\s+)?([\w.\"]+)\s+(.*)", re.I | re.S)
REF = re.compile(r"\breferences\s+([\w.\"]+)", re.I)


def norm(name):
    return name.replace('"', "").split(".")[-1].lower()


def split_top(body):
    parts, depth, cur = [], 0, ""
    for ch in body:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    return parts + ([cur.strip()] if cur.strip() else [])


def statements(sql):
    sql = re.sub(r"\$(\w*)\$.*?\$\1\$", "''", sql, flags=re.S)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    keep = [l if "schema-check: ignore" in l else re.sub(r"--.*", "", l) for l in sql.splitlines()]
    return [s.strip() for s in "\n".join(keep).split(";") if s.strip()]


class Model:
    def __init__(self):
        self.created_in = {}
        self.indexed = collections.defaultdict(set)
        self.fks = []
        self.findings = []

    def add(self, level, rule, where, msg):
        self.findings.append((level, rule, where, msg))


def column_checks(m, table, cols, where):
    has_pk = has_created = False
    for c in cols:
        low = c.lower()
        if low.startswith(("primary key", "constraint")) and "primary key" in low:
            has_pk = True
            first = re.search(r"primary key\s*\(\s*\"?(\w+)", low)
            if first:
                m.indexed[table].add(first.group(1))
            continue
        if low.startswith(("unique", "constraint")) and "unique" in low:
            first = re.search(r"unique\s*\(\s*\"?(\w+)", low)
            if first:
                m.indexed[table].add(first.group(1))
        fk = re.match(r"(?:constraint\s+\w+\s+)?foreign\s+key\s*\(\s*\"?(\w+)", low)
        if fk:
            m.fks.append((table, fk.group(1), "on delete" in low, where))
            continue
        if low.startswith(("check", "constraint", "exclude", "like")):
            continue
        name = re.match(r"\"?(\w+)\"?", c)
        if not name:
            continue
        col = name.group(1).lower()
        if "primary key" in low:
            has_pk = True
            m.indexed[table].add(col)
        if re.search(r"\bunique\b", low):
            m.indexed[table].add(col)
        if CREATED.match(c):
            has_created = True
        if MONEY.search(col) and FLOAT.search(low):
            m.add("ERROR", "money-float", where, f"{table}.{col} stores money as floating point: use bigint cents or numeric")
        if NAIVE_TS.search(low):
            m.add("WARN", "naive-timestamp", where, f"{table}.{col} is timestamp without time zone: use timestamptz")
        if REF.search(low):
            m.fks.append((table, col, "on delete" in low, where))
    return has_pk, has_created


def check_sql(m, rel, sql, file_no):
    for stmt in statements(sql):
        if "schema-check: ignore" in stmt:
            continue
        where = f"{rel}: {stmt.splitlines()[0][:70]}"
        ct = CREATE_TABLE.search(stmt)
        if ct and re.match(r"\s*create\s+table", stmt, re.I):
            table = norm(ct.group(1))
            m.created_in.setdefault(table, file_no)
            has_pk, has_created = column_checks(m, table, split_top(ct.group(2)), where)
            if not has_pk:
                m.add("ERROR", "table-no-pk", where, f"table {table} has no primary key")
            if not has_created:
                m.add("WARN", "no-created-at", where, f"table {table} has no created_at timestamptz")
            continue
        ci = CREATE_INDEX.search(stmt)
        if ci:
            table = norm(ci.group(3))
            first = re.match(r"\s*\"?(\w+)", ci.group(4))
            if first:
                m.indexed[table].add(first.group(1).lower())
            if not ci.group(2) and m.created_in.get(table, file_no) < file_no:
                m.add("WARN", "index-not-concurrent", where, f"index on existing table {table}: use CREATE INDEX CONCURRENTLY on large tables")
            continue
        al = ALTER.search(stmt)
        if al:
            alter_checks(m, norm(al.group(1)), al.group(2), where, file_no)


def alter_checks(m, table, rest, where, file_no):
    low = rest.lower()
    existing = m.created_in.get(table, -1) < file_no
    for clause in split_top(rest):
        cl = clause.lower()
        if cl.startswith("add column") or (cl.startswith("add ") and not cl.startswith(("add constraint", "add primary", "add unique", "add foreign"))):
            if "not null" in cl and "default" not in cl and existing:
                m.add("ERROR", "not-null-no-default", where, f"adding NOT NULL column without DEFAULT to existing table {table} fails on existing rows")
            col = re.match(r"add\s+(?:column\s+)?(?:if\s+not\s+exists\s+)?\"?(\w+)", cl)
            if col and MONEY.search(col.group(1)) and FLOAT.search(cl):
                m.add("ERROR", "money-float", where, f"{table}.{col.group(1)} stores money as floating point")
            if col and NAIVE_TS.search(cl):
                m.add("WARN", "naive-timestamp", where, f"{table}.{col.group(1)} is timestamp without time zone")
            if col and REF.search(cl):
                m.fks.append((table, col.group(1), "on delete" in cl, where))
        fk = re.search(r"foreign\s+key\s*\(\s*\"?(\w+)", cl)
        if fk:
            m.fks.append((table, fk.group(1), "on delete" in cl, where))
            if existing and "not valid" not in low:
                m.add("WARN", "fk-not-valid", where, f"FK on existing table {table}: add NOT VALID then VALIDATE CONSTRAINT to avoid a long lock")
    if re.search(r"\bdrop\s+column\b|\brename\s+(column\s+)?\w+\s+to\b|\balter\s+column\s+\"?\w+\"?\s+(set\s+data\s+)?type\b", low):
        m.add("WARN", "breaking-change", where, f"breaking change on {table}: use expand → migrate → contract (migrations-and-queries.md §2)")


def check_drops(m, rel, sql):
    for stmt in statements(sql):
        if re.match(r"\s*drop\s+table", stmt, re.I) and "schema-check: ignore" not in stmt:
            m.add("WARN", "drop-table", f"{rel}: {stmt[:70]}", "DROP TABLE: confirm backup, stop code use first, archive if retention requires")


def check_prisma(m, rel, text):
    postgres = re.search(r"provider\s*=\s*\"postgres(ql)?\"", text) is not None
    for name, body in re.findall(r"model\s+(\w+)\s*\{(.*?)\n\}", text, re.S):
        where = f"{rel}: model {name}"
        has_id = "@id" in body or "@@id" in body
        indexed = set()
        for grp in re.findall(r"@@(?:index|unique|id)\(\s*(?:fields:\s*)?\[\s*(\w+)", body):
            indexed.add(grp)
        fields = {}
        for line in body.splitlines():
            f = re.match(r"\s*(\w+)\s+(\w+)(\[\])?(\?)?\s*(.*)", line)
            if not f or line.strip().startswith(("//", "@@")):
                continue
            fname, ftype, attrs = f.group(1), f.group(2), f.group(5)
            fields[fname] = (ftype, attrs)
            if "@unique" in attrs or "@id" in attrs:
                indexed.add(fname)
            if MONEY.search(fname) and ftype == "Float":
                m.add("ERROR", "money-float", where, f"{name}.{fname} is Float: use Int (cents) or Decimal")
            if ftype == "DateTime" and postgres and "Timestamptz" not in attrs:
                m.add("WARN", "naive-timestamp", where, f"{name}.{fname} DateTime maps to timestamp without tz: add @db.Timestamptz(3)")
            for fk in re.findall(r"@relation\([^)]*fields:\s*\[\s*(\w+)", attrs):
                if fk not in indexed:
                    m.fks.append((name.lower(), fk.lower(), True, where))
        for fk_table, fk_col, _, w in [x for x in m.fks if x[0] == name.lower()]:
            if fk_col in {i.lower() for i in indexed}:
                m.indexed[name.lower()].add(fk_col)
        if not has_id:
            m.add("ERROR", "table-no-pk", where, f"model {name} has no @id / @@id")
        if not any(k.lower() in ("createdat", "created_at", "insertedat") for k in fields):
            m.add("WARN", "no-created-at", where, f"model {name} has no createdAt")


def finish(m):
    seen = set()
    for table, col, has_on_delete, where in m.fks:
        if (table, col) in seen:
            continue
        seen.add((table, col))
        if col not in m.indexed.get(table, set()):
            m.add("WARN", "fk-no-index", where, f"foreign key {table}.{col} has no index (Postgres does not create one)")
        if not has_on_delete and "model" not in where:
            m.add("WARN", "fk-no-on-delete", where, f"foreign key {table}.{col} has no ON DELETE rule: decide cascade / restrict / set null")


def collect(root):
    files = bk.walk(root, (".sql", ".prisma"), IGNORE_DIRS, dot_dirs=True)  # honors .gitignore (worktree copies, build output)
    return [f for f in files if f.endswith(".sql")], [f for f in files if f.endswith(".prisma")]


def run(root):
    m = Model()
    sql, prisma = collect(root)
    for i, rel in enumerate(sql):
        with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
            text = f.read()
        check_sql(m, rel, text, i)
        check_drops(m, rel, text)
    for rel in prisma:
        with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
            check_prisma(m, rel, f.read())
    finish(m)
    return m.findings, len(sql), len(prisma)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    a = p.parse_args()
    findings, n_sql, n_prisma = run(a.root)
    return bk.report(findings, "schema_check", a.root, note=f" ({n_sql} SQL files, {n_prisma} Prisma files)")


if __name__ == "__main__":
    sys.exit(main())
