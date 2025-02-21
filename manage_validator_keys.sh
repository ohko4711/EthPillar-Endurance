#!/bin/bash

# Author: coincashew.eth | coincashew.com
# License: GNU GPL
# Source: https://github.com/coincashew/ethpillar
#
# Made for home and solo stakers 🏠🥩

# Dir to install staking-deposit-cli
STAKING_DEPOSIT_CLI_DIR=$HOME
# Path to deposit cli tool
DEPOSIT_CLI_PATH=$STAKING_DEPOSIT_CLI_DIR/ethstaker_deposit-cli
# Initialize variable
OFFLINE_MODE=false
isLido=""
# Base directory with scripts
BASE_DIR=$HOME/git/ethpillar
# Load functions
source $BASE_DIR/functions.sh
# Load Lido CSM withdrawal address and fee recipient
source $BASE_DIR/env

# Pinned version of ethstaker-deposit-cli
edc_version="0.0.2"
edc_hash="4ac463b"

# Get machine info
_platform=$(get_platform)
_arch=$(get_arch)

function downloadEthstakerDepositCli(){
    if [ -d $STAKING_DEPOSIT_CLI_DIR/ethstaker_deposit-cli ]; then
        edc_version_installed=$($STAKING_DEPOSIT_CLI_DIR/ethstaker_deposit-cli/deposit --version)
        if [[ "${edc_version_installed}" =~ .*"${edc_version}".* ]]; then
            echo "ethstaker_deposit-cli is up-to-date"
            return
        else
            rm -rf $STAKING_DEPOSIT_CLI_DIR/ethstaker_deposit-cli
            echo "ethstaker_deposit-cli update available"
            echo "Updating to v${edc_version}"
            echo "from ${edc_version_installed}"
        fi
    fi
    ohai "Downloading ethstaker_deposit-cli v${edc_version}"
    #Install dependencies
    sudo apt install jq curl -y

    #Setup variables
    BINARIES_URL="https://github.com/ohko4711/ethstaker-deposit-cli/releases/download/v${edc_version}/ethstaker_deposit-cli-${edc_hash}-${_platform}-${_arch}.tar.gz"
    BINARY_FILE="ethstaker_deposit-cli.tar.gz"

    [[ -z $BINARIES_URL ]] && echo "Error: Unable to determine BINARIES URL" && exit 1
    ohai "Downloading URL: $BINARIES_URL"
    # Dir to install ethstaker_deposit-cli
    cd $STAKING_DEPOSIT_CLI_DIR
    # Download binary
    wget -O $BINARY_FILE $BINARIES_URL
    # Extract archive
    tar -xzvf $BINARY_FILE -C $STAKING_DEPOSIT_CLI_DIR
    # Cleanup
    rm ethstaker_deposit-cli.tar.gz
    # Rename
    mv ethstaker_deposit-cli*${_arch} ethstaker_deposit-cli
}

function generateNewValidatorKeys(){
    [[ $# -eq 1 ]] && local ARGUMENT=$1 && checkLido $1 || ARGUMENT="default"
    if network_isConnected; then
        if whiptail --title "Offline Key Generation" --defaultno --yesno "$MSG_OFFLINE" 20 78; then
            network_down
            OFFLINE_MODE=true
            ohai "Network is offline mode"
        fi
    fi

    _getNetwork

    if [ -z "$NETWORK" ]; then exit; fi # pressed cancel
    if ! whiptail --title "Information on Secret Recovery Phrase Mnemonic" --yesno "$MSG_INTRO" 24 78; then exit; fi
    if network_isConnected; then whiptail --title "Warning: Internet Connection Detected" --msgbox "$MSG_INTERNET" 18 78; fi
    setConfig
    _getEthAddy

    NUMBER_NEW_KEYS=$(whiptail --title "# of New Keys" --inputbox "How many keys to generate?" 8 78 --ok-button "Submit" 3>&1 1>&2 2>&3)
    _setKeystorePassword

    cd $DEPOSIT_CLI_PATH
    KEYFOLDER="${DEPOSIT_CLI_PATH}/$(date +%F-%H%M%S)"
    mkdir -p "$KEYFOLDER"
    ./deposit --non_interactive new-mnemonic --chain "$NETWORK" --execution_address "$ETHADDRESS" --num_validators "$NUMBER_NEW_KEYS" --keystore_password "$_KEYSTOREPASSWORD" --folder "$KEYFOLDER" --regular-withdrawal
    if [ $? -eq 0 ]; then
        #Update path
        KEYFOLDER="$KEYFOLDER/validator_keys"
        # $1 is argument for CSM Validator Plugin
        loadKeys $ARGUMENT
        if [ $OFFLINE_MODE == true ]; then
            network_up
            ohai "Network is online"
        fi
    else
        ohai "Error with staking-deposit-cli. Try again."
        exit
    fi
}

function _getEthAddy(){
    while true; do
        ETHADDRESS=$(whiptail --title "Ethereum Withdrawal Address" --inputbox "$MSG_ETHADDRESS" 15 78 --ok-button "Submit" 3>&1 1>&2 2>&3)
        if [ -z "$ETHADDRESS" ]; then exit; fi #pressed cancel
        if [[ "${ETHADDRESS}" =~ ^0x[a-fA-F0-9]{40}$ ]]; then
            break
        else
            whiptail --title "Error" --msgbox "Invalid ETH address. Try again." 8 78
        fi
    done
}

function _getNetwork(){
    NETWORK=$(whiptail --title "Network" --menu \
          "For which network are you generating validator keys?" 12 90 4 \
          "mainnet" "Ethereum - Real ETH. Real staking rewards." \
          "holesky" "long term Testnet  - Suitable for staking practice." \
          "ephemery" "short term Testnet - Ideal for staking practice. Monthly resets." \
          "endurance_devnet" "short term for Endurance Devnet - Ideal for staking practice. No rewards." \
          3>&1 1>&2 2>&3)
}

function importValidatorKeys(){
    [[ $# -eq 1 ]] && local ARGUMENT=$1 && checkLido $1 || ARGUMENT="default"
    KEYFOLDER=$(whiptail --title "Import Validator Keys from Offline Generation or Backup" --inputbox "$MSG_PATH" 16 78 --ok-button "Submit" 3>&1 1>&2 2>&3)
    if [ -d "$KEYFOLDER" ]; then
        _getNetwork

        if [ -z "$NETWORK" ]; then exit; fi # pressed cancel
        setConfig

        if whiptail --title "Important Information" --defaultno --yesno "$MSG_IMPORT" 20 78; then
            _KEYSTOREPASSWORD=""
            # $1 is argument for CSM Validator Plugin
            loadKeys $ARGUMENT
        fi
    else
        ohai "$KEYFOLDER does not exist. Try again."
        exit
    fi
}

function addRestoreValidatorKeys(){
    [[ $# -eq 1 ]] && local ARGUMENT=$1 && checkLido $1 || ARGUMENT="default"
    if whiptail --title "Offline Key Generation" --defaultno --yesno "$MSG_OFFLINE" 20 78; then
        network_down
        OFFLINE_MODE=true
        ohai "Network is down"
    fi
    _getNetwork

    if [ -z "$NETWORK" ]; then exit; fi # pressed cancel
    if ! whiptail --title "Information on Secret Recovery Phrase Mnemonic" --yesno "$MSG_INTRO" 24 78; then exit; fi
    if network_isConnected; then whiptail --title "Warning: Internet Connection Detected" --msgbox "$MSG_INTERNET" 18 78; fi
    setConfig
    _getEthAddy

    NUMBER_NEW_KEYS=$(whiptail --title "# of New Keys" --inputbox "How many keys to generate?" 8 78 --ok-button "Submit" 3>&1 1>&2 2>&3)
    START_INDEX=$(whiptail --title "# of Existing Keys" --inputbox "How many validator keys were previously made? Also known as the starting index." 10 78 --ok-button "Submit" 3>&1 1>&2 2>&3)
    whiptail --title "Keystore Password" --msgbox "Reminder to use the same keystore password as existing validators." 10 78
    _setKeystorePassword

    cd $DEPOSIT_CLI_PATH
    KEYFOLDER="${DEPOSIT_CLI_PATH}/$(date +%F-%H%M%S)"
    mkdir -p "$KEYFOLDER"
    ./deposit --non_interactive existing-mnemonic --chain "$NETWORK" --execution_address "$ETHADDRESS" --folder "$KEYFOLDER" --keystore_password "$_KEYSTOREPASSWORD" --validator_start_index "$START_INDEX" --num_validators "$NUMBER_NEW_KEYS" --regular-withdrawal
    if [ $? -eq 0 ]; then
        #Update path
        KEYFOLDER="$KEYFOLDER/validator_keys"
        # $1 is argument for CSM Validator Plugin
        loadKeys $ARGUMENT
        if [ $OFFLINE_MODE == true ]; then
            network_up
            ohai "Network is online"
        fi
    else
        ohai "Error with staking-deposit-cli. Try again."
        exit
    fi
}

function _setKeystorePassword(){
    while true; do
        # Get keystore password
        _KEYSTOREPASSWORD=$(whiptail --title "Keystore Password" --inputbox "Enter your validator's keystore password, must be at least 12 chars. " 12 78 --ok-button "Submit" 3>&1 1>&2 2>&3)
        if [[ ${#_KEYSTOREPASSWORD} -ge 12 ]]; then
            _VERIFY_PASS=$(whiptail --title "Verify Password" --inputbox "Confirm your keystore password" 12 78 --ok-button "Submit" 3>&1 1>&2 2>&3)
            if [[ "${_KEYSTOREPASSWORD}" = "${_VERIFY_PASS}" ]]; then
                ohai "Password is same."
                break
            else
                whiptail --title "Error" --msgbox "Passwords not the same. Try again." 8 78
            fi
        else
            whiptail --msgbox "The keystore password must be at least 8 characters long." 8 78
        fi
    done
}

function setConfig(){
    case $NETWORK in
          mainnet)
            LAUNCHPAD_URL="https://launchpad.ethereum.org"
            LAUNCHPAD_URL_LIDO="https://csm.lido.fi/?ref=ethpillar"
            CSM_FEE_RECIPIENT_ADDRESS=${CSM_FEE_RECIPIENT_ADDRESS_MAINNET}
            CSM_WITHDRAWAL_ADDRESS=${CSM_WITHDRAWAL_ADDRESS_MAINNET}
            CSM_SENTINEL_URL="https://t.me/CSMSentinel_bot"
            FAUCET=""
            HOMEPAGE="https://ethereum.org"
            EXPLORER="https://beaconcha.in"
          ;;
          holesky)
            LAUNCHPAD_URL="https://holesky.launchpad.ethstaker.cc"
            LAUNCHPAD_URL_LIDO="https://csm.testnet.fi/?ref=ethpillar"
            CSM_FEE_RECIPIENT_ADDRESS=${CSM_FEE_RECIPIENT_ADDRESS_HOLESKY}
            CSM_WITHDRAWAL_ADDRESS=${CSM_WITHDRAWAL_ADDRESS_HOLESKY}
            CSM_SENTINEL_URL="https://t.me/CSMSentinelHolesky_bot"
            FAUCET="https://holesky-faucet.pk910.de"
            HOMEPAGE="https://holesky.ethpandaops.io"
            EXPLORER="https://holesky.beaconcha.in"
          ;;
          ephemery)
            LAUNCHPAD_URL="https://launchpad.ephemery.dev"
            LAUNCHPAD_URL_LIDO="https://TBD.testnet.fi/?ref=ethpillar"
            CSM_FEE_RECIPIENT_ADDRESS=${CSM_FEE_RECIPIENT_ADDRESS_HOLESKY}
            CSM_WITHDRAWAL_ADDRESS=${CSM_WITHDRAWAL_ADDRESS_HOLESKY}
            CSM_SENTINEL_URL="https://t.me/CSMSentinelTBD"
            FAUCET="https://faucet.bordel.wtf"
            HOMEPAGE="https://ephemery.dev"
            EXPLORER="https://beaconlight.ephemery.dev"
          ;;
          endurance_devnet)
            LAUNCHPAD_URL="https://staking.fusionist.io/en/"
            LAUNCHPAD_URL_LIDO=""  # No Lido support for endurance devnet
            CSM_FEE_RECIPIENT_ADDRESS=""  # No CSM support for endurance devnet
            CSM_WITHDRAWAL_ADDRESS=""  # No CSM support for endurance devnet
            CSM_SENTINEL_URL=""  # No CSM sentinel for endurance devnet
            FAUCET=""
            HOMEPAGE="https://www.fusionist.io/"
            # TODO: config beaconcha.in for endurance devnet solv bigtabel issues
            EXPLORER="http://78.46.91.61:9777/"
          ;;
    esac

    # Check if Lido CSM Validator
    if [[ $isLido ]]; then
        # Update message for Lido
        MSG_ETHADDRESS="\nSet this to Lido's CSM Withdrawal Vault Address.
\n${NETWORK}: ${CSM_WITHDRAWAL_ADDRESS}
\nIn checksum format, ether the Withdrawal Address:"
    fi
}

function checkLido(){
    [[ $# -eq 1 ]] && local ARGUMENT=$1 || ARGUMENT="default"
    if [[ $(grep --ignore-case -oE "${CSM_FEE_RECIPIENT_ADDRESS_MAINNET}" /etc/systemd/system/validator.service) ||
          $(grep --ignore-case -oE "${CSM_FEE_RECIPIENT_ADDRESS_HOLESKY}" /etc/systemd/system/validator.service) ||
          "$ARGUMENT" == "plugin_csm_validator" ]]; then
      isLido="1"
    fi
}

# Load validator keys into validator client
function loadKeys(){
   case $1 in
      default)
        getClientVC && sudo systemctl stop validator
        ;;
      plugin_csm_validator)
        VC="Nimbus"
        local __DATA_DIR=${DATA_DIR}
        local __BINARY_PATH="${PLUGIN_INSTALL_PATH}"
        local __SERVICE_USER="${SERVICE_ACCOUNT}"
        local __SERVICE_NAME="${SERVICE_NAME}"
        sudo systemctl stop ${__SERVICE_NAME}
        ;;
   esac
   ohai "Loading PubKeys into $VC Validator"
   ohai "Stopping validator to import keys"
   case $VC in
      Lighthouse)
        sudo lighthouse account validator import \
          --datadir /var/lib/lighthouse \
          --directory=$KEYFOLDER \
          --reuse-password
        sudo chown -R validator:validator /var/lib/lighthouse/validators
        sudo chmod 700 /var/lib/lighthouse/validators
      ;;
     Lodestar)
        sudo mkdir -p /var/lib/lodestar/validators
        cd /usr/local/bin/lodestar
        sudo ./lodestar validator import \
          --dataDir="/var/lib/lodestar/validators" \
          --keystore=$KEYFOLDER
        sudo chown -R validator:validator /var/lib/lodestar/validators
        sudo chmod 700 /var/lib/lodestar/validators
      ;;
     Teku)
        if [[ -z $_KEYSTOREPASSWORD ]]; then
            while true; do
                # Get keystore password
                _KEYSTOREPASSWORD=$(whiptail --title "Teku Keystore Password" --inputbox "Enter your keystore password" 10 78 --ok-button "Submit" 3>&1 1>&2 2>&3)
                VERIFY_PASS=$(whiptail --title "Verify Password" --inputbox "Confirm your keystore password" 10 78 --ok-button "Submit" 3>&1 1>&2 2>&3)
                if [[ "${_KEYSTOREPASSWORD}" = "${VERIFY_PASS}" ]]; then
                    ohai "Password is same."
                    break
                else
                    whiptail --title "Error" --msgbox "Passwords not the same. Try again." 8 78
                fi
            done
        fi
        echo $_KEYSTOREPASSWORD > $HOME/validators-password.txt
        # Create password file for each keystore
        for f in $KEYFOLDER/keystore*.json; do sudo cp $HOME/validators-password.txt $KEYFOLDER/$(basename $f .json).txt; done
        sudo mkdir -p /var/lib/teku_validator/validator_keys
        sudo cp $KEYFOLDER/keystore* /var/lib/teku_validator/validator_keys
        sudo chown -R validator:validator /var/lib/teku_validator
        sudo chmod -R 700 /var/lib/teku_validator
        rm $HOME/validators-password.txt
      ;;
     Nimbus)
        if [[ "$1" = "plugin_csm_validator" ]]; then
            sudo "${__BINARY_PATH}"/nimbus_beacon_node deposits import \
            --data-dir="${__DATA_DIR}" $KEYFOLDER
            sudo chown -R ${__SERVICE_USER}:${__SERVICE_USER} "${__DATA_DIR}"
            sudo chmod -R 700 "${__DATA_DIR}"
        else
            sudo /usr/local/bin/nimbus_beacon_node deposits import \
                --data-dir=/var/lib/nimbus_validator $KEYFOLDER
            sudo chown -R validator:validator /var/lib/nimbus_validator
            sudo chmod -R 700 /var/lib/nimbus_validator
        fi
      ;;
     Prysm)
        sudo /usr/local/bin/validator accounts import \
          --accept-terms-of-use \
          --wallet-dir=/var/lib/prysm/validators \
          --keys-dir=$KEYFOLDER
        sudo chown -R validator:validator /var/lib/prysm/validators
        sudo chmod 700 /var/lib/prysm/validators
      ;;
     esac
     ohai "Starting validator"
     [[ $1 == "default" ]] && sudo systemctl start validator
     [[ $1 == "plugin_csm_validator" ]] && sudo systemctl start ${__SERVICE_NAME}
     queryValidatorQueue
     setLaunchPadMessage
     whiptail --title "Next Steps: Upload JSON Deposit Data File" --msgbox "$MSG_LAUNCHPAD" 24 95
     whiptail --title "Tips: Things to Know" --msgbox "$MSG_TIPS" 24 78
     ohai "Finished loading keys"
     promptViewLogs $1
}

function setLaunchPadMessage(){
    MSG_FAUCET="" && MSG_HOMEPAGE="" && MSG_EXPLORER=""
    [[ -n ${FAUCET} ]] && MSG_FAUCET=">> Faucet Available: $FAUCET"
    [[ -n ${HOMEPAGE} ]] && MSG_HOMEPAGE=">> Network Homepage: $HOMEPAGE"
    [[ -n ${EXPLORER} ]] && MSG_EXPLORER=">> Explorer:         $EXPLORER"
    MSG_LAUNCHPAD="1) Visit the Launchpad: $LAUNCHPAD_URL
\n2) Upload your deposit_data-#########.json found in the directory:
\n$KEYFOLDER
\n3) Connect the Launchpad with your wallet, review and accept terms.
\n4) Complete the 32 ETH deposit transaction(s).
\n5) Wait for validators to become active. $MSG_VALIDATOR_QUEUE
\nUseful links:
$MSG_HOMEPAGE
$MSG_EXPLORER
$MSG_FAUCET"

    MSG_TIPS=" - Wait for Node Sync: Before making a deposit, ensure your EL/CL client is synced to avoid missing rewards.
\n - Timing of Validator Activation: After depositing, it takes about 15 hours for a validator to be activated unless there's a long entry queue.
\n - Backup Keystore Files: Keep copies on offline USB storage.
   Location: $KEYFOLDER
\n - Generate Voluntary Exit Message: Once active and assigned an index #, generate your validator's VEM. To stop validator duties, broadcast VEM."

    MSG_LAUNCHPAD_LIDO="1) Visit Lido CSM: $LAUNCHPAD_URL_LIDO
\n2) Connect your wallet on the correct network, review and accept terms.
\n3) Copy JSON from your deposit_data-#########.json
\nTo view JSON, run command:
cat $KEYFOLDER/deposit*
\n4) Provide the ~2 ETH/stETH bond per validator.
\n5) Lido will deposit the 32ETH. Wait for your validators to become active. $MSG_VALIDATOR_QUEUE
\nUseful links:
$MSG_HOMEPAGE
$MSG_EXPLORER
$MSG_FAUCET"

    MSG_TIPS_LIDO=" - DO NOT DEPOSIT 32ETH YOURSELF: Lido will deposit for you.
\n - Wait for Node Sync: Before making the ~2ETH bond deposit, ensure your EL/CL client is synced to avoid missing rewards.
\n - Timing of Validator Activation: After depositing, it takes about 15 hours for a validator to be activated unless there's a long entry queue.
\n - Backup Keystore Files: Keep copies on offline USB storage.
   Location: $KEYFOLDER
\n - Subscribe to CSM Sentinel Bot: Provides your CSM Node Operator events via telegram $CSM_SENTINEL_URL
\n - Generate Voluntary Exit Message: Once active and assigned an index #, generate your validator's VEM. To stop validator duties, broadcast VEM."

    if [[ $isLido ]]; then
       # Update message for Lido
       MSG_LAUNCHPAD="${MSG_LAUNCHPAD_LIDO}"
       MSG_TIPS="$MSG_TIPS_LIDO"
    fi
}

function queryValidatorQueue(){
    #Variables
    BEACONCHAIN_VALIDATOR_QUEUE_API_URL="/api/v1/validators/queue"
    declare -A BEACONCHAIN_URLS=()
    BEACONCHAIN_URLS["mainnet"]="https://beaconcha.in"
    BEACONCHAIN_URLS["holesky"]="https://holesky.beaconcha.in"
    BEACONCHAIN_URLS["ephemery"]="https://beaconchain.ephemery.dev"
    # TODO: temp use maninet https://beacon.fusionist.io//api/v1/validators/queue
    BEACONCHAIN_URLS["endurance_devnet"]="https://beacon.fusionist.io"  

    # Dencun entry churn cap
    CHURN_ENTRY_PER_EPOCH=8
    EPOCHS_PER_DAY_CONSTANT=225

    # Query for data
    json=$(curl -s ${BEACONCHAIN_URLS["${NETWORK}"]}${BEACONCHAIN_VALIDATOR_QUEUE_API_URL})

    # Parse JSON using jq and print data
    if $(echo "$json" | jq -e '.data[]' > /dev/null 2>&1); then
        CHURN_ENTRY_PER_DAY=$(echo "scale=0; $CHURN_ENTRY_PER_EPOCH * $EPOCHS_PER_DAY_CONSTANT" | bc)
        _val_joining=$(echo $json | jq -r '.data.beaconchain_entering')
        _val_wait_days=$(echo "scale=1; $(echo "$json" | jq -r '.data.beaconchain_entering') / $CHURN_ENTRY_PER_DAY" | bc)
        MSG_VALIDATOR_QUEUE="For ${NETWORK}, currently ${_val_joining} validators waiting to join. ETA: ${_val_wait_days} days."
    else
      echo "DEBUG: Unable to query beaconcha.in for $NETWORK validator queue data."
    fi
}

function getClientVC(){
    VC=$(cat /etc/systemd/system/validator.service | grep Description= | awk -F'=' '{print $2}' | awk '{print $1}')
}

function promptViewLogs(){
    if whiptail --title "Validator Keys Imported - $VC" --yesno "Would you like to view logs and confirm everything is running properly?" 8 78; then
        case $1 in
            default)
               sudo bash -c 'journalctl -fu validator | ccze -A' ;;
            plugin_csm_validator)
               sudo bash -c "journalctl -fu ${SERVICE_NAME} | ccze -A" ;;
        esac
    fi
}

function setMessage(){
    MSG_INTRO="During this step, your Secret Recovery Phrase (also known as a "mnemonic") and an accompanying set of validator keys will be generated specifically for you. For comprehensive information regarding these keys, please refer to: https://kb.beaconcha.in/ethereum-staking/ethereum-2-keys
\nThe importance of safeguarding both the Secret Recovery Phrase and the validator keys cannot be overstated, as they are essential for accessing your funds. Exposure of these keys may lead to theft. To learn how to securely store them, visit: https://www.ledger.com/blog/how-to-protect-your-seed-phrase
\nFor enhanced security, it is strongly recommended that you create the Wagyu Key Gen (https://wagyu.gg) application on an entirely disconnected offline machine. A viable approach to this includes transferring the application onto a USB stick, connecting it to an isolated offline computer, and running it from there. Afterwards, copy your keys back to this machine and import. Continue?"
    MSG_OFFLINE="To ensure maximum security of your secret recovery phrase, it's important to operate this tool in an offline environment.
\nBe certain that your secret recovery phrase remains offline from the internet throughout the process.
\nDisconnecting from the internet might cut off computer access. Ensure you can recover access to this machine or VPS.
\nWould you like to disable the internet while generating keys for enhanced security?"
    MSG_INTERNET="Being connected to the internet while using this tool drastically increases the risk of exposing your Secret Recovery Phrase.
\nYou can avoid this risk by having a live OS such as Tails installed on a USB drive and run on a computer with network capabilities disabled.
\nYou can visit https://tails.net/install/ for instructions on how to download, install, and run Tails on a USB device.
\nIf you have any questions you can get help at https://dsc.gg/ethstaker"
    MSG_PATH="Enter the path to your keystore files.
\nDirectory contains keystore-m.json file(s).
\nExample: $DEPOSIT_CLI_PATH/YYYY-MM-DD-NNNNNN/validator_keys"
    MSG_ETHADDRESS="Ensure that you have control over this address.
\nETH address secured by a hardware wallet is recommended.
\nIn checksum format, enter your Withdrawal Address:"
    MSG_IMPORT="Importing validator keys:
\n1) I acknowledge that if migrating from another node, I must wait for at least two epochs (12 mins 48 sec) before continuing.
\n2) I acknowledge that if migrating from another node, I have deleted the keys from the previous machine. This ensures that the keys will NOT inadvertently restart and run in two places.
\n3) Lastly, these validator keys are NOT operational on any other machine (such as a cloud hosting service or DVT).
\nContinue?"
}

menuMain(){
# Define the options for the main menu
OPTIONS=(
  1 "Generate new validator keys"
  2 "Import validator keys from offline key generation or backup"
  3 "Add new or regenerate existing validator keys from Secret Recovery Phrase"
  - ""
  99 "Exit"
)

while true; do
    # Display the main menu and get the user's choice
    CHOICE=$(whiptail --clear --cancel-button "Back"\
      --backtitle "Public Goods by Coincashew.eth" \
      --title "EthPillar - Validator Key Management" \
      --menu "Choose a category:" \
      0 42 0 \
      "${OPTIONS[@]}" \
      3>&1 1>&2 2>&3)
    if [ $? -gt 0 ]; then # user pressed <Cancel> button
        break
    fi

    # Handle the user's choice
    case $CHOICE in
      1)
        generateNewValidatorKeys
        ;;
      2)
        importValidatorKeys
       ;;
      3)
        addRestoreValidatorKeys
        ;;
      99)
        break
        ;;
    esac
done
}

[[ $# -eq 1 ]] && skip="$1" || skip=""
setWhiptailColors
setMessage
downloadEthstakerDepositCli
checkLido
# Only run if no args
[[ -z $skip ]] && menuMain
