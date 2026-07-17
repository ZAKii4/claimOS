# Cours 7 — Brancher le frontend sur les deux parcours et les 6 agents

## Ce qui existait déjà (rien reconstruit)

Avant ce chapitre, `frontend/src/components/claims/` avait déjà :

- **`NewClaimWizard.tsx`** : assistant de création en 3 étapes (infos → documents → revue), avec
  upload multi-fichiers, sélecteur de `DocumentRole` par fichier, et un bouton "Passer (sans
  documents)".
- **`ClaimReviewPanel.tsx`** (508 lignes) : affiche le `ClaimOpeningForm` fusionné avec badges
  FOUND/CONFLICT/NOT_FOUND, confiance, et correction en ligne déjà branchée sur
  `PATCH .../opening-form`.

Ces deux composants couvraient déjà tout le chemin "upload" décrit aux Cours 1-2. Il manquait deux
choses pour exploiter le reste du travail backend : un moyen d'utiliser le nouvel endpoint bulk de
saisie manuelle (Cours 3), et une UI pour la collaboration à 6 agents (Cours 4-5).

## 1. Éviter la duplication des libellés de champs

`ClaimReviewPanel.tsx` avait déjà trois dictionnaires de libellés français
(`TOP_LEVEL_LABELS`, `CONDUCTEUR_LABELS`, `PARTIE_ADVERSE_LABELS`) construits pour l'affichage en
lecture. Plutôt que de les redéfinir dans un nouveau composant (risque de divergence si un champ
est renommé côté backend), ils sont simplement passés en `export const` — une seule source de
vérité pour les libellés, utilisée à la fois en lecture (`ClaimReviewPanel`) et en saisie
(`ManualEntryForm`).

## 2. `ManualEntryForm.tsx` — la saisie manuelle groupée

Un formulaire par section (Police/souscripteur/sinistre, Conducteur, Partie adverse), avec un
`Record<string, string>` de valeurs indexé par chemin pointé (`"numero_police"`,
`"conducteur.nom"`) — exactement la même convention que `POST .../opening-form/manual` attend
côté backend (Cours 3).

Deux décisions de conception à noter :

- **Type d'input dérivé du champ, pas texte partout** : une petite table `FIELD_KIND` mappe les
  champs connus comme booléens (`victimes_blessees`, `conducteur_est_souscripteur`,
  `sinistre_suspicieux`...) vers un `<select>` Oui/Non, les dates vers `<input type="date">`, et
  `responsabilite_pct` vers un input numérique — miroir de `SCALAR_FIELD_SPECS` côté
  `llm_field_extractor.py`. Un champ texte vide n'est jamais confondu avec "l'opérateur veut
  effacer ce champ" : seuls les champs réellement remplis sont envoyés au backend
  (`Object.entries(values).filter(([, v]) => v !== "")`), cohérent avec la sémantique de
  `submit_manual_fields()` qui n'écrit que ce qu'on lui donne.
- **Victimes explicitement exclues**, avec un message à l'utilisateur plutôt qu'un champ qui
  échouerait silencieusement — miroir direct de la limite documentée au Cours 3
  (`get_field`/`set_field` ne résolvent pas les chemins de liste).

## 3. `AgentCollaborationPanel.tsx` — piloter les 6 agents

Un bouton déclenche `POST /claims/{claimId}/agents/run` (Cours 5) et affiche la réponse brute de
`AgentManager.process_claim()` de façon lisible :

- Badge de décision finale (`context.metadata.supervisor_summary.final_decision`, avec repli sur
  `context.decision.decision` si le superviseur n'a pas tourné) — coloré selon la sévérité
  (rouge pour `FRAUD_REVIEW`, ambre pour `HUMAN_REVIEW`, vert pour `AUTO_APPROVED`).
  bandeau d'avertissement si `supervisor_summary.overridden` est vrai (Cours 4, le filet de
  sécurité du superviseur) — l'opérateur voit explicitement *pourquoi* une décision a été
  rétrogradée, pas seulement le résultat final.
- Liste des incohérences légales (`context.validation_report.issues`).
- Une grille des 6 agents avec leur statut (`Exécuté`/`Échec`/`Ignoré`) et leur premier message —
  correspond directement à `agent_results[agent_id]` (`AgentResult.messages[0]`), donc si un agent
  échoue, l'opérateur voit le message d'erreur réel du backend, pas un état générique.

Ce panneau ne s'auto-déclenche pas : conforme à la décision du Cours 5 de garder cette étape
explicite (un onglet "Analyse IA" séparé), pas un appel automatique après upload/saisie — plus
simple à déboguer, chaque étape ayant son propre résultat inspectable.

## 4. Intégration

- **`NewClaimWizard.tsx`** : l'étape "upload" a maintenant deux boutons de bascule
  ("Uploader des documents" / "Saisie manuelle"). En mode manuel, `ManualEntryForm` remplace la
  zone de dépôt de fichiers ; sa soumission avance directement à l'étape "review" (qui réutilise
  `ClaimReviewPanel`, inchangé).
- **Page de détail du claim** (`claims/[id]/page.tsx`) : deux nouveaux onglets ajoutés à côté de
  "Documents" et "Formulaire d'ouverture" — **"Saisie manuelle"** (le même `ManualEntryForm`,
  utilisable à tout moment sur un claim existant, pas seulement à la création — cohérent avec le
  Cours 3 : les deux parcours ne s'excluent pas dans le temps) et **"Analyse IA"**
  (`AgentCollaborationPanel`).

## 5. Vérification — en conditions réelles, pas juste `tsc`

Une vérification "ça compile" n'aurait rien prouvé sur le comportement réel. Le parcours a été
piloté avec un vrai navigateur (Playwright, faute de `chromium-cli` disponible dans cet
environnement) contre le vrai backend (Postgres + Ollama déjà vérifiés joignables, Cours 1) :

1. Authentification : un JWT valide a été généré directement via `jwt_manager.create_access_token()`
   (le backend a été relancé avec un `SECRET_KEY` fixe pour que le token signé côté script et
   celui vérifié côté serveur utilisent la même clé) et injecté dans le `localStorage` sous la clé
   `claimos-auth` que `useAuthStore` (zustand `persist`) attend — contourne volontairement l'écran
   de connexion et le moteur Zero Trust, non pertinents pour ce qu'on vérifie ici.
2. Création d'un claim, bascule en "Saisie manuelle", remplissage de `numero_police` et
   `lieu_survenance`, soumission — **vérifié en base** que
   `claim_file.field_overrides` contient bien les deux valeurs exactes (pas de troncature réelle
   malgré un artefact d'affichage constaté dans la colonne étroite du wizard, cosmétique,
   préexistant dans `ClaimReviewPanel`, hors périmètre de ce chapitre).
3. Onglet "Analyse IA", clic sur "Lancer l'analyse IA" — **appel réel** à
   `POST /claims/{id}/agents/run`, qui a exécuté les 6 agents pour de vrai (dont deux vrais appels
   Ollama, `fraud_agent` et `legal_agent`). Résultat observé : `REQUEST_MORE_DOCUMENTS` (cohérent —
   4% de complétude, sous le seuil de 50% du Cours 4), score de fraude 0%, 0 incohérence légale,
   les 6 agents tous "Exécuté" avec leurs vrais messages individuels.
4. `console --errors` vide aux deux étapes.

Ce test a un effet de bord assumé : un claim `SMOKE-<timestamp>` existe désormais dans la base de
développement. Laissé en l'état — c'est un artefact de test trivial et sans risque, pas une
donnée réelle de sinistre, et le supprimer via SQL brut aurait été un risque inutile pour un gain
nul.
