# Publicar TransmiEye en internet (sin depender de tu PC)

El sistema queda en un servidor en la nube, encendido las 24 horas, con un enlace `https://...` que se abre desde cualquier lugar. Las cámaras pueden ser:

- **Un celular o PC con cámara**, usando la página *Transmitir cámara*. No necesita nada en la red de la estación.
- **Cámaras IP** cuyo RTSP sea accesible desde internet.
- **Videos subidos** desde la página Cámaras, para demostraciones.

Las webcams USB solo sirven cuando el sistema corre en el mismo equipo donde están conectadas.

## 1. Elegir el servidor

El servidor necesita al menos **2 núcleos y 4 GB de RAM** para correr YOLO en CPU.

| Opción | Costo | Comentario |
|---|---|---|
| **Oracle Cloud Always Free** (VM Ampere A1) | Gratis | Hasta 2 núcleos y 12 GB de RAM sin costo. Pide tarjeta para verificar identidad, a veces no hay capacidad disponible y Oracle puede reclamar instancias inactivas. Es la opción recomendada para la práctica. |
| Cualquier VPS con Ubuntu (DigitalOcean, AWS, Google Cloud, Azure, Hetzner…) | De pago | Los mismos pasos desde el punto 3. Revisa si tu universidad tiene créditos para estudiantes. |

Plataformas como Render o Railway no sirven en sus planes básicos: dan unos 512 MB de RAM, insuficientes para PyTorch.

## 2. Crear la máquina en Oracle Cloud

1. Crea la cuenta en https://cloud.oracle.com. Elige como región principal la más cercana; no se puede cambiar después.
2. Ve a **Menú → Compute → Instances → Create instance**:
   - **Image:** Canonical Ubuntu 24.04 (o 22.04).
   - **Shape:** *Change shape → Ampere → VM.Standard.A1.Flex*, con **2 OCPU y 12 GB** de memoria.
   - **Networking:** deja la red por defecto y marca *Assign a public IPv4 address*.
   - **SSH keys:** *Generate a key pair for me* y **descarga la llave privada**. Sin ella no podrás entrar.
   - Pulsa **Create**.

   Si aparece *Out of host capacity*, Oracle no tiene máquinas libres en esa zona. Prueba otro *Availability domain* (AD-1, AD-2, AD-3), pide 1 OCPU y 6 GB, o inténtalo más tarde (en la noche suele haber más espacio). Es frecuente en regiones muy usadas como Ashburn. Pasar la cuenta a *Pay As You Go* da prioridad y los recursos Always Free siguen sin costo, pero cualquier recurso fuera del plan gratuito se cobra: si lo haces, crea una alerta de presupuesto de 1 USD en *Billing → Budgets*.

   Si solo necesitas mostrar el sistema por un rato, no hace falta servidor: usa el link temporal desde tu PC descrito en el README (*Compartir un link desde tu PC*).
3. Abre los puertos web. En la página de la instancia entra a la *Subnet → Security List → Add Ingress Rules* y agrega dos reglas:
   - Source `0.0.0.0/0`, protocolo TCP, puerto destino **80**.
   - Source `0.0.0.0/0`, protocolo TCP, puerto destino **443**.
4. Copia la **IP pública** que aparece en la página de la instancia.

## 3. Entrar al servidor

Desde la terminal de Windows (CMD o PowerShell), en la carpeta donde quedó la llave:

```
ssh -i ssh-key-XXXX.key ubuntu@IP_PUBLICA
```

Si Windows se queja de los permisos de la llave, haz clic derecho sobre el archivo → *Propiedades → Seguridad → Opciones avanzadas*, quita la herencia y deja solo a tu usuario.

## 4. Instalar TransmiEye

Dentro del servidor:

```
git clone https://github.com/TU-USUARIO/TU-REPO.git transmieye
cd transmieye
bash desplegar.sh
```

El script hace lo siguiente:

- instala Docker y abre los puertos del firewall de Ubuntu;
- te propone un dominio gratuito basado en la IP (`129-146-10-20.sslip.io`), o puedes escribir uno propio;
- te pide la contraseña del usuario `admin`;
- construye y arranca el sistema con HTTPS automático (Let's Encrypt).

La primera vez tarda entre 10 y 15 minutos, porque descarga PyTorch y construye la imagen. Al terminar muestra el enlace, por ejemplo `https://129-146-10-20.sslip.io`.

El HTTPS no es opcional: los navegadores solo permiten usar la cámara del celular en páginas seguras.

## 5. Usar un celular como cámara

1. En el computador, entra como admin y ve a **Cámaras → Agregar cámara → Celular o navegador**. Ponle un código (por ejemplo `CAM-HER-01`) y guárdala.
2. En el celular, abre el mismo enlace, ingresa con un usuario **supervisor** o **admin** y ve a **Transmitir cámara**. Elige la cámara y pulsa **Iniciar transmisión**, y acepta el permiso de cámara.
3. Fija el celular en alto, mirando las puertas, y conéctalo a la corriente. La pantalla se mantiene encendida mientras transmite.
4. Con la transmisión en curso, en el computador abre **Zonas y puertas** de esa cámara y dibuja el carril, la plataforma y la línea de cada puerta.

**Consumo de datos:** con calidad *Normal* (960 px) y 8 cuadros por segundo cada cuadro pesa unos 50 KB, es decir, cerca de 1,4 GB por hora. Con datos móviles usa calidad *Liviana* y 4 cuadros por segundo, o mejor conecta el celular a wifi.

## 6. Mantenimiento

| Tarea | Comando (dentro de la carpeta `transmieye` del servidor) |
|---|---|
| Actualizar después de subir cambios a GitHub | `git pull && sudo docker compose up -d --build` |
| Ver los registros | `sudo docker compose logs -f transmieye` |
| Reiniciar | `sudo docker compose restart` |
| Copia de seguridad | Copia la carpeta `data/` (base de datos, evidencias y reportes) |

La base de datos y las evidencias viven en `data/` del servidor, así que sobreviven a reinicios y actualizaciones. Ni esa carpeta ni el archivo `.env`, que guarda la contraseña inicial, se suben a GitHub.

## Seguridad en un servidor público

- No se crea la cuenta `admin123`: la contraseña inicial es la que escribiste en el script.
- Tras 5 intentos fallidos de ingreso desde la misma IP, el ingreso se bloquea 10 minutos.
- Solo los usuarios **supervisor** y **admin** pueden transmitir video. Crea una cuenta aparte para cada celular que haga de cámara.
- Las imágenes de evidencia se anonimizan antes de guardarse y se purgan a los 30 días.
