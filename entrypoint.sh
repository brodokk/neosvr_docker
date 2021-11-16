#!/bin/sh

if [ -n "${INSTALL_APPS}" ]; then
  OLD_IFS=$IFS
  IFS=','
  for app in ${INSTALL_APPS}; do
    steamcmd_binary="steamcmd"
    password_bypass=""
    beta_cmd=""
    if [ -n "${STEAM_BETA_NAME}" ]; then
      beta_cmd=" -beta ${STEAM_BETA_NAME}"
      if [ -n "${STEAM_BETA_KEY}" ]; then
        beta_cmd="${beta_cmd} -betapassword ${STEAM_BETA_KEY}"
      fi
    fi
    if [ -n "${STEAM_PWD}" ]; then
      password_bypass="echo '${STEAM_PWD}' | "
    fi
    echo "Check if ${app} is up to date"
    /bin/sh -c "${steamcmd_binary} +login ${STEAM_USER} ${STEAM_PWD} +force_install_dir /steam/${app} +app_update ${app}${beta_cmd} validate +quit"
  done
  IFS=$OLD_IFS
fi

echo "setting up neos config from env"

CONFIG_PATH='/steam/740250/Config'

cat $CONFIG_PATH | jq --arg u "${NEOSVR_USER}" '.loginCredential = $u' | jq --arg p "${NEOSVR_PWD}" '.loginPassword = $p' | sponge $CONFIG_PATH

arguments=$@
case "$arguments" in
  "/"*)
    echo "Run custom commands : ${arguments}"
    /bin/sh -c "$arguments";;
  *)
    echo "Cleaning old stuff..."
    find /steam/${LAUNCH_APP}/Data/Assets -atime +7 -delete
    find /steam/${LAUNCH_APP}/Data/Cache -atime +7 -delete
    find /Logs -atime +30 -delete
    echo "Run NeosVR headless client..."
    cd /steam/${LAUNCH_APP}/ && mono Neos.exe -l /logs;;
esac
