# PiyasaPilot Secrets

This document lists the secrets required for the GitHub Actions CI/CD pipeline and the production environment.
**DO NOT** store actual secret values in this file or any version-controlled file.

## GitHub Actions Secrets (Repository Secrets)

The following secrets must be configured in the GitHub repository settings (Settings > Secrets and variables > Actions):

*   `EC2_HOST`: The public IP address or domain name of the production EC2 instance.
*   `EC2_USER`: The SSH username for the EC2 instance (e.g., `ubuntu`).
*   `EC2_SSH_KEY`: The private SSH key used to authenticate with the EC2 instance.
*   `STRIPE_SECRET_KEY`: The Stripe secret API key for billing integration.
*   `STRIPE_WEBHOOK_SECRET`: The Stripe webhook secret for verifying event signatures.
*   `SENTRY_DSN`: The Sentry Data Source Name for error tracking and performance monitoring.

## .env File Variables

The variables above (along with other configuration options) should be placed in the `/opt/piyasapilot/.env` file on the production server. See `.env.example` in the repository root for a complete list of required environment variables.
