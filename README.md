### README.md

# Movie Scraper

## Projekt na zaliczenie przedmiotu Przetwarzanie Równoległe i Rozproszone
### Wykonane przez Tomasz Piekarczyk oraz Emilia Massowa

## Spis Treści
- [Movie Scraper](#movie-scraper)
  - [Projekt na zaliczenie przedmiotu Przetwarzanie Równoległe i Rozproszone STAC](#projekt-na-zaliczenie-przedmiotu-przetwarzanie-równoległe-i-rozproszone-stac)
  - [Wymagania wstępne](#wymagania-wstępne)
  - [Instalacja i konfiguracja](#instalacja-i-konfiguracja)
    - [Korzystanie z Docker Compose](#korzystanie-z-docker-compose)
    - [Korzystanie z Kubernetes](#korzystanie-z-kubernetes)
    - [Uruchamianie ręczne za pomocą Docker](#uruchamianie-ręczne-za-pomocą-docker)
  - [Użytkowanie](#użytkowanie)
  - [Endpointy](#endpointy)
  - [Zmienne środowiskowe](#zmienne-środowiskowe)
  - [Wkład w projekt](#wkład-w-projekt)
  - [Licencja](#licencja)

## Wymagania wstępne

- Docker
- Docker Compose (jeśli korzystasz z Docker Compose)
- Kubernetes i kubectl (jeśli korzystasz z Kubernetes)
- Minikube (opcjonalnie, do lokalnej konfiguracji Kubernetes)

## Instalacja i konfiguracja

### Korzystanie z Docker Compose

1. Sklonuj repozytorium:
    ```sh
    git clone https://github.com/deefyy/movie-scraper.git
    cd movie-scraper
    ```

2. Zbuduj i uruchom kontenery Docker:
    ```sh
    docker-compose up -d
    ```

3. Uzyskaj dostęp do aplikacji:
    - UI: [http://localhost:5000](http://localhost:5000)
    - Backend: [http://localhost:5001](http://localhost:5001)

### Korzystanie z Kubernetes

1. Sklonuj repozytorium:
    ```sh
    git clone <repository-url>
    cd movie-scraper
    ```

2. Uruchom Minikube (jeśli używasz Minikube):
    ```sh
    minikube start
    ```

3. Zastosuj manifesty Kubernetes:
    ```sh
    kubectl apply -f kubernetes-manifests/namespace.yaml
    kubectl apply -f kubernetes-manifests/mongo-pv.yaml
    kubectl apply -f kubernetes-manifests/mongo-deployment.yaml
    kubectl apply -f kubernetes-manifests/configmap.yaml
    kubectl apply -f kubernetes-manifests/backend-deployment.yaml
    kubectl apply -f kubernetes-manifests/ui-deployment.yaml
    ```

4. Uzyskaj adresy usług:
    ```sh
    minikube service prir-ui -n movie-scraper
    ```

### Uruchamianie ręczne za pomocą Docker

1. Sklonuj repozytorium:
    ```sh
    git clone <repository-url>
    cd movie-scraper
    ```

2. Zbuduj obrazy Docker:
    ```sh
    docker build -t backend backend
    docker build -t ui ui
    ```

3. Utwórz sieć Docker:
    ```sh
    docker network create movie-scraper-network
    ```

4. Uruchom kontener MongoDB:
    ```sh
    docker run --name prir-mongo --network movie-scraper-network -e MONGO_INITDB_ROOT_USERNAME=root -e MONGO_INITDB_ROOT_PASSWORD=root -v prir-mongo-data:/data/db -p 27017:27017 -d mongo
    ```

5. Uruchom kontener backendu:
    ```sh
    docker run --name prir-backend --network movie-scraper-network -e DB_URI="mongodb://prir-mongo:27017/" -e DB_USERNAME="root" -e DB_PASSWORD="root" -e DB_NAME="movie_database" -e BACKEND_HOST="0.0.0.0" -e BACKEND_PORT="5001" -p 5001:5001 -d backend
    ```

6. Uruchom kontener UI:
    ```sh
    docker run --name prir-ui --network movie-scraper-network -e DB_URI="mongodb://prir-mongo:27017/" -e DB_USERNAME="root" -e DB_PASSWORD="root" -e DB_NAME="movie_database" -e BACKEND_HOST="prir-backend" -e BACKEND_PORT="5001" -e UI_HOST="0.0.0.0" -e UI_PORT="5000" -p 5000:5000 -d ui
    ```

7. Uzyskaj dostęp do aplikacji:
    - UI: [http://localhost:5000](http://localhost:5000)
    - Backend: [http://localhost:5001](http://localhost:5001)

## Użytkowanie

Aplikacja zapewnia interfejs webowy do scrapowania gatunków filmowych oraz szczegółów filmów. Użytkownicy mogą inicjować procesy scrapowania i przeglądać wyniki.

## Endpointy

### Endpointy Backend

- `POST /scrape`: Inicjuje proces scrapowania filmów.
- `POST /scrape_genres`: Inicjuje proces scrapowania gatunków.
- `GET /results`: Pobiera szczegóły zeskrapowanych filmów.

### Endpointy UI

- `/`: Strona główna do inicjowania procesów scrapowania i przeglądania wyników.

## Zmienne środowiskowe

Poniższe zmienne środowiskowe są używane do konfiguracji aplikacji:

- `DB_URI`: URI do bazy danych MongoDB.
- `DB_USERNAME`: Nazwa użytkownika MongoDB.
- `DB_PASSWORD`: Hasło użytkownika MongoDB.
- `DB_NAME`: Nazwa bazy danych w MongoDB.
- `BACKEND_HOST`: Host dla usługi backendu.
- `BACKEND_PORT`: Port dla usługi backendu.
- `UI_HOST`: Host dla usługi UI.
- `UI_PORT`: Port dla usługi UI.

## Licencja

Ten projekt jest licencjonowany na licencji MIT. Zobacz plik LICENSE, aby uzyskać więcej informacji.
