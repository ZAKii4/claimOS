# Zero Trust & Session Management

L'approche Zero Trust suppose que le réseau interne n'est pas plus fiable qu'Internet.

## Risk Score
- Chaque connexion est évaluée.
- Connexion via un nouvel appareil = +40 points de risque.
- Connexion via une IP non reconnue/anormale = +50 points de risque.
- Si le score dépasse 80, l'utilisateur passe en statut "mfa_required" immédiatement après vérification du mot de passe.

## Multi-Factor Authentication (TOTP)
Les secrets TOTP sont générés via `pyotp`. L'utilisateur peut scanner l'URI via Google Authenticator ou Authy. Le MFA est requis pour valider les tokens d'accès sur des sessions à haut risque.
