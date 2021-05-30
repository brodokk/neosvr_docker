#!/bin/sh

if [ -n "${INSTALL_APPS}" ]; then
  OLD_IFS=$IFS
  IFS=','
  for app in ${INSTALL_APPS}; do
    steamcmd_binary="steamcmd"
    password_bypass=""
    beta_cmd=""
    if [ -n "${BETA_NAME}" ]; then
      beta_cmd=" -beta ${BETA_NAME}"
      if [ -n "${BETA_KEY}" ]; then
        beta_cmd="${beta_cmd} -betapassword ${BETA_KEY}"
      fi
    fi
    if [ -n "${PASSWORD}" ]; then
      password_bypass="echo '${PASSWORD}' | "
    fi
    echo "Check if ${app} is up to date"
    /bin/sh -c "${steamcmd_binary} +login ${LOGIN} ${PASSWORD} +force_install_dir /steam/${app} +app_update ${app}${beta_cmd} validate +quit"
  done
  IFS=$OLD_IFS
fi

arguments=$@
case "$arguments" in
  "/"*)
    echo "Run custom commands : ${arguments}"
    /bin/sh -c "$arguments";;
  *)
    echo "Cleaning old stuff..."
    find /steam/${LAUNCH_APP}/Data/Assets -atime +7 -delete
    find /steam/${LAUNCH_APP}/Data/Cache -atime +7 -delete
    echo "Run NeosVR headless client..."
    cd /steam/${LAUNCH_APP}/ && mono Neos.exe;;
esac
