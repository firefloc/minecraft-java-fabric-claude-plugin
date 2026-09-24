# Portage Codex et Hermes — plan d'implémentation

> Pour l'agent externe : utiliser le skill Superpowers writing-plans comme contrat de travail, puis executing-plans tâche par tâche. Cocher les étapes seulement après exécution et conserver les preuves des commandes. Lire la spec liée avant toute modification.

**But :** rendre la suite complète de 30 skills utilisable depuis Claude Code, Codex et Hermes sans dupliquer le workflow ni fixer la version de Minecraft.

**Architecture :** un noyau partagé skills/, reference/, tools/ ; de minces adaptations hôte pour découvrir les skills, connecter les deux MCP et résoudre chemins et noms d'outils. Hermes charge directement skills/ via external_dirs. Les helpers Python gardent les variables d'environnement comme source commune des endpoints et jetons.

**Technologies :** Markdown/YAML frontmatter, Node.js 20, Python 3.10+, pytest, MCP Streamable HTTP, Codex plugin manifest, Hermes Agent v0.21.4 constaté localement.

**Spec :** docs/superpowers/specs/2026-09-24-codex-hermes-portage-design.md

## Contraintes globales

- Conserver les 30 noms de skills et les deux noms de serveurs minecraft-java / minecraft-java-client.
- Conserver les noms d'outils Java natifs, le workflow et ses portes de validation.
- Garder les champs Claude model/context quand requis ; ils ne déterminent pas le modèle Codex/Hermes.
- Aucun arbre de skills copié, proxy MCP, parseur YAML ajouté, ni choix de version Minecraft.
- Ne jamais committer jeton, config utilisateur ou capture privée du monde.
- Ne pas déclarer un essai en jeu réussi sur la seule base des validateurs statiques.

## Fichiers et frontières

| Unité | Fichiers responsables |
| --- | --- |
| Contrat portable | reference/runtime-portability.md ; skills/minecraft-builder/SKILL.md ; skills/minecraft-mcp-setup/SKILL.md |
| Connexion Hermes | Nouveau reference/mcp/hermes-connection.md ; skills/setup-connect/SKILL.md ; README.md |
| Corpus partagé | Les 23 skills repérés par la commande d'inventaire de la tâche 3 et leurs fichiers reference/ associés |
| Interactions et outils | Neuf fichiers repérés par la tâche 4 ; reference/execution/engine-limits.md ; skills/exec-inspect/SKILL.md |
| Contrôle automatique | scripts/validate-plugin.mjs ; éventuellement un test Node minimal de régression ; .github/workflows/ci.yml |
| Documentation de maintien | AGENTS.md ; CONTRIBUTING.md ; skills/TAXONOMY.md si une règle de portée change |

Ne modifier tools/mcp_config.py que si les essais prouvent que sa priorité environnement → configs existantes → défaut ne suffit pas. Les tests actuels tools/builder/tests/test_mcp_config.py couvrent déjà l'URL et le jeton fournis par l'environnement.

## Points de revue obligatoires

1. Un checkout dont le chemin contient des espaces et un shell lancé hors du checkout n'exécutent jamais un chemin Claude littéral.
2. Hermes découvre mcp__minecraft_java__server_get_status et mcp__minecraft_java_client__view_capture, malgré les tirets dans les noms de serveurs.
3. L'absence de client rendu conserve le build utilisable mais le rapport annonce « inspection serveur seulement ».
4. URL et jeton distants restent identiques entre l'hôte et les helpers ; aucun jeton n'apparaît dans Git, la ligne de commande imprimée ni le log de validation.
5. Si AskUserQuestion ou la délégation native n'existe pas, la clarification passe par l'interface active et les étapes restent séquentielles sans supprimer de porte.

## Préparation : établir la base

- [ ] Lire AGENTS.md, la spec et reference/orchestration/workflow-spine.md ; noter le SHA de départ. Ne pas supposer que le manifeste Codex signifie portage complet.
- [ ] Exécuter node scripts/validate-plugin.mjs et python -m pytest tools/builder/tests tools/terrain/tests tools/voxel/tests. Noter erreurs déjà présentes avant toute édition.
- [ ] Exécuter le validateur Codex installé localement : python /home/firefloc/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py . Si cet outil n'existe pas sur la machine de l'agent, signaler « non exécuté ».
- [ ] Vérifier la config Hermes réelle avec hermes --version, hermes skills --help et sa documentation locale ; ne pas déduire une syntaxe d'un autre Hermes.

### Tâche 1 — Contrat de noms et de chemins entre hôtes

**Fichiers :** modifier reference/runtime-portability.md, skills/minecraft-builder/SKILL.md, skills/minecraft-mcp-setup/SKILL.md.

**Entrée :** deux serveurs et leurs noms d'outils Java. **Sortie :** règle unique pour résoudre un outil et la racine du plugin, réutilisée dans les tâches 2–4.

- [ ] Documenter une table Claude / Codex / Hermes avec : racine du plugin ; nom préfixé de server_get_status ; nom préfixé de view_capture ; manière de poser une question ; comportement sans sous-agent. Pour Hermes, le préfixe attendu est mcp__minecraft_java__ et mcp__minecraft_java_client__ ; la découverte effective de l'hôte reste l'autorité.
- [ ] Dans les deux skills d'entrée, remplacer les instructions exclusivement Codex par le contrat neutre et pointer vers le guide de connexion propre à l'hôte. Conserver le déroulé actuel et les noms des deux serveurs.
- [ ] Vérifier que les quatre orchestrateurs build-* conduisent toujours à la même chaîne de portes. Contrôle : rg -n 'survey|research|plan|inspect|register|reflect' skills/minecraft-builder/SKILL.md reference/orchestration/workflow-spine.md.
- [ ] Exécuter node scripts/validate-plugin.mjs. Si ce contrôle échoue, corriger les références avant de passer à la tâche 2.
- [ ] Faire un commit limité à ces trois fichiers, avec un message décrivant le contrat portable.

### Tâche 2 — Installer logiquement la suite dans Hermes et connecter les MCP

**Fichiers :** créer reference/mcp/hermes-connection.md ; modifier skills/setup-connect/SKILL.md et README.md. Ne pas créer d'installateur ni de copie de skills.

**Entrée :** dossier skills/ et endpoints MCP existants. **Sortie :** instructions reproductibles pour voir les 30 skills et appeler le MCP sous Hermes.

- [ ] Dans le guide, donner l'exemple exact de configuration de profil :

      skills:
        external_dirs:
          - /chemin/absolu/vers/le-clone/skills
      mcp_servers:
        minecraft-java:
          url: http://127.0.0.1:8765/mcp

  Ajouter minecraft-java-client à http://127.0.0.1:8766/mcp dans un bloc facultatif, seulement si un vrai client rendu tourne. Documenter les variantes distante et avec jeton à l'aide de variables d'environnement, sans valeur secrète en exemple.
- [ ] Expliquer la précédence des skills Hermes (profil local avant external_dirs), la possibilité de conflit de nom et le fait que external_dirs n'est pas une protection en écriture. Documenter comment vérifier la découverte avec hermes skills list et, si le CLI l'expose, skill_view en session. Le critère est 30/30 skills, pas seulement deux entrées.
- [ ] Faire de setup-connect une procédure à branches Claude, Codex, Hermes, avec une vérification commune server_get_status puis, si client présent, client_status et view_capture. Les exemples claude mcp add restent seulement dans la branche Claude.
- [ ] Valider sur une configuration Hermes temporaire ou un profil de test ; ne pas réécrire le profil utilisateur pendant le test. Si l'accès Hermes réel manque, consigner ce contrôle comme non exécuté.
- [ ] Exécuter node scripts/validate-plugin.mjs et committer uniquement les fichiers de cette tâche.

### Tâche 3 — Convertir les chemins exécutables du corpus

**Fichiers :** les SKILL.md listés par rg -l '\$\{CLAUDE_PLUGIN_ROOT\}' skills --glob 'SKILL.md' (23 fichiers au départ), plus les fichiers de reference/ et de skills/*/reference/ contenant des exemples réellement exécutables. Ne pas changer les métadonnées Claude model/context.

**Entrée :** résolution de racine de la tâche 1. **Sortie :** aucune instruction partagée qui exécute la variable Claude sans traduction Codex/Hermes.

- [ ] Générer l'inventaire exact avec rg -n '\$\{CLAUDE_PLUGIN_ROOT\}' skills reference agents ; classifier chaque occurrence : simple lien, prose Claude ou commande shell/Python.
- [ ] Convertir les liens et commandes des quatre skills build-* et de survey-site ; vérifier ce lot avec rg avant de toucher les autres.
- [ ] Convertir les six skills design-* ; vérifier ce lot avec rg.
- [ ] Convertir les cinq skills exec-* ; vérifier ce lot avec rg.
- [ ] Convertir les cinq skills terrain-* et les deux system-* ; vérifier ce lot avec rg.
- [ ] Convertir les références communes et les exemples des sous-dossiers reference/ repérés à l'inventaire. Les simples liens deviennent relatifs à la racine ; dans les commandes, utiliser une racine absolue résolue selon la tâche 1 et citer les chemins. Tester un checkout contenant des espaces. Ne pas faire de remplacement global aveugle : certains exemples Claude doivent rester valides.
- [ ] Corriger les snippets Python qui lisent os.environ['CLAUDE_PLUGIN_ROOT'] afin qu'ils utilisent la racine résolue ou une variable commune documentée ; conserver un chemin Claude valable si l'exemple est propre à Claude.
- [ ] Relancer rg et inspecter chaque occurrence restante : elle doit être dans une consigne ou un exemple explicitement Claude. Faire échouer la validation statique si une commande commune non protégée subsiste (tâche 5).
- [ ] Exécuter node scripts/validate-plugin.mjs puis python -m pytest tools/builder/tests tools/terrain/tests tools/voxel/tests ; committer ce lot de chemins.

### Tâche 4 — Convertir les interactions et les noms d'outils

**Fichiers :** skills/design-{building,city,grounds,house,monument,village}/reference/interview.md ; skills/system-{redstone,transit}/reference/interview.md ; skills/design-house/SKILL.md ; skills/exec-inspect/SKILL.md ; reference/execution/engine-limits.md ; skills/setup-connect/SKILL.md.

**Entrée :** contrat de la tâche 1. **Sortie :** instructions qui fonctionnent dans l'interface active et sur les noms de tools découverts.

- [ ] Rechercher rg -n 'AskUserQuestion|mcp__minecraft-java|claude mcp add' skills reference agents. Dans les huit fichiers interview et design-house, remplacer l'appel littéral AskUserQuestion par la règle « poser une question courte par l'interface hôte si la réponse manque », en gardant les questions métier utiles.
- [ ] Dans exec-inspect et engine-limits, parler de serveur minecraft-java-client + outil natif view_capture / sense_* plutôt que supposer un préfixe avec tiret. Conserver une table d'exemples par hôte dans runtime-portability.md, sans modifier les noms transmis au mod.
- [ ] Vérifier les chemins d'échec : serveur absent, client absent, client pas en jeu, sous-agent absent. Chaque cas doit produire un message clair et préserver les portes restantes.
- [ ] Exécuter rg de nouveau et justifier chaque mention Claude résiduelle. Exécuter node scripts/validate-plugin.mjs ; committer les changements.

### Tâche 5 — Verrouiller la portabilité dans le validateur et la CI

**Fichiers :** scripts/validate-plugin.mjs ; .github/workflows/ci.yml ; éventuellement scripts/tests/validate-plugin.test.mjs si un contrôle ajouté comporte une branche non triviale.

**Entrée :** fichiers convertis tâches 1–4. **Sortie :** une régression détectée automatiquement avant livraison.

- [ ] Étendre le validateur existant, sans nouvelle dépendance : exiger le guide Hermes, conserver les 30 noms et les deux noms MCP, repérer les références partagées à un outil préfixé avec tiret et les exemples exécutables non portables. Ne pas bannir globalement les métadonnées Claude ou sa documentation propre.
- [ ] Tester que le validateur échoue sur un exemple volontairement cassé dans une copie temporaire du dépôt, puis passe sur l'arbre restauré. Pour une logique de détection complexe, garder un seul test Node petit et ciblé ; ne pas introduire de framework.
- [ ] Vérifier que la CI exécute le validateur étendu. Ajouter les tests Python à la CI seulement si leur environnement et leur durée sont acceptables ; sinon documenter une commande de validation manuelle obligatoire.
- [ ] Exécuter node scripts/validate-plugin.mjs et python -m pytest tools/builder/tests tools/terrain/tests tools/voxel/tests. Exécuter le validateur Codex si disponible. Committer quand les sorties affichent zéro échec.

### Tâche 6 — Preuves de bout en bout sur les trois hôtes

**Fichiers :** créer docs/portability-smoke-test.md pour le protocole et les résultats datés ; ne pas stocker token, coordonnées privées, capture du monde ou logs bruts sensibles.

**Entrée :** une instance de test Minecraft Java et, pour le test visuel, un vrai client rendu. **Sortie :** matrice de preuves séparant statique, monde headless et rendu.

- [ ] Pour Claude, Codex et Hermes : charger les deux skills d'entrée, vérifier la découverte des skills métier, appeler server_get_status puis level_get_info sans écriture. Noter version du jeu réellement testée, sans l'imposer au produit.
- [ ] En monde de test jetable, demander la même petite structure aux trois hôtes, vérifier qu'un seul build-* est choisi et conserver la trace des portes survey, research, plan, build, integrate, inspect, register, reflect. Nettoyer le monde de test selon la procédure de test convenue, sans effacer un monde utilisateur.
- [ ] En mode serveur seul, vérifier que le résultat dit « inspection serveur seulement ». En mode client rendu, obtenir client_status et view_capture ; vérifier que l'image confirme le résultat plutôt que la seule réponse MCP.
- [ ] Tester une connexion distante avec variables d'environnement et jeton fictif côté configuration, puis un vrai endpoint d'essai si disponible ; chercher les chaînes sensibles dans la sortie avant de publier un extrait.
- [ ] Marquer chaque case PASS, FAIL ou NON TESTÉ. Un FAIL interdit la mention « portage complet » ; un NON TESTÉ visuel interdit la mention « inspection visuelle vérifiée ».

### Tâche 7 — Handoff et revue finale

**Fichiers :** mettre à jour README.md, CONTRIBUTING.md, AGENTS.md et docs/portability-smoke-test.md uniquement pour refléter le comportement vérifié.

- [ ] Repasser la spec section par section : tracer chaque exigence vers une modification et un contrôle. Chercher les placeholders et chemins morts avec rg.
- [ ] Exécuter les trois validations statiques de la préparation, puis git diff --check et git status --short ; enregistrer les résultats dans le guide de test.
- [ ] Donner au mainteneur un exemple de première demande identique pour Codex et Hermes et le chemin de diagnostic si server_get_status échoue.
- [ ] Faire la revue finale du diff, committer la documentation de livraison, pousser sur une branche dédiée du fork et ouvrir une PR vers le fork si une revue y est souhaitée. Ne pas ouvrir de PR vers le dépôt amont sans instruction explicite.

## Estimation et seuil de fin

Pour une personne connaissant les trois hôtes : 5 à 8 jours de travail, dont 1 à 2 jours pour les essais en jeu et les corrections qu'ils révèlent. Sans serveur Minecraft disponible, 4 à 6 jours peuvent produire un portage statiquement contrôlé ; le statut final reste conditionnel jusqu'au smoke test. Le critère d'arrêt est atteint lorsque la matrice Claude/Codex/Hermes, serveur seul/client rendu, ne comporte aucun FAIL sur le chemin principal et que les validateurs passent.
