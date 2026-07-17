# GPU & VRAM Orchestrator

Puisque nous hébergeons plusieurs modèles (`llama3.1`, `qwen2.5`, `mistral`, `nomic-embed`), il est impossible de tous les garder en mémoire simultanément sur une machine classique (ex: 16Go VRAM).

Le `gpu_manager` maintient un dictionnaire des modèles chargés et de leur poids estimé.
Avant chaque appel d'inférence (Chat ou Embedding), l'orchestrateur vérifie si le modèle est dans le dictionnaire. 
S'il faut le charger et que l'espace manque, le plus ancien modèle est évincé silencieusement.
