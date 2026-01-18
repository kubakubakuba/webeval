# Manual Setup

For testing, start the testing environment

```bash
./scripts/testing_environment.sh
```

this will set up Debian Trixie which you can then try the setup inside of (with the webeval already copied over)

# Setup

```bash
git clone https://gitlab.fel.cvut.cz/b35apo/qtrvsim-eval-web /opt/qtrvsim-eval-web
cd /opt/qtrvsim-eval-web
```

```bash
cd scripts
chmod +x *.sh
cp ../.env.example ../.env
```

```bash
./install_requirements.sh
source ~/.local/bin/env
```

```bash
./setup_psql.sh
```

```bash
./create_database.sh
```

(optional)
```bash
./import_data.sh ../docker/webeval_sample_data.sql
```

```bash
./setup_services.sh
```

```bash
./setup_wiki.sh
```

```bash
./setup_apache2.sh
```



