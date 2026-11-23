# ft_transcendence

## Web
- [x] Major module: Use a Framework as backend.
- [x] Minor module: Use a front-end framework or toolkit.
- [x] Minor module: Use a database for the backend.
- [ ] Major module: Store the score of a tournament in the Blockchain.
## User Management
- [x] Major module: Standard user management, authentication, users across tournaments.
- [x] Major module: Implementing a remote authentication.
Gameplay and user experience
- [x] Major module: Remote players
- [ ] Major module: Multiplayers (more than 2 in the same game).
- [ ] Major module: Add Another Game with User History and Matchmaking.
- [ ] Minor module: Game Customization Options.
- [x] Major module: Live chat.
## AI-Algo
- [x] Major module: Introduce an AI Opponent.
- [ ] Minor module: User and Game Stats Dashboards
## Cybersecurity
- [ ] Major module: Implement WAF/ModSecurity with Hardened Configuration and HashiCorp Vault for Secrets Management.
- [ ] Minor module: GDPR Compliance Options with User Anonymization, Local Data Management, and Account Deletion.
- [x] Major module: Implement Two-Factor Authentication (2FA) and JWT.
## Devops
- [ ] Major module: Infrastructure Setup for Log Management.
- [ ] Minor module: Monitoring system.
- [ ] Major module: Designing the Backend as Microservices.
## Graphics
- [x] Major module: Use of advanced 3D techniques.
## Accessibility
- [x] Minor module: Support on all devices.
- [x] Minor module: Expanding Browser Compatibility.
- [ ] Minor module: Multiple language supports.
- [ ] Minor module: Add accessibility for Visually Impaired Users.
- [ ] Minor module: Server-Side Rendering (SSR) Integration.
## Server-Side Pong
- [x] Major module: Replacing Basic Pong with Server-Side Pong and Implementing an API.
- [ ] Major module: Enabling Pong Gameplay via CLI against Web Users with API Integration.
## Running locally

1. `cp backend/backend/.env.example backend/backend/.env` and fill it in. `DJANGO_SECRET_KEY` and `JWT_SECRET` are required.
2. Start the backend stack first (it creates the shared network): `docker compose -f backend/docker-compose.yml up --build`
3. Start the frontend: `docker compose -f frontend/docker-compose.yml up --build`
4. Open https://localhost:1337. nginx serves the frontend, `/api`, `/ws` and `/avatars` on this one origin.

Adminer (8080), Grafana (3000), Prometheus (9090) and the Django port (8000) are bound to 127.0.0.1 only.

## Tests

```bash
docker run -d --rm --name pong3d-test-pg -p 127.0.0.1:55432:5432 \
  -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test postgres:16-alpine
cd backend/backend
DJANGO_SETTINGS_MODULE=ft_transcendence.test_settings python manage.py test
```
