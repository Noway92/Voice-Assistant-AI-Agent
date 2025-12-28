# Voice-Assistant-AI-Agent

![Diagramme](/public/Architecture.png)

# Environement
The environement is for python 3.10
If you want to use python 3.13, just use requirements_python3_13

# Run code 
python app.py
ngrok http 5000 
Fetch the forwarding adress
Copy the adress in your BASE_URL 
Go in https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
Click on the number you want to use
Copy the adress in "Voice Configuration" → "A CALL COMES IN"

# IMPORTANT : POUR LANCER IL FAUT AVOIR OLLAMA OUVERT


## Idées : 

Agents : 
- Quand on fait les prompts des agents on peut mettre des conditions sur le retour des tools : par exemple si le tool retourne "fin" ou "reservation réussit" on peut demander d'arreter d'utiliser l'agent
- Agent Instructor (on peut mettre du early stopping, ...)

Workflow : 
- Faut il vérifié quand on renvoie au LLM final si on a bien répondu à la question ou pas ?

Audio : 
- Si le son n'est pas lu par le speak_offline : utiliser gTTS (dans tous les cas on attend la version de vianney)

## Reste à Faire : 

Agent : 
- Créer tous les agents avec les bonnes bases

Audio : 
- Synthétiser la voix de Vianney pour la réponse vocal
