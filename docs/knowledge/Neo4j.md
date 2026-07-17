# Neo4j & Graph Intelligence

Neo4j est utilisé pour comprendre la connectivité du monde de claimOS.

## Algorithmes
- **Entity Resolution** : Résolution des entités (Personne A et Personne B sont-elles les mêmes ?).
- **Fraud Networks** : Utilise la détection de communautés (`Connected Components`, `PageRank`) pour repérer automatiquement des anneaux de fraude (ex: 3 personnes partagent le même IBAN sur des sinistres différents).

*Note: En l'absence de cluster Neo4j, une abstraction `NetworkX` est utilisée de façon transparente via l'`IRepository`.*
