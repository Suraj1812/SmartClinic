#!/bin/sh
set -eu

cp /etc/odoo/odoo.conf /tmp/odoo.conf
printf '\nadmin_passwd = %s\n' "${ODOO_MASTER_PASSWORD:-change-this-master-password}" >> /tmp/odoo.conf

exec odoo \
  --config=/tmp/odoo.conf \
  --db_host=db \
  --db_port=5432 \
  --db_user="${POSTGRES_USER:-odoo}" \
  --db_password="${POSTGRES_PASSWORD:-odoo}" \
  --database="${ODOO_DB:-smartclinic}" \
  --without-demo=all
