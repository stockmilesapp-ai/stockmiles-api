# Seeds

Data the app needs that is not created through the API. Each seed has a JSON file (the data) and a loader (the command that makes the database match it).

Loaders run against the database in `DATABASE_URL` (in `.env`), so they change Supabase when run from a normal checkout. Run migrations first (`uv run alembic upgrade head`).

Every loader can be run any number of times: it inserts what is new, updates what changed, and leaves the database matching the file.

## Platform members

StockMiles staff who can use the platform screens. This file is the only way to add them; there is no API or UI for it.

| File | Purpose |
|---|---|
| `platform_members.json` | The list: `email`, `role` (`platform_admin`), `tenantScope` (`all` or `assigned`) |
| `load_platform_members.py` | The loader |

```bash
uv run python -m app.seeds.load_platform_members
```

What it does:

- Adds each listed email, or updates its role and scope.
- Sets the status to `invited` until that person first signs in with Google using the email, then `active`.
- Sets `disabled` on members who are no longer in the file. They are not deleted, so the member access links they created keep their author.

To remove someone's access, delete their entry from the file and run the command again. To add someone, add an entry and run it.
