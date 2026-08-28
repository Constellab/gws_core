---
name: query-lab-db
description: Read a Constellab lab's databases over MCP — list the brick databases, inspect their tables, and run read-only SQL with gws_core_db_list and gws_core_db_query. Use when asked what is stored in the lab, to count or find rows, or to inspect a brick's schema.
---

# Reading a Constellab lab's databases

Two tools, both read-only:

| | |
|---|---|
| `gws_core_db_list` | the databases this lab has, one per installed brick |
| `gws_core_db_query` | one read-only SQL statement against one of them |

Every lab brick owns a database named after it. `gws_core` holds the platform's own
tables (users, scenarios, resources, tags, notes); every other brick holds its own.

## Work from the schema, never from a guess

Table and column names are not guessable — they carry brick-specific prefixes and the
schema moves between brick versions. Read it first, in three steps:

```
gws_core_db_list()
gws_core_db_query(sql="SHOW TABLES", db="gws_core")
gws_core_db_query(sql="DESCRIBE gws_scenario", db="gws_core")
gws_core_db_query(sql="SELECT title, status FROM gws_scenario ORDER BY last_modified_at DESC", db="gws_core")
```

Skipping `DESCRIBE` costs a round trip to an error every time the column you assumed is
named something else.

## What the tools accept

- **One statement per call.** No `;` separators.
- **`SELECT` / `SHOW` / `EXPLAIN` / `DESCRIBE` / `WITH` only.** Anything that would write
  is rejected before it runs, and the query itself runs in a transaction that is always
  rolled back. You cannot damage the lab with these tools, so you do not need to ask
  before reading.
- **`db` defaults to `gws_core`.** Pass a brick name for anything else.
- **`limit` defaults to 20 rows**, `0` for no limit. It protects your context, not the
  lab: the result says `truncated` when rows were dropped, and `row_count` counts what
  you received, not what matched.

Prefer a narrow `SELECT` over `SELECT *` on a wide table, and aggregate in SQL
(`COUNT`, `GROUP BY`) rather than pulling rows to count them yourself.

## Errors

An error comes back as a readable message with the next action in it — an unknown
column, an unknown database, a rejected statement. Read it and correct the query; a
failed call has changed nothing.

## What this does not do

These tools read the database directly. They do not run scenarios, create resources or
modify anything — that is what the lab's own interface and its brick tools are for. And
a lab user sees, through these tools, exactly what they could already read through the
`gws db` command line: no more, no less.
