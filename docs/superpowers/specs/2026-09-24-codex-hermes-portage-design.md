# Portage complet Codex et Hermes — spécification

Date : 2026-09-24. Base : kazaminosuke/minecraft-java-fabric-claude-plugin, commit 1404ffe. Décision de produit : aucune version de Minecraft n'est choisie ici.

## Intention et résultat attendu

Une seule suite de 30 skills doit piloter le même serveur Minecraft Java depuis Claude Code, Codex et Hermes. Un utilisateur doit pouvoir installer la suite, connecter le MCP, lancer une construction, voir les étapes réellement exécutées et obtenir une vérification honnête du résultat. Le portage concerne l'outillage des agents ; il ne crée ni mod Fabric ni mécanique de jeu.

Succès observable : sur chacun des trois hôtes, la demande « construis une petite structure près du joueur » emprunte la même chaîne survey → research → plan → blueprint/build → integrate → inspect → register → reflect. Le serveur monde répond à server_get_status. Si un vrai client de rendu est disponible, client_status puis view_capture prouvent l'inspection visuelle ; sinon le résultat porte explicitement la mention « inspection serveur seulement ». Une connexion distante authentifiée ne divulgue aucun jeton dans les fichiers suivis ou les journaux.

## État de départ vérifié

| Surface | Aujourd'hui | Conséquence |
| --- | --- | --- |
| Claude Code | Manifeste, agents, 30 skills, MCP et workflow historique présents | Préserver le comportement et les métadonnées Claude. |
| Codex | Manifeste .codex-plugin/plugin.json, deux skills d'entrée, deux adaptateurs et procédure MCP présents ; validateur existant | Consolider toute la suite, et pas seulement les deux entrées. |
| Hermes Agent v0.21.4 local | Lit les skills Markdown via skills.external_dirs et les MCP HTTP via mcp_servers ; renomme les composants MCP avec des underscores | Adapter la découverte, les noms d'outils et la configuration, sans recopier les skills. |
| Contenu commun | 23 SKILL.md contiennent CLAUDE_PLUGIN_ROOT, 24 contiennent model:, 11 context: fork ; 9 fichiers mentionnent AskUserQuestion | Les chemins exécutables et les interactions hôte doivent être portables ; les métadonnées Claude peuvent rester. |
| Utilitaires Python | tools/mcp_config.py lit environnement, JSON Claude/projet et TOML Codex ; pas YAML Hermes | Choisir l'environnement comme source commune de paramètres MCP pour Hermes et les scripts, sans parser YAML. |

La CI actuelle exécute le validateur Node. Les tests Python couvrent notamment la découverte des URL et jetons MCP. Aucun test en jeu n'est déduit de ces tests statiques.

## Décisions d'architecture

1. Le tronc commun reste skills/, reference/ et tools/. Aucun arbre Hermes ou Codex dupliqué. Les adaptations de lancement restent dans les deux skills d'entrée, reference/runtime-portability.md et les guides MCP propres à l'hôte.
2. Les 30 skills sont exposés à Hermes par skills.external_dirs pointant vers le dossier skills/ du clone. Cela évite copie, lien symbolique fragile et installateur maison. Documenter que les répertoires externes sont modifiables par Hermes si les droits du système le permettent ; ne pas présenter external_dirs comme une protection en écriture.
3. Les noms de serveurs sont invariants : minecraft-java et minecraft-java-client. Les noms Java natifs tels que server_get_status et view_capture sont invariants. Le nom préfixé exposé à Hermes est normalisé, par exemple mcp__minecraft_java__server_get_status. Les instructions partagées doivent nommer serveur + outil natif, puis laisser chaque hôte résoudre le nom effectivement découvert. Ne pas coder des alias fictifs dans le mod.
4. Les chemins relatifs à la suite sont résolus depuis la racine qui contient les manifestes Claude/Codex. Les exemples exécutables ne doivent pas supposer que le dossier courant est la racine du plugin. Les adaptations Codex/Hermes calculent cette racine avant d'exécuter un helper. Les exemples Claude existants gardent leur variable historique quand elle est nécessaire.
5. Les champs frontmatter model, context et effort restent pour compatibilité Claude. Codex/Hermes les ignorent comme contraintes de sélection de modèle. Les rôles logiques lead, specialist, executor et host-default guident l'orchestration ; l'absence de sous-agent entraîne l'exécution séquentielle avec les mêmes portes de validation.
6. Pour un serveur distant, MINECRAFT_MCP_URL et MINECRAFT_MCP_CLIENT_URL servent de source commune aux configs hôtes et aux helpers ; les jetons proviennent exclusivement de variables d'environnement. Les réglages localhost gardent leurs valeurs par défaut. Ne pas ajouter PyYAML uniquement pour lire la configuration Hermes.

## Contrats fonctionnels

- Découverte : Codex et Hermes affichent les deux skills d'entrée et peuvent charger les 28 autres. Un conflit de nom avec un skill local Hermes doit être détecté et signalé, car le skill local a priorité sur external_dirs.
- Connexion : monde obligatoire, client de rendu facultatif ; les deux endpoints peuvent se trouver sur des machines différentes. Le succès de healthz, ou d'une simple présence de configuration, ne prouve pas la connexion MCP. La preuve minimale est server_get_status.
- Construction : un seul orchestrateur build-* est choisi selon l'intention principale. Les portes « plan avant écriture », « intégration avant inspection » et « inspection avant enregistrement » sont conservées.
- Échanges utilisateur : AskUserQuestion devient une demande de clarification dans l'interface active, lorsque l'information manque réellement. Aucune fonction absente d'un hôte n'est appelée littéralement.
- Inspection : les noms d'outils sont découverts par l'hôte ; le test visuel exige un vrai client et view_capture. Le mode headless ne peut pas être déclaré visuellement validé.
- Sécurité : aucun token dans Git, la sortie standard ou une commande partagée ; les appels monde à effets de bord gardent les gardes du workflow existant.

## Hors périmètre

Pas de sélection de version Minecraft, migration Fabric, refonte des 30 métiers de construction, génération de nouvelles structures, agent IA autonome en jeu, ni publication dans des marketplaces publiques. Pas d'installation permanente dans le profil de l'utilisateur par le seul fait de cloner le dépôt.

## Risques et validation

Le risque majeur n'est pas la syntaxe du manifeste : c'est qu'un skill profond exécute encore un chemin Claude, cherche un nom d'outil préfixé absent, ou saute une porte du workflow. Les validations statiques doivent inspecter ces cas. Les validations en jeu doivent couvrir un petit build réversible, un mode serveur sans client, puis un mode avec client rendu. Si aucun serveur de test n'est disponible, marquer le portage « statiquement validé, essai en jeu restant », jamais « complet ».

## Options écartées

- Copier 30 skills pour Hermes : dérive des correctifs entre hôtes et coût de maintenance inutile.
- Ajouter un proxy MCP qui renomme les outils : surface de panne et de sécurité supplémentaire pour une traduction de nom que l'hôte fait déjà.
- Réécrire le mod Fabric ou figer Minecraft 1.21.1 : ne résout aucun problème de portabilité des agents et contredit la décision de version ouverte.
- Ajouter un parseur YAML aux helpers : les variables d'environnement couvrent déjà le cas Hermes, y compris les endpoints distants.
