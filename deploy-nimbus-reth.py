# Author: coincashew.eth | coincashew.com
# License: GNU GPL
# Source: https://github.com/coincashew/ethpillar
#
# Validator-Install: Standalone Nimbus BN + Standalone Nimbus VC + Reth EL + MEVboost
# Quickstart :: Minority Client :: Docker-free
#
# Made for home and solo stakers 
#
# Acknowledgments
# Validator-Install is branched from validator-install written by Accidental-green: https://github.com/accidental-green/validator-install
# The groundwork for this project was established through their previous efforts.

import os
import requests
import re
import fnmatch
import random
import json
import tarfile
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
import random
import sys
import platform
from consolemenu import *
from consolemenu.items import *
import argparse
from dotenv import load_dotenv, dotenv_values
from config import *

import os

def clear_screen():
    if os.name == 'posix':  # Unix-based systems (e.g., Linux, macOS)
        os.system('clear')
    elif os.name == 'nt':   # Windows
        os.system('cls')

clear_screen()  # Call the function to clear the screen

# Valid configurations
valid_networks = ['MAINNET', 'HOLESKY', 'SEPOLIA', 'ENDURANCE', 'ENDURANCE_DEVNET']
valid_exec_clients = ['RETH']
valid_consensus_clients = ['NIMBUS']
valid_install_configs = ['Solo Staking Node', 'Full Node Only', 'Lido CSM Staking Node', 'Lido CSM Validator Client Only' ,'Validator Client Only', 'Failover Staking Node']

# Load environment variables from env file
load_dotenv("env")

# Set options to parsed arguments
EL_P2P_PORT=os.getenv('EL_P2P_PORT')
EL_RPC_PORT=os.getenv('EL_RPC_PORT')
EL_MAX_PEER_COUNT=os.getenv('EL_MAX_PEER_COUNT')
CL_P2P_PORT=os.getenv('CL_P2P_PORT')
CL_REST_PORT=os.getenv('CL_REST_PORT')
CL_MAX_PEER_COUNT=os.getenv('CL_MAX_PEER_COUNT')
CL_IP_ADDRESS=os.getenv('CL_IP_ADDRESS')

# Endurance Mainnet
CL_TRUSTPEERS=os.getenv('CL_TRUSTPEERS')
CL_STATICPEERS=os.getenv('CL_STATICPEERS')
CL_BOOTNODES=os.getenv('CL_BOOTNODES')
EL_BOOTNODES=os.getenv('EL_BOOTNODES')


# Endurance Devnet
ENDURANCE_DEVNET_CL_STATICPEERS=os.getenv('ENDURANCE_DEVNET_CL_STATICPEERS')
ENDURANCE_DEVNET_CL_TRUSTPEERS=os.getenv('ENDURANCE_DEVNET_CL_TRUSTPEERS')
ENDURANCE_DEVNET_CL_BOOTNODES=os.getenv('ENDURANCE_DEVNET_CL_BOOTNODES')
ENDURANCE_DEVNET_EL_BOOTNODES=os.getenv('ENDURANCE_DEVNET_EL_BOOTNODES')

JWTSECRET_PATH=os.getenv('JWTSECRET_PATH')
GRAFFITI=os.getenv('GRAFFITI')
FEE_RECIPIENT_ADDRESS=os.getenv('FEE_RECIPIENT_ADDRESS')
MEV_MIN_BID=os.getenv('MEV_MIN_BID')
CSM_FEE_RECIPIENT_ADDRESS_MAINNET=os.getenv('CSM_FEE_RECIPIENT_ADDRESS_MAINNET')
CSM_FEE_RECIPIENT_ADDRESS_HOLESKY=os.getenv('CSM_FEE_RECIPIENT_ADDRESS_HOLESKY')
CSM_GRAFFITI=os.getenv('CSM_GRAFFITI')
CSM_MEV_MIN_BID=os.getenv('CSM_MEV_MIN_BID')
CSM_WITHDRAWAL_ADDRESS_MAINNET=os.getenv('CSM_WITHDRAWAL_ADDRESS_MAINNET')
CSM_WITHDRAWAL_ADDRESS_HOLESKY=os.getenv('CSM_WITHDRAWAL_ADDRESS_HOLESKY')

# Create argparse options
parser = argparse.ArgumentParser(description='Validator Install Options :: CoinCashew.com',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--network", type=str, help="Sets the Ethereum network", choices=valid_networks, default="")
parser.add_argument("--jwtsecret", type=str,help="Sets the jwtsecret file", default=JWTSECRET_PATH)
parser.add_argument("--graffiti", type=str, help="Sets the validator graffiti message", default=GRAFFITI)
parser.add_argument("--fee_address", type=str, help="Sets the fee recipient address", default="")
parser.add_argument("--el_p2p_port", type=int, help="Sets the Execution Client's P2P Port", default=EL_P2P_PORT)
parser.add_argument("--el_rpc_port", type=int, help="Sets the Execution Client's RPC Port", default=EL_RPC_PORT)
parser.add_argument("--el_max_peers", type=int, help="Sets the Execution Client's max peer count", default=EL_MAX_PEER_COUNT)
parser.add_argument("--cl_p2p_port", type=int, help="Sets the Consensus Client's P2P Port", default=CL_P2P_PORT)
parser.add_argument("--cl_rest_port", type=int, help="Sets the Consensus Client's REST Port", default=CL_REST_PORT)
parser.add_argument("--cl_max_peers", type=int, help="Sets the Consensus Client's max peer count", default=CL_MAX_PEER_COUNT)
parser.add_argument("--vc_only_bn_address", type=str, help="Sets Validator Only configuration's (beacon node) IP address, e.g. http://192.168.1.123:5052")
parser.add_argument("--skip_prompts", type=str, help="Performs non-interactive installation. Skips any interactive prompts if set to true", default="")
parser.add_argument("--install_config", type=str, help="Sets the node installation configuration", choices=valid_install_configs, default="")
parser.add_argument("-v", "--version", action="version", version="%(prog)s 1.0.0")
args = parser.parse_args()
#print(args)

def get_machine_architecture():
  machine_arch=platform.machine()
  if machine_arch == "x86_64":
    return "amd64"
  elif machine_arch == "aarch64":
    return "arm64"
  else:
    print(f'Unsupported machine architecture: {machine_arch}')
    exit(1)

def get_computer_platform():
  platform_name=platform.system()
  if platform_name == "Linux":
    return platform_name
  else:
    print(f'Unsupported platform: {platform_name}')
    exit(1)

binary_arch=get_machine_architecture()
platform_arch=get_computer_platform()

# Change to the home folder
os.chdir(os.path.expanduser("~"))

if not args.network and not args.skip_prompts:
    # Ask the user for Ethereum network
    index = SelectionMenu.get_selection(valid_networks,title='Validator Install Quickstart :: CoinCashew.com',subtitle='Installs Reth EL / Nimbus BN / Nimbus VC / MEVboost\nSelect Ethereum network:')

    # Exit selected
    if index == 5:
        exit(0)

    # Set network
    eth_network=valid_networks[index]
    eth_network=eth_network.lower()
else:
    eth_network=args.network.lower()

if not args.install_config and not args.skip_prompts:
    # Sepolia can only be full node
    if eth_network == "sepolia":
        install_config=valid_install_configs[1]
    else:
        # Ask the user for installation config
        index = SelectionMenu.get_selection(valid_install_configs,title='Validator Install Quickstart :: CoinCashew.com',subtitle='What type of installation would you like?\nSelect your type:',show_exit_option=False)
        # Set install configuration
        install_config=valid_install_configs[index]
else:
    install_config=args.install_config

# Sepolia is a permissioned validator set, default to NODE_ONLY
if eth_network == "sepolia":
    NODE_ONLY=True
    MEVBOOST_ENABLED=False
    VALIDATOR_ENABLED=False
    VALIDATOR_ONLY=False
else:
    match install_config:
       case "Solo Staking Node":
          NODE_ONLY=False
          MEVBOOST_ENABLED=True
          VALIDATOR_ENABLED=True
          VALIDATOR_ONLY=False
       case "Full Node Only":
          NODE_ONLY=True
          MEVBOOST_ENABLED=False
          VALIDATOR_ENABLED=False
          VALIDATOR_ONLY=False
       case "Lido CSM Staking Node":
          NODE_ONLY=False
          MEVBOOST_ENABLED=True
          VALIDATOR_ENABLED=True
          VALIDATOR_ONLY=False
          if eth_network == "mainnet":
              FEE_RECIPIENT_ADDRESS=CSM_FEE_RECIPIENT_ADDRESS_MAINNET
              CSM_WITHDRAWAL_ADDRESS=CSM_WITHDRAWAL_ADDRESS_MAINNET
          elif eth_network == "holesky":
              FEE_RECIPIENT_ADDRESS=CSM_FEE_RECIPIENT_ADDRESS_HOLESKY
              CSM_WITHDRAWAL_ADDRESS=CSM_WITHDRAWAL_ADDRESS_HOLESKY
          else:
            print(f'Unsupported Lido CSM Staking Node network: {eth_network}')
            exit(1)
          GRAFFITI=CSM_GRAFFITI
          MEV_MIN_BID=CSM_MEV_MIN_BID
       case "Lido CSM Validator Client Only":
          NODE_ONLY=False
          MEVBOOST_ENABLED=True
          VALIDATOR_ENABLED=True
          VALIDATOR_ONLY=True
          if eth_network == "mainnet":
              FEE_RECIPIENT_ADDRESS=CSM_FEE_RECIPIENT_ADDRESS_MAINNET
              CSM_WITHDRAWAL_ADDRESS=CSM_WITHDRAWAL_ADDRESS_MAINNET
          elif eth_network == "holesky":
              FEE_RECIPIENT_ADDRESS=CSM_FEE_RECIPIENT_ADDRESS_HOLESKY
              CSM_WITHDRAWAL_ADDRESS=CSM_WITHDRAWAL_ADDRESS_HOLESKY
          else:
              print(f'Unsupported Lido CSM Staking Node network: {eth_network}')
              exit(1)
          GRAFFITI=CSM_GRAFFITI
          MEV_MIN_BID=CSM_MEV_MIN_BID
       case "Validator Client Only":
          NODE_ONLY=False
          MEVBOOST_ENABLED=True
          VALIDATOR_ENABLED=True
          VALIDATOR_ONLY=True
       case "Failover Staking Node":
          NODE_ONLY=False
          MEVBOOST_ENABLED=True
          VALIDATOR_ENABLED=False
          VALIDATOR_ONLY=False

execution_client=""
consensus_client=""

if not VALIDATOR_ONLY:
    # Set clients to reth
    execution_client = valid_exec_clients[0]
    execution_client = execution_client.lower()

# Set clients to nimbus
consensus_client = valid_consensus_clients[0]
# Set to lowercase
consensus_client = consensus_client.lower()


# Validates an eth address
def is_valid_eth_address(address):
    pattern = re.compile("^0x[a-fA-F0-9]{40}$")
    return bool(pattern.match(address))

# Set FEE_RECIPIENT_ADDRESS
if not NODE_ONLY and FEE_RECIPIENT_ADDRESS == "" and not args.skip_prompts:
    # Prompt User for validator tips address
    while True:
        FEE_RECIPIENT_ADDRESS = Screen().input(f'Enter your Ethereum address (aka Fee Recipient Address)\n Hints: \n - Use ETH adddress from a hardware wallet.\n - Do not use an exchange address.\n > ')
        if is_valid_eth_address(FEE_RECIPIENT_ADDRESS):
            print("Valid Ethereum address")
            break
        else:
            print("Invalid Ethereum address. Try again.")

# Validates an CL beacon node address with port
def validate_beacon_node_address(ip_port):
    pattern = r"^(http|https|ws):\/\/((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(:?\d{1,5})?$"
    if re.match(pattern, ip_port):
        return True
    else:
        return False

BN_ADDRESS=""
# Set BN_ADDRESS
if VALIDATOR_ONLY and args.vc_only_bn_address is None and not args.skip_prompts:
    # Prompt User for beacon node address
    while True:
        BN_ADDRESS = Screen().input(f'\nEnter your consensus client (beacon node) address.\nExample: http://192.168.1.123:5052\n > ')
        if validate_beacon_node_address(BN_ADDRESS):
            print("Valid beacon node address")
            break
        else:
            print("Invalid beacon node address. Try again.")
else:
    BN_ADDRESS=args.vc_only_bn_address



if not args.skip_prompts:
    # Format confirmation message
    if install_config == "Solo Staking Node" or install_config == "Lido CSM Staking Node" or install_config == "Failover Staking Node":
        message=f'\nConfirmation: Verify your settings\n\nNetwork: {eth_network.upper()}\nInstallation configuration: {install_config}\nFee Recipient Address: {FEE_RECIPIENT_ADDRESS}\n\nIs this correct?'
    elif install_config == "Full Node Only":
        message=f'\nConfirmation: Verify your settings\n\nNetwork: {eth_network.upper()}\nInstallation configuration: {install_config}\n\nIs this correct?'
    elif install_config == "Validator Client Only" or install_config == "Lido CSM Validator Client Only" :
        message=f'\nConfirmation: Verify your settings\n\nNetwork: {eth_network.upper()}\nInstallation configuration: {install_config}\nFee Recipient Address: {FEE_RECIPIENT_ADDRESS}\n\nConsensus client (beacon node) address: {BN_ADDRESS}\n\nIs this correct?'
    else:
        print(f"\nError: Unknown install_config")
        exit(1)

    answer=PromptUtils(Screen()).prompt_for_yes_or_no(f'{message}')

    if not answer:
        file_name = os.path.basename(sys.argv[0])
        print(f'\nInstall cancelled by user. \n\nWhen ready, re-run install command:\npython3 {file_name}')
        exit(0)
        
        
def download_endurance_config(url):
    # Save current working directory
    original_dir = os.getcwd()
    print(f"Before download_endurance_config:Original directory: {original_dir}")
    print(f"download_endurance_config:URL: {url}")
    print(f"Ready to download endurance network genesis configuration")
    subprocess.run(['sudo', 'mkdir', '-p', '/opt/ethpillar/el-cl-genesis-data'], check=True)
    # Clean up existing directory if it exists
    if os.path.exists('/tmp/network_config'):
        shutil.rmtree('/tmp/network_config')
    subprocess.run(['git', 'clone', url, '/tmp/network_config'])
    os.chdir('/tmp/network_config')
    # Add execute permissions to decompress.sh
    subprocess.run(['chmod', '+x', './decompress.sh'])
    # Use bash explicitly to run the script
    subprocess.run(['bash', './decompress.sh'])
    # Use sudo to copy files
    print(f'copy custom genesis file to /opt/ethpillar/el-cl-genesis-data')
    subprocess.run(['sudo', 'cp', 'genesis.json', '/opt/ethpillar/el-cl-genesis-data/'])
    subprocess.run(['sudo', 'cp', 'genesis.ssz', '/opt/ethpillar/el-cl-genesis-data/'])
    subprocess.run(['sudo', 'cp', 'config.yaml', '/opt/ethpillar/el-cl-genesis-data/'])
    subprocess.run(['sudo', 'cp', 'deploy_block.txt', '/opt/ethpillar/el-cl-genesis-data/'])
    subprocess.run(['sudo', 'cp', 'deposit_contract.txt', '/opt/ethpillar/el-cl-genesis-data/'])
    subprocess.run(['sudo', 'cp', 'deposit_contract_block.txt', '/opt/ethpillar/el-cl-genesis-data/'])
    subprocess.run(['sudo', 'cp', 'deposit_contract_block_hash.txt', '/opt/ethpillar/el-cl-genesis-data/'])
    
    shutil.rmtree('/tmp/network_config')
    # Restore original working directory
    os.chdir(original_dir)
    
    
# Initialize sync urls for selected network
if eth_network == "mainnet":
    sync_urls = mainnet_sync_urls
elif eth_network == "holesky":
    sync_urls = holesky_sync_urls
elif eth_network == "sepolia":
    sync_urls = sepolia_sync_urls
elif eth_network == "endurance":
    sync_urls = endurance_sync_urls
    download_endurance_config("https://github.com/OpenFusionist/network_config")
elif eth_network == "endurance_devnet":
    download_endurance_config("https://github.com/OpenFusionist/devnet_network_config")
    sync_urls = endurance_devnet_sync_urls

# Use a random sync url
sync_url = random.choice(sync_urls)[1]



def setup_node():
    if not VALIDATOR_ONLY:
        # Create JWT directory
        subprocess.run([f'sudo mkdir -p $(dirname {JWTSECRET_PATH})'], shell=True)

        # Generate random hex string and save to file
        rand_hex = subprocess.run(['openssl', 'rand', '-hex', '32'], stdout=subprocess.PIPE)
        subprocess.run([f'sudo tee {JWTSECRET_PATH}'], input=rand_hex.stdout, stdout=subprocess.DEVNULL, shell=True)

    # Update and upgrade packages
    subprocess.run(['sudo', 'apt', '-y', '-qq', 'update'])
    subprocess.run(['sudo', 'apt', '-y', '-qq', 'upgrade'])

    # Autoremove packages
    subprocess.run(['sudo', 'apt', '-y', '-qq' , 'autoremove'])

    # Chrony timesync package
    subprocess.run(['sudo', 'apt', '-y', '-qq', 'install', 'chrony'])

def install_mevboost():
    if MEVBOOST_ENABLED == True and not VALIDATOR_ONLY:
        # Step 1: Create mevboost service account
        os.system("sudo useradd --no-create-home --shell /bin/false mevboost")

        # Step 2: Install mevboost
        # Change to the home folder
        os.chdir(os.path.expanduser("~"))

        # Define the Github API endpoint to get the latest release
        url = 'https://api.github.com/repos/flashbots/mev-boost/releases/latest'

        # Send a GET request to the API endpoint
        response = requests.get(url)
        global mevboost_version
        mevboost_version = response.json()['tag_name']

        # Search for the asset with the name that ends in {platform_arch}_{binary_arch}.tar.gz
        assets = response.json()['assets']
        download_url = None
        for asset in assets:
            if asset['name'].endswith(f'{platform_arch.lower()}_{binary_arch}.tar.gz'):
                download_url = asset['browser_download_url']
                break

        if download_url is None:
            print("Error: Could not find the download URL for the latest release.")
            exit(1)

        # Download the latest release binary
        # TODO: 使用自定义版本支持自定义genesis-fork-version 读取, 等待rc版本发布后更新
        download_url = "https://github.com/flashbots/mev-boost/releases/download/v1.9-rc2/mev-boost_1.9-rc2_linux_amd64.tar.gz"
        print(f">> Downloading mevboost > URL: {download_url}")

        try:
            # Download the file
            response = requests.get(download_url, stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Save the binary to the home folder
            with open("mev-boost.tar.gz", "wb") as f:
                for chunk in response.iter_content(1024):
                    if chunk:
                        f.write(chunk)

            print(f">> Successfully downloaded: {asset['name']}")

        except requests.exceptions.RequestException as e:
            print(f"Error: Unable to download file. Try again later. {e}")
            exit(1)

        # Extract the binary to the home folder
        with tarfile.open('mev-boost.tar.gz', 'r:gz') as tar:
            tar.extractall()

        # Move the binary to /usr/local/bin using sudo
        os.system(f"sudo mv mev-boost /usr/local/bin")

        # Remove files
        os.system(f"rm mev-boost.tar.gz LICENSE README.md")

        ##### MEV Boost Service File
        mev_boost_service_file_lines = [
        '[Unit]',
        f'Description=MEV-Boost Service for {eth_network.upper()}',
        'Wants=network-online.target',
        'After=network-online.target',
        'Documentation=https://www.coincashew.com',
        '',
        '[Service]',
        'User=mevboost',
        'Group=mevboost',
        'Type=simple',
        'Restart=always',
        'RestartSec=5',
        'ExecStart=/usr/local/bin/mev-boost -relay-check\\'
        ]

        # Add custom endurance network parameters
        if eth_network == 'endurance_devnet':
            mev_boost_service_file_lines.extend([
                '    -genesis-fork-version 0x10000001 \\',
                '    -genesis-timestamp 1705568400 \\'
            ])
        elif eth_network == 'endurance':
            # Standard network configuration
            mev_boost_service_file_lines.extend([
                '    -genesis-fork-version 0x10000001 \\',
                '    -genesis-timestamp 1709532000 \\'
            ])
        else:
            # Standard network configuration
            mev_boost_service_file_lines.extend([
                f'    -{eth_network} \\'
            ])
            
        # Add network-specific relay options
        relay_options = {
            'mainnet': mainnet_relay_options,
            'holesky': holesky_relay_options,
            'sepolia': sepolia_relay_options,
            'endurance_devnet': endurance_devnet_relay_options,
            'endurance': endurance_relay_options
        }.get(eth_network, sepolia_relay_options)

        for relay in relay_options:
            relay_line = f'    -relay {relay["url"]} \\'
            mev_boost_service_file_lines.append(relay_line)

        # Remove the trailing '\\' from the last relay line
        mev_boost_service_file_lines[-1] = mev_boost_service_file_lines[-1].rstrip(' \\')

        mev_boost_service_file_lines.extend([
            '',
            '[Install]',
            'WantedBy=multi-user.target',
        ])
        mev_boost_service_file = '\n'.join(mev_boost_service_file_lines)

        mev_boost_temp_file = 'mev_boost_temp.service'
        global mev_boost_service_file_path
        mev_boost_service_file_path = '/etc/systemd/system/mevboost.service'

        with open(mev_boost_temp_file, 'w') as f:
            f.write(mev_boost_service_file)

        os.system(f'sudo cp {mev_boost_temp_file} {mev_boost_service_file_path}')
        os.remove(mev_boost_temp_file)

def download_and_install_reth():
    if execution_client == 'reth':
        # Create User and directories
        subprocess.run(["sudo", "useradd", "--no-create-home", "--shell", "/bin/false", "execution"])
        subprocess.run(["sudo", "mkdir", "-p", "/var/lib/reth"])
        subprocess.run(["sudo", "chown", "-R", "execution:execution", "/var/lib/reth"])
        
        # Install required dependencies
        subprocess.run(["sudo", "apt-get", '-qq', "install", "build-essential", "cmake", "pkg-config", "libssl-dev", "clang", "-y"], check=True)

        # Define the Github API endpoint to get the latest release
        url = 'https://api.github.com/repos/paradigmxyz/reth/releases/latest'

        # Send a GET request to the API endpoint
        response = requests.get(url)
        global reth_version
        reth_version = response.json()['tag_name']

        # Adjust binary name based on architecture
        if binary_arch == "amd64":
            _arch = "x86_64"
        elif binary_arch == "arm64":
            _arch = "aarch64"
        else:
            print("Error: Unknown binary architecture.")
            exit(1)

        # Search for the asset with the exact name pattern
        assets = response.json()['assets']
        download_url = None
        tar_filename = None
        expected_filename = f'reth-{reth_version}-{_arch}-unknown-linux-gnu.tar.gz'
        for asset in assets:
            if asset['name'] == expected_filename:
                download_url = asset['browser_download_url']
                tar_filename = asset['name']
                break

        if download_url is None or tar_filename is None:
            print(f"Error: Could not find the download URL for the latest release (version {reth_version}).")
            print("Available assets:")
            for asset in assets:
                print(f"- {asset['name']}")
            exit(1)

        # Download the latest release binary
        print(f">> Downloading Reth {reth_version} > URL: {download_url}")

        try:
            # Download the file
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            # Save the binary to a temporary file
            with tempfile.NamedTemporaryFile('wb', suffix='.tar.gz', delete=False) as temp_file:
                for chunk in response.iter_content(1024):
                    if chunk:
                        temp_file.write(chunk)
                temp_path = temp_file.name

            print(f">> Successfully downloaded: {tar_filename}")

        except requests.exceptions.RequestException as e:
            print(f"Error: Unable to download file. Try again later. {e}")
            exit(1)

        # Create a temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract the binary to the temporary directory
            result = subprocess.run(["tar", "xzf", temp_path, "-C", temp_dir], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error extracting: {result.stderr}")
                exit(1)

            # Copy the reth binary directly to /usr/local/bin
            result = subprocess.run(["sudo", "cp", "-a", f"{temp_dir}/reth", "/usr/local/bin/"], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error copying: {result.stderr}")
                exit(1)

        # Set permissions and ownership
        subprocess.run(["sudo", "chmod", "a+x", "/usr/local/bin/reth"])
        subprocess.run(["sudo", "chown", "execution:execution", "/usr/local/bin/reth"])

        # Remove the temporary tar file
        os.remove(temp_path)

        ##### RETH SERVICE FILE ###########
        reth_exec_flag = f'''node --full --log.file.directory=/var/lib/reth/log --datadir=/var/lib/reth --port={EL_P2P_PORT} --http --http.addr=0.0.0.0 --http.port={EL_RPC_PORT} --ws --ws.addr=0.0.0.0 --authrpc.jwtsecret={JWTSECRET_PATH} --metrics=0.0.0.0:6060 --authrpc.addr=0.0.0.0 --authrpc.port=8551'''
        
        if eth_network == 'endurance':
            reth_exec_flag = f'{reth_exec_flag} --chain=/opt/ethpillar/el-cl-genesis-data/genesis.json --bootnodes={EL_BOOTNODES} --trusted-peers={EL_BOOTNODES}'
        elif eth_network == 'endurance_devnet':
            reth_exec_flag = f'{reth_exec_flag} --chain=/opt/ethpillar/el-cl-genesis-data/genesis.json --bootnodes={ENDURANCE_DEVNET_EL_BOOTNODES} --trusted-peers={ENDURANCE_DEVNET_EL_BOOTNODES}'
        else:
            reth_exec_flag = f'{reth_exec_flag} --chain={eth_network}'

        reth_service_file = f'''[Unit]
Description=Reth Execution Layer Client service for {eth_network.upper()}
After=network-online.target
Wants=network-online.target
Documentation=https://paradigmxyz.github.io/reth/

[Service]
Type=simple
User=execution
Group=execution
Restart=on-failure
RestartSec=3
KillSignal=SIGINT
TimeoutStopSec=900
ExecStart=/usr/local/bin/reth {reth_exec_flag}

[Install]
WantedBy=multi-user.target
'''
        reth_temp_file = 'execution_temp.service'
        global reth_service_file_path
        reth_service_file_path = '/etc/systemd/system/execution.service'

        with open(reth_temp_file, 'w') as f:
            f.write(reth_service_file)

        os.system(f'sudo cp {reth_temp_file} {reth_service_file_path}')

        os.remove(reth_temp_file)

def download_nimbus():
    if consensus_client == 'nimbus':
        # Change to the home folder
        os.chdir(os.path.expanduser("~"))

        # Define the Github API endpoint to get the latest release
        url = 'https://api.github.com/repos/status-im/nimbus-eth2/releases/latest'

        # Send a GET request to the API endpoint
        response = requests.get(url)
        global nimbus_version
        nimbus_version = response.json()['tag_name']

        # Adjust binary name
        if binary_arch == "amd64":
          _arch="amd64"
        elif binary_arch == "arm64":
          _arch="arm64v8"
        else:
           print("Error: Unknown binary architecture.")
           exit(1)

        # Search for the asset appropriate for this system architecture and platform
        assets = response.json()['assets']
        download_url = None
        for asset in assets:
            if f'_{platform_arch}_{_arch}' in asset['name'] and asset['name'].endswith('.tar.gz'):
                download_url = asset['browser_download_url']
                break

        if download_url is None:
            print("Error: Could not find the download URL for the latest release.")
            exit(1)

        # Download the latest release binary
        print(f">> Downloading Nimbus > URL: {download_url}")

        try:
            # Download the file
            response = requests.get(download_url, stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Save the binary to the home folder
            with open("nimbus.tar.gz", "wb") as f:
                for chunk in response.iter_content(1024):
                    if chunk:
                        f.write(chunk)

            print(f">> Successfully downloaded: {asset['name']}")

        except requests.exceptions.RequestException as e:
            print(f"Error: Unable to download file. Try again later. {e}")
            exit(1)

        # Extract the binary to the home folder
        with tarfile.open('nimbus.tar.gz', 'r:gz') as tar:
            tar.extractall()

        # Find the extracted folder
        extracted_folder = None
        for item in os.listdir():
            if item.startswith(f'nimbus-eth2_{platform.system()}_{_arch}'):
                extracted_folder = item
                break

        if extracted_folder is None:
            print("Error: Could not find the extracted folder.")
            exit(1)

        # Copy the binary to /usr/local/bin using sudo
        os.system(f"sudo cp {extracted_folder}/build/nimbus_beacon_node /usr/local/bin")
        os.system(f"sudo cp {extracted_folder}/build/nimbus_validator_client /usr/local/bin")

        # Remove the nimbus.tar.gz file and extracted folder
        os.remove('nimbus.tar.gz')
        os.system(f"rm -r {extracted_folder}")

def install_nimbus():
    if consensus_client == 'nimbus' and not VALIDATOR_ONLY:
        # Create data paths, service user, assign ownership permissions
        subprocess.run(['sudo', 'mkdir', '-p', '/var/lib/nimbus'])
        subprocess.run(['sudo', 'chmod', '700', '/var/lib/nimbus'])
        subprocess.run(['sudo', 'useradd', '--no-create-home', '--shell', '/bin/false', 'consensus'])
        subprocess.run(['sudo', 'chown', '-R', 'consensus:consensus', '/var/lib/nimbus'])

        if MEVBOOST_ENABLED == True:
            _mevparameters='--payload-builder=true --payload-builder-url=http://127.0.0.1:18550'
        else:
            _mevparameters=''

        if VALIDATOR_ENABLED == True and FEE_RECIPIENT_ADDRESS:
            _feeparameters=f'--suggested-fee-recipient={FEE_RECIPIENT_ADDRESS}'
        else:
            _feeparameters=''

        # Network specific parameters
        if eth_network == 'endurance':
            el_bootnodes = CL_BOOTNODES.split(',')
            bootstrap_nodes = ' '.join([f'--bootstrap-node={enode}' for enode in el_bootnodes])
            
            direct_peers = CL_STATICPEERS.split(',')
            direct_peers_str = " ".join([f"--direct-peer={peer}" for peer in direct_peers])
            
            _network_params = f'--network=/opt/ethpillar/el-cl-genesis-data {bootstrap_nodes} {direct_peers_str}'
            
        elif eth_network == 'endurance_devnet':
            # Split ENDURANCE_DEVNET_CL_BOOTNODES into a list of enodes
            el_bootnodes = ENDURANCE_DEVNET_CL_BOOTNODES.split(',')
            bootstrap_nodes = ' '.join([f'--bootstrap-node={enode}' for enode in el_bootnodes])
            
            direct_peers = ENDURANCE_DEVNET_CL_STATICPEERS.split(',')
            direct_peers_str = " ".join([f"--direct-peer={peer}" for peer in direct_peers])
            
            # Update _network_params with the new bootstrap nodes
            _network_params = f'--network=/opt/ethpillar/el-cl-genesis-data {bootstrap_nodes} {direct_peers_str}'
        else:
            _network_params = f'--network={eth_network}'

        ########### NIMBUS SERVICE FILE #############
        nimbus_service_file = f'''[Unit]
Description=Nimbus Beacon Node Consensus Client service for {eth_network.upper()}
Wants=network-online.target
After=network-online.target
Documentation=https://www.coincashew.com

[Service]
Type=simple
User=consensus
Group=consensus
Restart=on-failure
RestartSec=3
KillSignal=SIGINT
TimeoutStopSec=900
ExecStart=/usr/local/bin/nimbus_beacon_node {_network_params} --data-dir=/var/lib/nimbus --tcp-port={CL_P2P_PORT} --udp-port={CL_P2P_PORT} --max-peers={CL_MAX_PEER_COUNT} --rest-port={CL_REST_PORT} --enr-auto-update=true --web3-url=http://127.0.0.1:8551 --rest --metrics --metrics-port=8008 --jwt-secret={JWTSECRET_PATH} --non-interactive --status-bar=false --in-process-validators=false {_feeparameters} {_mevparameters}

[Install]
WantedBy=multi-user.target
'''
        nimbus_temp_file = 'consensus_temp.service'
        global nimbus_service_file_path
        nimbus_service_file_path = '/etc/systemd/system/consensus.service'

        with open(nimbus_temp_file, 'w') as f:
            f.write(nimbus_service_file)

        os.system(f'sudo cp {nimbus_temp_file} {nimbus_service_file_path}')
        os.remove(nimbus_temp_file)

def run_nimbus_checkpoint_sync():
    network_config = eth_network
    if eth_network == 'endurance' or eth_network == 'endurance_devnet':
        print(f'for endurance network, use custom network config: /opt/ethpillar/el-cl-genesis-data ')
        network_config = '/opt/ethpillar/el-cl-genesis-data'
    if sync_url is not None and not VALIDATOR_ONLY:
        print(f'>> Running Checkpoint Sync. Using Sync URL: {sync_url}')
        db_path = "/var/lib/nimbus/db"
        os.system(f'sudo rm -rf {db_path}')
        subprocess.run([
            'sudo', '/usr/local/bin/nimbus_beacon_node', 'trustedNodeSync',
            f'--network={network_config}', '--data-dir=/var/lib/nimbus',
            f'--trusted-node-url={sync_url}', '--backfill=false'
        ])
        os.system(f'sudo chown -R consensus:consensus {db_path}')

def install_nimbus_validator():
    if MEVBOOST_ENABLED == True:
        _mevparameters='--payload-builder=true'
    else:
        _mevparameters=''

    if VALIDATOR_ENABLED == True and FEE_RECIPIENT_ADDRESS:
        _feeparameters=f'--suggested-fee-recipient={FEE_RECIPIENT_ADDRESS}'
    else:
        _feeparameters=''

    if BN_ADDRESS:
        _beaconnodeparameters=f'--beacon-node={BN_ADDRESS}'
    else:
        _beaconnodeparameters=f'--beacon-node=http://{CL_IP_ADDRESS}:{CL_REST_PORT}'

    if consensus_client == 'nimbus' and VALIDATOR_ENABLED == True:
        # Create data paths, service user, assign ownership permissions
        subprocess.run(['sudo', 'mkdir', '-p', '/var/lib/nimbus_validator'])
        subprocess.run(['sudo', 'chmod', '700', '/var/lib/nimbus_validator'])
        subprocess.run(['sudo', 'useradd', '--no-create-home', '--shell', '/bin/false', 'validator'])
        subprocess.run(['sudo', 'chown', '-R', 'validator:validator', '/var/lib/nimbus_validator'])

        nimbus_validator_file = f'''[Unit]
Description=Nimbus Validator Client service for {eth_network.upper()}
Wants=network-online.target
After=network-online.target
Documentation=https://www.coincashew.com

[Service]
Type=simple
User=validator
Group=validator
Restart=on-failure
RestartSec=3
KillSignal=SIGINT
TimeoutStopSec=900
ExecStart=/usr/local/bin/nimbus_validator_client --data-dir=/var/lib/nimbus_validator --metrics --metrics-port=8009 --non-interactive --doppelganger-detection=off --graffiti={GRAFFITI} {_beaconnodeparameters} {_feeparameters} {_mevparameters}

[Install]
WantedBy=multi-user.target
'''
        nimbus_temp_file = 'validator_temp.service'
        global nimbus_validator_file_path
        nimbus_validator_file_path = '/etc/systemd/system/validator.service'

        with open(nimbus_temp_file, 'w') as f:
            f.write(nimbus_validator_file)

        os.system(f'sudo cp {nimbus_temp_file} {nimbus_validator_file_path}')
        os.remove(nimbus_temp_file)

def finish_install():
    # Reload the systemd daemon
    subprocess.run(['sudo', 'systemctl', 'daemon-reload'])

    print(f'##########################\n')
    print(f'## Installation Summary ##\n')
    print(f'##########################\n')

    print(f'Installation Configuration: \n{install_config}\n')

    if execution_client == 'reth':
        print(f'Reth Version: \n{reth_version}\n')

    if consensus_client == 'nimbus':
        print(f'Nimbus Version: \n{nimbus_version}\n')

    if MEVBOOST_ENABLED and not VALIDATOR_ONLY:
        print(f'Mevboost Version: \n{mevboost_version}\n')

    print(f'Network: {eth_network.upper()}\n')

    if not VALIDATOR_ONLY:
        print(f'CheckPointSyncURL: {sync_url}\n')

    if VALIDATOR_ONLY and BN_ADDRESS:
        print(f'Beacon Node Address: {BN_ADDRESS}\n')
        os.chdir(os.path.expanduser("~/git/ethpillar"))
        os.system(f'cp .env.overrides.example .env.overrides')

    if NODE_ONLY == False:
        print(f'Validator Fee Recipient Address: {FEE_RECIPIENT_ADDRESS}\n')

    print(f'Systemd service files created:')
    if not VALIDATOR_ONLY:
        print(f'\n{nimbus_service_file_path}\n{reth_service_file_path}')
    if VALIDATOR_ENABLED == True:
        print(f'{nimbus_validator_file_path}')
    if MEVBOOST_ENABLED == True and not VALIDATOR_ONLY:
        print(f'{mev_boost_service_file_path}')

    if args.skip_prompts:
        print(f'\nNon-interactive install successful! Skipped prompts.')
        exit(0)

    # Prompt to start services
    if not VALIDATOR_ONLY:
        answer=PromptUtils(Screen()).prompt_for_yes_or_no(f"\nInstallation successful!\nSyncing a Nimbus/Reth node for validator duties can be as quick as a few hours.\nWould you like to start syncing now?")
        if answer:
            os.system(f'sudo systemctl start execution consensus')
            if MEVBOOST_ENABLED == True:
                os.system(f'sudo systemctl start mevboost')

    answer=PromptUtils(Screen()).prompt_for_yes_or_no(f"\nConfigure node to autostart:\nWould you like this node to autostart when system boots up?")

    # Prompt to enable autostart services
    if answer:
        if not VALIDATOR_ONLY:
            os.system(f'sudo systemctl enable execution consensus')
        if VALIDATOR_ENABLED == True:
            os.system(f'sudo systemctl enable validator')
        if MEVBOOST_ENABLED == True and not VALIDATOR_ONLY:
            os.system(f'sudo systemctl enable mevboost')

    # Ask CSM staker if they to manage validator keystores
    if install_config == 'Lido CSM Staking Node' or install_config == 'Lido CSM Validator Client Only':
        answer=PromptUtils(Screen()).prompt_for_yes_or_no(f"\nWould you like to generate or import new Lido CSM validator keys now?\nReminder: Set the Lido withdrawal address to: {CSM_WITHDRAWAL_ADDRESS}")
        if answer:
            os.chdir(os.path.expanduser("~/git/ethpillar"))
            command = './manage_validator_keys.sh'
            subprocess.run(command)

    # Ask solo staker if they to manage validator keystores
    if install_config == 'Solo Staking Node' or install_config == 'Validator Client Only':
        answer=PromptUtils(Screen()).prompt_for_yes_or_no(f"\nWould you like to generate or import validator keys now?\nIf not, resume at: ethpillar > Validator Client ")
        if answer:
            os.chdir(os.path.expanduser("~/git/ethpillar"))
            command = './manage_validator_keys.sh'
            subprocess.run(command)

    # Failover staking node reminders
    if install_config == 'Failover Staking Node':
        print(f'\nReminder for Failover Staking Node configurations:\n1. Consensus Client: Expose consensus client RPC port\n2. UFW Firewall: Update to allow incoming traffic on port {CL_REST_PORT}\n3. UFW firewall: Whitelist the validator(s) IP address.')

    # Validator Client Only overrides
    if install_config == 'Validator Client Only' or install_config == 'Lido CSM Validator Client Only':
        answer=PromptUtils(Screen()).prompt_for_yes_or_no(f"\nValidator Client Only:\n1) Be sure to expose your consensus client RPC port {CL_REST_PORT} and open firewall for this port.\n2) Would you like update your EL/CL override settings now?\nYour validator client needs to know EL/CL settings.\nIf not, update later at\nEthPillar > System Administration > Override environment variables.")
        if answer:
            command = ['nano', '~/git/ethpillar/.env.overrides']
            subprocess.run(command)

setup_node()
install_mevboost()
download_and_install_reth()
download_nimbus()
install_nimbus()
run_nimbus_checkpoint_sync()
install_nimbus_validator()
finish_install()
