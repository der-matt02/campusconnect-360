# Guía de Operación y Automatización DevSecOps — CampusConnect 360

Esta guía documenta los componentes del sistema, analiza los problemas que resolvimos hoy y detalla cómo levantar todo el ecosistema de **CampusConnect 360** mañana en solo dos pasos sencillos.

---

## 1. Mapa de Conectividad (¿Cómo está conectado todo?)

El siguiente diagrama muestra el flujo de datos desde el repositorio en la nube hasta tu navegador local:

```mermaid
graph TD
    %% GitHub & CI/CD
    subgraph GitHub Cloud
        git[Repositorio GitHub] -->|Pipeline CI/CD| ghcr[GitHub Container Registry]
        zap[OWASP ZAP Runner] -->|Escanea DAST| ngrok_url[URL de ngrok]
    end

    %% Red Local
    subgraph Tu Laptop (Host Windows)
        ngrok_url -->|Túnel Seguro| ngrok[ngrok CLI]
        ngrok -->|Redirecciona a localhost:8080| pf[kubectl port-forward]
    end

    %% Cluster Minikube
    subgraph Minikube Cluster (K8s)
        pf -->|Bridge de Red| ingress[Ingress Controller NodePort]
        ingress -->|Rutas /api, /auth| gateway[Gateway Pod]
        ingress -->|Rutas /| frontend[React Frontend Pod]
        
        flux[Flux CD Controllers] -->|Monitorea cada 1m| git
        flux -->|Aplica manifiestos| k8s_api[Kubernetes API]
        k8s_api -->|Descarga imágenes privadas usando ghcr-secret| ghcr
    end
```

---

## 2. Análisis de Problemas Resueltos (Lecciones Aprendidas)

Durante la instalación inicial nos enfrentamos a 4 desafíos técnicos importantes. Así es como los solucionamos de forma permanente:

1. **Error de Deploy Keys (404 Not Found):**
   * *Causa:* Al ser colaborador y no el administrador del repositorio, tu token no tiene permisos para agregar llaves SSH de despliegue a la configuración de GitHub.
   * *Solución:* Agregamos `--token-auth` al bootstrap de Flux para forzar la sincronización sobre HTTPS usando tu token directo.
2. **Restricción de Kustomize (Parent Directory `..`):**
   * *Causa:* Por seguridad, Kustomize prohíbe referenciar archivos que estén fuera del directorio raíz de su `kustomization.yaml`.
   * *Solución:* Movimos `gitrepository.yaml` y `helmrelease.yaml` dentro de la carpeta `flux-system/` para que estén en el mismo nivel.
3. **Deadlock de Helm (pending-install):**
   * *Causa:* Al no tener las credenciales de descarga de imágenes en el cluster (`ghcr-secret`), los pods no iniciaron. Helm se bloqueó en un tiempo de espera de 5 minutos, congelando cualquier actualización o nuevo commit.
   * *Solución:* Desinstalamos manualmente la versión atascada usando `helm uninstall` en el namespace `flux-system` para forzar a Helm a iniciar de nuevo.
4. **Estrategia de Actualización (Chart Version Cache):**
   * *Causa:* Por defecto, Flux solo reconstruye el chart si cambia la versión en `Chart.yaml`. Las modificaciones en las plantillas locales eran ignoradas por la ación.
   * *Solución:* Cambiamos la directiva `reconcileStrategy` a `Revision` para indicarle a Flux que reconstruya y actualice el Chart en **cada commit**.

---

## 3. Guía de Uso: "Cómo levantar el proyecto mañana"

Mañana, cuando enciendas tu computadora, no tendrás que repetir la configuración de Flux ni de Git. Tienes dos escenarios:

### Escenario A: Si conservas el cluster de hoy (Recomendado)
Minikube guarda el estado del cluster en el disco. Solo debes iniciar Minikube y los túneles:

1. Abre PowerShell y enciende Minikube:
   ```powershell
   minikube start
   ```
2. Ejecuta el script de automatización (ver sección 4) para crear el Port-Forward y ngrok:
   ```powershell
   .\scripts\start_devsecops.ps1
   ```

### Escenario B: Si recreas Minikube desde cero
Si eliminas Minikube (`minikube delete`) y quieres montar todo limpio de nuevo:

1. Crea el cluster y habilita el ingress:
   ```powershell
   minikube start
   minikube addons enable ingress
   ```
2. Corre el bootstrap de Flux (HTTPS):
   ```powershell
   flux bootstrap github --owner=der-matt02 --repository=campusconnect-360 --branch=build/devsecops --path=deploy/bootstrap --personal --token-auth
   ```
3. Ejecuta el script de automatización de abajo para inyectar tus credenciales, el port-forward y ngrok de un solo golpe.
