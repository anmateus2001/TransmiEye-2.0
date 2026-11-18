#!/usr/bin/env bash
# Instala y arranca TransmiEye en un servidor Ubuntu nuevo (Oracle Cloud, AWS, Google Cloud, etc.).
# Uso, dentro de la carpeta del proyecto:   bash desplegar.sh
set -e

if ! command -v docker >/dev/null; then
  echo "Instalando Docker..."
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
fi

# Ubuntu en Oracle Cloud trae reglas de iptables que bloquean 80 y 443 aunque abras la red en la consola
if sudo iptables -L INPUT -n 2>/dev/null | grep -q "REJECT"; then
  echo "Abriendo los puertos 80 y 443 en el firewall del sistema..."
  sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
  sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
  sudo netfilter-persistent save 2>/dev/null || true
fi

IP=$(curl -fsS https://api.ipify.org || curl -fsS https://ifconfig.me)
SUGERIDO="$(echo "$IP" | tr . -).sslip.io"
read -rp "Dominio [$SUGERIDO]: " DOMINIO
DOMINIO=${DOMINIO:-$SUGERIDO}
read -rsp "Contraseña para el usuario admin (mínimo 8 caracteres): " CLAVE; echo
[ ${#CLAVE} -ge 8 ] || { echo "La contraseña es muy corta."; exit 1; }

cat > .env <<ENV
DOMINIO=$DOMINIO
TRANSMIEYE_ADMIN_PASS=$CLAVE
ENV
chmod 600 .env
mkdir -p data videos

sudo docker compose up -d --build
echo
echo "Listo. En 1 o 2 minutos abre:  https://$DOMINIO"
echo "Usuario: admin   Contraseña: la que acabas de escribir"
