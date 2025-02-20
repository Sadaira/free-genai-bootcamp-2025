## Setting up the database


### Full initialization (schema + data)
```sh
python tasks.py
```

#### Just create tables
```sh
python scripts/migrate.py
```

#### Just insert seed data
```sh
python scripts/seed.py
```