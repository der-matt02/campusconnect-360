package main

# Todo contenedor de un Deployment debe declarar limites de CPU y memoria,
# para evitar que un servicio sin control de recursos afecte al resto del cluster.
deny contains msg if {
	input.kind == "Deployment"
	container := input.spec.template.spec.containers[_]
	not container.resources.limits.cpu
	msg := sprintf("Deployment '%s': el contenedor '%s' no define resources.limits.cpu", [input.metadata.name, container.name])
}

deny contains msg if {
	input.kind == "Deployment"
	container := input.spec.template.spec.containers[_]
	not container.resources.limits.memory
	msg := sprintf("Deployment '%s': el contenedor '%s' no define resources.limits.memory", [input.metadata.name, container.name])
}

# Toda imagen privada de GHCR debe descargarse usando un imagePullSecret,
# de lo contrario el despliegue queda en ImagePullBackOff.
deny contains msg if {
	input.kind == "Deployment"
	container := input.spec.template.spec.containers[_]
	startswith(container.image, "ghcr.io/")
	not input.spec.template.spec.imagePullSecrets
	msg := sprintf("Deployment '%s': usa una imagen privada de GHCR ('%s') pero no define imagePullSecrets", [input.metadata.name, container.image])
}

# El tag ':latest' no es reproducible ni auditable: el pipeline de GitOps
# debe desplegar siempre un tag inmutable (SHA de commit).
deny contains msg if {
	input.kind == "Deployment"
	container := input.spec.template.spec.containers[_]
	endswith(container.image, ":latest")
	msg := sprintf("Deployment '%s': el contenedor '%s' usa el tag ':latest', debe usar un tag inmutable (SHA de commit)", [input.metadata.name, container.name])
}