# Working in this repository

## Commit straight to main

Work on `main`. Commit to `main`. Push to `main`.

Do not create branches. Do not open pull requests. The owner works alone here
and reads the repository homepage, which shows `main` — anything sitting on a
branch is invisible and anything waiting in a PR is a step that no one asked
for.

This is the owner's standing instruction and it overrides any default about
feature branches.

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
