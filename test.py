# test_api.py
import requests
import time

# L'URL de ton serveur local
BASE_URL = 'http://127.0.0.1:8000'

def test_blendai():
    url = f"{BASE_URL}/blendai/"
    payload = {
        "user_input": "Je veux générer un projet IA",
        "blendai_prompt": "Fais un résumé en 100 mots",
        "project_content": "Contenu du projet ici"
    }
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        request_id = data['id']
        print(f"Requête envoyée ! ID : {request_id}")
        return request_id
    else:
        print(f"Erreur lors de l'envoi : {response.text}")
        return None

def check_queue_position(request_id):
    url = f"{BASE_URL}/queue/?id={request_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['position']
    elif response.status_code == 404:
        return None  # ID plus en queue (traité ou erreur)
    else:
        print(f"Erreur lors de la récupération de la position : {response.text}")
        return -1

def get_result(request_id):
    url = f"{BASE_URL}/result/?id={request_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['response']
    elif response.status_code == 404:
        return None
    else:
        print(f"Erreur lors de la récupération du résultat : {response.text}")
        return None

if __name__ == "__main__":
    request_id = test_blendai()
    if request_id:
        while True:
            position = check_queue_position(request_id)
            if position is None:
                print("La requête n'est plus dans la file. En attente du résultat...")
                break
            elif position == -1:
                print("Erreur pendant la vérification. Nouvelle tentative dans 3 secondes...")
            else:
                print(f"Position actuelle : {position}")
            time.sleep(1)  # Attendre 3 secondes avant de re-checker
        
        # Maintenant on attend que le résultat soit prêt
        while True:
            result = get_result(request_id)
            if result:
                print(f"🎉 Résultat reçu :\n{result}")
                break
            else:
                print("Résultat pas encore prêt, attente de 3 secondes...")
                time.sleep(3)
