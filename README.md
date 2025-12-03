# Voice-Assistant-AI-Agent

![Diagramme](/public/Architecture.png)

# IMPORTANT : POUR LANCER IL FAUT AVOIR OLLAMA OUVERT


## Idées : 
Offline/online
- Créer une fonction qui définit le LLM que l'on utilise dans chaque agent (par exemple return le offline ou online et choisir)?
- Choisir quand utiliser online ou offline (si question simple offline sinon online)

Agents : 
- Quand on fait les prompts des agents on peut mettre des conditions sur le retour des tools : par exemple si le tool retourne "fin" ou "reservation réussit" on peut demander d'arreter d'utiliser l'agent
- Agent Instructor (on peut mettre du early stopping, ...)

Workflow : 
- Faut il vérifié quand on renvoie au LLM final si on a bien répondu à la question ou pas ?
- Utiliser google maps pour récup position

Audio : 
- Si le son n'est pas lu par le speak_offline : utiliser gTTS (dans tous les cas on attend la version de vianney)

## Reste à Faire : 

BDD : 
- Choisir les Bases a utilisées.
- Créer les bases + rajouter la connexion

Agent : 
- Créer tous les agents avec les bonnes bases

Audio : 
- Synthétiser la voix de Vianney pour la réponse vocal
