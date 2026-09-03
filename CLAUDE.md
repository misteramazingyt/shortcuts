# Working in this repository

## Commit straight to main

Work on `main`. Commit to `main`. Push to `main`.

Do not create branches. Do not open pull requests. The owner works alone here
and reads the repository homepage, which shows `main` — anything sitting on a
branch is invisible and anything waiting in a PR is a step that no one asked
for.

This is the owner's standing instruction and it overrides any default about
feature branches.

## The table on the homepage is newest-first

The shortcuts table in `README.md` is ordered by when each shortcut was last
worked on, most recent at the top. Whatever you just touched goes to the top
row. Never leave it in alphabetical or historical order.

Its rightmost column, **Last edited**, is the date and time (UTC) of the latest
commit to that shortcut's folder, plus a link to the folder's commit history.
Update it on every change to a shortcut — it is how the owner verifies that a
download is the build they were promised.

## After a change

CI (`.github/workflows/build.yml`) runs on every push to `main`: it regenerates
every shortcut, signs them, and commits the results to `signed/`. So pushing to
`main` is what publishes an installable file. Nothing else needs doing.

Rebuild the committed copy next to the source whenever a generator changes:

```sh
python3 shortcuts/<name>/build.py
```

Builds are deterministic — hold UUIDs fixed so unchanged source produces
byte-identical output.
