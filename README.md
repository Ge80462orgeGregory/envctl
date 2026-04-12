# envctl

A CLI tool for managing and syncing environment variable sets across local, staging, and production configs.

---

## Installation

```bash
pip install envctl
```

Or install from source:

```bash
git clone https://github.com/yourname/envctl.git && cd envctl && pip install .
```

---

## Usage

```bash
# Initialize envctl in your project
envctl init

# Add an environment variable to a config
envctl set DATABASE_URL "postgres://localhost/mydb" --env local

# List all variables for an environment
envctl list --env staging

# Sync variables from local to staging
envctl sync --from local --to staging

# Pull config into a .env file
envctl export --env production --output .env
```

envctl stores configs in a `.envctl/` directory at your project root. Each environment (local, staging, production) is tracked separately, making it easy to diff and promote changes across environments.

---

## Configuration

envctl looks for a `.envctl/config.yaml` file in your project root. Run `envctl init` to generate one automatically.

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any major changes.

---

## License

[MIT](LICENSE)